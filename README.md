# Instabot.py 🤖 🌟

**Instabot.py** is an extremely light instagram bot that uses the undocumented Web API. Unlike other bots, Instabot.py does _not_ require Selenium or a WebDriver. Instead, it interacts with the API over simple HTTP Requests. It runs on most systems, including Raspberry Pi.

[![Donate](https://img.shields.io/badge/PayPal-Donate%20to%20Author-blue.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=7BMM6JGE73322&lc=US)
[![Chat on Telegram](https://img.shields.io/badge/Chat%20on-Telegram-brightgreen.svg)](https://t.me/joinchat/DYKH-0G_8hsDDoN_iE8ZlA)
[![Latest version on](https://badge.fury.io/py/instabot-py.svg)](https://badge.fury.io/py/instabot-py)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/instabot-py.svg)](https://pypi.org/project/instabot-py/)
<!-- [![Travis Pipelines build status](https://img.shields.io/travis/com/yurilaaziz/instabot-py.svg)](https://travis-ci.com/yurilaaziz/instabot-py/) -->

## Requirements

- Python v3.6 or greater
- Pip v18 or greater


## Quick Start 🚀

- **Make sure you have Python 3.6 or above installed**

  - `python3 --version`

On Windows you might have to use `python` without the version (`3`) suffix. Experienced users should use virtualenv.

- **If your version is below 3.6, we recommend you install the latest Python 3.7**

  - [Python on Windows](https://github.com/instabot-py/instabot.py/wiki/Installing-Python-on-Windows)
  - [Python on Mac](https://github.com/instabot-py/instabot.py/wiki/Installing-Python-3.7-on-macOS)
  - [Python on Raspberry Raspbian / Debian / Ubuntu](https://github.com/instabot-py/instabot.py/wiki/Installing-Python-3.7-on-Raspberry-Pi)

- **Install instabot.py from PyPi repository**

  - `python3 -m pip install instabot-py`

- **Start the bot** 🏁

  - `instabot-py`
  - or `python3 -m instabot_py`
  - For more advanced parameters and configurations download and edit [example.py](https://raw.githubusercontent.com/instabot-py/instabot.py/master/example.py) and run `python3 example.py`

- **Config** ⚙️

When you first run `instabot-py` a file called `config.ini` will be created in your current directory, along with an SQLite DB, and an error.log.

After the initial configuration, you can manually edit `config.ini` with a text editor. Restart the bot for changes to take effect.

The `%username%.db` file contains a record of the posts the bot has liked, and the users it has followed/unfollowed.

The `%username%.session` file stores your session with Instagram to avoid re-logins each time you start the bot.


## Upgrade ⬆️

- `python3 -m pip install instabot-py --no-cache-dir --upgrade`

## Install methods

**Recommended: From PyPi:** (Stable)

- `python3 -m pip install instabot-py`

**From sources:**  (Bleeding edge)

- `python3 -m pip install git+https://github.com/instabot-py/instabot.py`

## Parameters
| Parameter            | Type|                Description                           |        Default value             |
|:--------------------:|:---:|:----------------------------------------------------:|:--------------------------------:|
| login                | str | Your instagram username                              |      |
| password             | str | Your instagram password                              |      |
| start\_at\_h         | int | Start program at the hour                            | 0    |
| start\_at\_m         | int | Start program at the min                             | 0    |
| end\_at\_h           | int | End program at the hour                              | 23   |
| end\_at\_m           | int | End program at the min                               | 59   |
| database\_name       | str | change the name of database file to use multiple account | "follows\_db.db"   |
| session\_file        | str | change the name of session file so to avoid having to login every time. Set False to disable. | "username.session"   |
| like_per_day         | int | Number of photos to like per day (over 1000 may cause throttling) | 1000 |
| media_max_like       | int | Maximum number of likes on photos to like (set to 0 to disable) | 0    |
| media_min_like       | int | Minimum number of likes on photos to like (set to 0 to disable) | 0    |
| follow_per_day       | int | Users to follow per day                              | 0    |
| follow_time          | int | Seconds to wait before unfollowing                   | 5 * 60 * 60 |
| user_min_follow      | int | Check user before following them if they have X minimum of followers. Set 0 to disable                   | 0 |
| user_max_follow      | int | Check user before following them if they have X maximum of followers. Set 0 to disable                   | 0 |
| follow_time_enabled  | bool| Whether to wait seconds set in follow_time before unfollowing | True |
| unfollow_per_day     | int | Users to unfollow per day                            | 0    |
| unfollow_recent_feed | bool| If enabled, will populate database with users from recent feed and unfollow if they meet the conditions. Disable if you only want the bot to unfollow people it has previously followed. | True |
| unlike_per_day     | int | Number of media to unlike that the bot has previously liked. Set to 0 to disable.                           | 0    |
| time_till_unlike     | int | How long to wait after liking media before unliking them. | 3 * 24 * 60 * 60 (3 days) |
| comments_per_day     | int | Comments to post per day                             | 0    |
| comment_list         | [[str]] | List of word lists for comment generation. @username@ will be replaced by the media owner's username     | [['this', 'your'], ['photo', 'picture', 'pic', 'shot'], ['is', 'looks', 'is really'], ['great', 'super', 'good'], ['.', '...', '!', '!!']] |
| tag_list             | [str] | Tags to use for finding posts by hasthag or location(l:locationid from e.g. https://www.instagram.com/explore/locations/212999109/los-angeles-california/)                     | ['cat', 'car', 'dog', 'l:212999109'] |
| tag_blacklist        | [str] | Tags to ignore when liking posts                   | [] |
| user_blacklist       | {str: str} | Users whose posts to ignore. Example: `{"username": "", "username2": ""}` type only the key and leave value empty -- it will be populated with userids on startup.                | {} |
| max_like_for_one_tag | int | How many media of a given tag to like at once (out of 21) | 5 |
| unfollow_break_min   | int | Minimum seconds to break between unfollows           | 15 |
| unfollow_break_max   | int | Maximum seconds to break between unfollows           | 30 |
| log_mod              | int | Logging target (0 log to console, 1 log to file, 2 no log.) | 0 |
| proxy                | str | Access instagram through a proxy. (host:port or user:password@host:port) | |
| unfollow_not_following   | bool | Unfollow Condition: Unfollow those who do not follow you back | True |
| unfollow_inactive   | bool | Unfollow Condition: Unfollow those who have not posted in a while (inactive) | True |
| unfollow_probably_fake  | bool | Unfollow Condition: Unfollow accounts which skewed follow/follower ratio (probably fake) | True |
| unfollow_selebgram  | bool | Unfollow Condition: Unfollow (celebrity) accounts with too many followers and not enough following | False |
| unfollow_everyone  | bool | Unfollow Condition: Will unfollow everyone in unfollow queue (wildcard condition) | False |

## Contributing
Please feel free to contribute and submit PR requests. All help is appreciated. Look for issues with the label [needs help](https://github.com/instabot-py/instabot.py/labels/needs%20help).

<!-- 
## Video Tutorials
The following video tutorials demo setting up and running the bot:
* [Windows](https://www.youtube.com/watch?v=V8P0UCrACA0)
* [Mac/Linux](https://www.youtube.com/watch?v=ASO-cZO6uqo)
-->


## Instabot with yaml config
By default, instabot looks for configuration file (instabot.config.yml)
it could be changed by exporting environement varibale with the full path
````bash
export INSTABOT_CONFIG_FILE=instabot2.config.yml
````


````yaml

---
login : "username"
password : "password"
debug: 1
#Send INFO notification to Telegram channel 
logging.handlers.telegram:
  level: INFO
  class: telegram_handler.TelegramHandler
  token: __YOUR__CHANNEL__TOKEN__
  chat_id: __CHAT_ID__
logging.loggers.InstaBot.handlers:
  - telegram
  - console

follow_time: 1200
unfollow_per_day: 1000
follow_per_day: 1000

````

[Create Telegram bot for instabot](https://core.telegram.org/bots#3-how-do-i-create-a-bot)


## Community

- [Telegram Group](https://t.me/joinchat/DYKH-0G_8hsDDoN_iE8ZlA)
- [Facebook Group](https://www.facebook.com/groups/instabot/)
- [IRC Channel on Freenode.net #instabot](http://webchat.freenode.net?channels=%23instabot)
