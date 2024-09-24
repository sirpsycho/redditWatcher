# redditWatcher

## Description

Monitor subreddits and alert on new posts containing keywords

This script works via simple web scraping and generates a Discord message when there are new posts on a given subreddit matching a given set of strings. Follow the set up steps below to get started.

### A note on where to run this
This is intended to be run on some type of always-up server/host. It would be great if this could be run on a cloud service like AWS/Azure/etc but Reddit has apparently blocked unauthenticated requests coming from these network ranges (at least AWS; feel free to try other providers, your results may vary). You can run this on your personal computer, especially if you don't particularly care about perfect uptime. Alternatively, this would be perfect to run on a Raspberry Pi or similar low-power SBC.

## Set up

### 1) Create a discord webhook

This is how you will receive notifications. Discord is nice because it's totally free and very easy to set up and customize your notification preferences.

1. If you don't already have a discord account, head over to https://discord.com/ and sign up
2. You'll need a discord server where you have admin privileges. When setting up your discord account, you'll generally create a personal server, which is perfectly suitable
3. Right-click on your server and select `Server settings > Integrations`
4. Click `Webhooks` > `New Webhook`
5. Click on your new webhook and give it a name; ex `RedditWatcher`, and choose which channel it should post to
6. Click `Copy Webhook URL`

### 2) Edit config.json

The `config.json` file is where you configure which subreddit(s) you want to monitor, which keywords you want to search for, and other various settings. **At the minimum** you will need to configure these settings:

1. `discord_webhook_url`: Paste in the full webhook URL you copied in step 1
2. `subreddit_name`: This is the name of the subreddit you want to monitor (without the `r/`)
3. `search_strings`: This is a list/array of keywords you want to search for in new posts. Enclose each keyword in double-quotes and separate them by commas

You can adjust the other settings to your preference.

You can also choose to monitor multiple subreddits; just make a copy of everything between the curly brackets under `subreddit_monitoring_configs`, and edit the settings as desired

Here's an example config:
```
{
    "discord_webhook_url": "https://discord.com/api/webhooks/ ...TRUNCATED...",
    "log_to_file_enabled": true,
    "subreddit_monitoring_configs": [
        {
            "subreddit_name": "sneakers",
            "search_strings": ["nike", "jordan", "air force"],
            "search_post_titles": true,
            "search_post_descriptions": true,
            "case_sensitive": false
        }
    ]
}
```

### 3) Set this script to run on a schedule

This step will be different depending on the OS you're running.

#### Linux

Create a [cron job](https://devhints.io/cron) to execute the script

#### Windows

Prerequisites:
* Python is installed
* the `requests` module is installed (ex `pip install requests`)

1. Open `Task Scheduler` and click `Create Task...`
2. Give it a name; ex. `redditWatcher`
3. Select `Run whether user is logged in or not` and `Do not store password ...` (you dont need any special user permissions)
4. Under `Triggers` select `New Trigger`
5. Choose the option to repeat the task every `5 minutes` for a duration of `Indefinitely`
6. Under `Actions` select `New...`
7. Under `Program/script`, paste in the full path to your `python.exe` file
8. Under `Add arguments`, type `redditWatcher.py`
9. Under `Start in`, paste in the full path to the directory where you downloaded `redditWatcher.py`
   * ex. if the file is at `C:\SomePath\redditWatcher.py`, use `C:\SomePath\`

