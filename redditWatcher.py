import sys
import json
import requests
from bs4 import BeautifulSoup
import logging


BASE_DOMAIN = "www.reddit.com"
POST_ELEMENT_ID_STRING = "data-ks-id"
FILE_CHECKED_IDS = "checked.txt"  # a text file containing a list of IDs that we've already checked (reduce extra requests & duplicate notifications)
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", 
    "Accept-Encoding": "gzip, deflate, br, zstd", 
    "Accept-Language": "en-US,en;q=0.9", 
    "Host": BASE_DOMAIN, 
    "Priority": "u=0, i", 
    "Referer": BASE_DOMAIN, 
    "Sec-Ch-Ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Google Chrome\";v=\"128\"", 
    "Sec-Ch-Ua-Mobile": "?0", 
    "Sec-Ch-Ua-Platform": "\"Windows\"", 
    "Sec-Fetch-Dest": "document", 
    "Sec-Fetch-Mode": "navigate", 
    "Sec-Fetch-Site": "cross-site", 
    "Sec-Fetch-User": "?1", 
    "Upgrade-Insecure-Requests": "1", 
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36", 
}

# read the config file
with open("config.json", "r") as f:
    config = json.load(f)

# configure logging
logging_handlers = [logging.StreamHandler(sys.stdout)]
if config.get("log_to_file_enabled", False):
    logging_handlers.append(logging.FileHandler("info.log"))
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    handlers=logging_handlers,
)
logger = logging.getLogger()
logger.info("Start")
raise RuntimeError('test')

# read a local file of reddit post IDs that we've already processed
with open(FILE_CHECKED_IDS, 'r') as f:
    lines = f.readlines()
    checked_ids = [line.strip() for line in lines if line.strip()]
logger.info(f'Loaded {len(checked_ids)} already-checked IDs from local file "{FILE_CHECKED_IDS}"')


def main():
    # iterate over each subreddit and append to a list of matches
    all_matches = []
    for monitoring_config in config["subreddit_monitoring_configs"]:
        all_matches.extend(
            get_latest_subreddit_matches(monitoring_config=monitoring_config)
        )

    logger.info(f'Found {len(all_matches)} new posts matching configured search strings')
    for match in all_matches:
        logger.info(json.dumps(match, indent=4))
    send_notifications_discord(matches=all_matches)
    logger.info("Done")


def get_latest_subreddit_matches(monitoring_config: dict) -> list:
    # grab the latest posts from the subreddit page
    subreddit_name = monitoring_config["subreddit_name"]
    search_strings = monitoring_config["search_strings"]
    logger.info(f'Searching latest posts on "r/{subreddit_name}" for strings: {str(search_strings)}')
    subreddit_url = f'https://{BASE_DOMAIN}/r/{subreddit_name}/new/'
    response = requests.get(subreddit_url, headers=DEFAULT_HEADERS)
    if response.status_code != 200:
        logger.error(f'got non-200 response "{response.status_code}"')
        logger.error(response.text)
        return []
    
    # parse the links to the newest posts (generally returns the 3 newest)
    soup = BeautifulSoup(response.text, 'html.parser')
    latest_posts = soup.find_all('a', slot="full-post-link")
    logger.info(f'Grabbed {len(latest_posts)} latest posts')
    
    # of the latest posts, filter out any that we've already processed
    new_posts = [post for post in latest_posts if post.get(POST_ELEMENT_ID_STRING, "") not in checked_ids]
    logger.info(f'{len(new_posts)} posts are new')
    
    matches = []
    for post in new_posts:
        id = post.get(POST_ELEMENT_ID_STRING, "")
        href = post.get("href", "")
        url = "https://" + BASE_DOMAIN + href
        title = post.text.strip()
        
        logger.info(f'ID: "{id}", URL: "{url}", Title: "{title}"')
        
        # load the individual post to get the post description
        response = requests.get(url, headers=DEFAULT_HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        description = str(soup.select(f'#{id}-post-rtjson-content'))
        
        # if we dont care about case sensitivity, make everything lowercase
        if not monitoring_config["case_sensitive"]:
            title = title.lower()
            description = description.lower()
            search_strings = [string.lower() for string in search_strings]
        
        # check if we match on any search strings in the title or the description
        matched_strings = []
        if monitoring_config["search_post_titles"]:
            matched_strings.extend([string for string in search_strings if string in title])
        if monitoring_config["search_post_descriptions"]:
            matched_strings.extend([string for string in search_strings if string in description])
            
        # remove duplicates
        matched_strings = list(set(matched_strings))
        
        # append to the list of matches if we match on anything
        if matched_strings:
            matches.append({
                "id": id,
                "subreddit_name": subreddit_name,
                "url": url,
                "title": title,
                "matched_strings": str(matched_strings),
            })

    # add the new post IDs to our local list so we don't process them again
    with open(FILE_CHECKED_IDS, 'a') as f:
        for post in new_posts:
            f.write(post.get(POST_ELEMENT_ID_STRING, "") + "\n")

    return matches


def send_notifications_discord(matches: list):
    for match in matches:
        logger.info(f'Sending notification for {match["id"]}...')
        payload = {
            "content": f'New r/{match["subreddit_name"]} post matched on {match["matched_strings"]}: {match["url"]}'
        }
        response = requests.post(
            url=config["discord_webhook_url"],
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        if response.status_code in [200, 204]:
            logger.info("Message sent succcessfully")
        else:
            logger.warning(f"Message failed with status code: {response.status_code}")
            logger.warning(response.text)


main()
