#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging.config
from collections import OrderedDict

import requests
import yaml
from config42 import ConfigManager
from config42.handlers import ArgParse

import instabot_py
from instabot_py import InstaBot
from instabot_py.default_config import DEFAULT_CONFIG
from instabot_py.instabot import CredsMissing

schema = [
    dict(
        name="login",
        key="login",
        source=dict(argv=["--login"]),
        description="Your instagram username",
        required=False
    ), dict(
        name="password",
        key="password",
        source=dict(argv=["--password"]),
        description="Your instagram password",
        required=False
    ), dict(
        name="SQLite3 database path",
        key="database.path",
        source=dict(argv=["--sqlite-path"]),
        description="Contains the SQLite database path",
        required=False
    ), dict(
        name="session_file",
        key="session_file",
        source=dict(argv=["--session-file"]),
        description="change the name of session file so to avoid having to login every time. Set False to disable.",
        required=False
    ), dict(
        name="like_per_run",
        key="like_per_run",
        source=dict(argv=["--like-per-run"]),
        description="Number of photos to like per day (over 1000 may cause throttling)",
        type="integer",
        required=False

    ), dict(
        name="media_max_like",
        key="media_max_like",
        source=dict(argv=["--media-max-like"]),
        description="Maximum number of likes on photos to like (set to 0 to disable)",
        type="integer",
        required=False,

    ), dict(
        name="media_min_like",
        key="media_min_like",
        source=dict(argv=["--media-min-like"]),
        description="Minimum number of likes on photos to like (set to 0 to disable)",
        type="integer",
        required=False

    ), dict(
        name="follow_per_run",
        key="follow_per_run",
        source=dict(argv=["--follow-per-run"]),
        description="Users to follow per day",
        type="integer",
        required=False

    ), dict(
        name="follow_time",
        key="follow_time",
        source=dict(argv=["--follow-time"]),
        description="Seconds to wait before unfollowing",
        type="integer",
        required=False

    ), dict(
        name="user_min_follow",
        key="user_min_follow",
        source=dict(argv=["--user-min-follow"]),
        description="Check user before following them if they have X minimum of followers. Set 0 to disable",
        type="integer",
        required=False

    ), dict(
        name="user_max_follow",
        key="user_max_follow",
        source=dict(argv=["--user-max-follow"]),
        description="Check user before following them if they have X maximum of followers. Set 0 to disable",
        type="integer",
        required=False

    ), dict(
        name="unfollow_per_run",
        key="unfollow_per_run",
        source=dict(argv=["--unfollow-per-run"]),
        description="Users to unfollow per day",
        type="integer",
        required=False

    ), dict(
        name="unfollow_recent_feed",
        key="unfollow_recent_feed",
        source=dict(argv=["--unfollow-recent-feed"]),
        description="If enabled, will populate database with users from recent feed and unfollow if they meet the conditions. Disable if you only want the bot to unfollow people it has previously followed.",
        type="integer",
        required=False
    ), dict(
        name="unlike_per_run",
        key="unlike_per_run",
        source=dict(argv=["--unlike-per-run"]),
        description="Number of media to unlike that the bot has previously liked. Set to 0 to disable.",
        type="integer",
        required=False
    ), dict(
        name="time_till_unlike",
        key="time_till_unlike",
        source=dict(argv=["--time-till-unlike"]),
        description="How long to wait after liking media before u",
        type="integer",
        required=False
    ), dict(
        name="comment_list",
        key="comment_list",
        source=dict(argv=["--comment-list"]),
        description="List of word lists for comment generation. @username@ will be replaced by the media owner's username",
        required=False), dict(
        name="tag_list",
        key="tag_list",
        source=dict(argv=["--tag-list"]),
        description="Tags to use for finding posts by hasthag or location(l:locationid from e.g. https://www.instagram.com/explore/locations/212999109/los-angeles-california/)",
        required=False
    ), dict(
        name="max_like_for_one_tag",
        key="max_like_for_one_tag",
        source=dict(argv=["--max-like-for-one-tag"]),
        description="How many media of a given tag to like at once (out of 21)",
        type="integer",
        required=False
    ), dict(
        name="unfollow_break_min",
        key="unfollow_break_min",
        source=dict(argv=["--unfollow-break-min"]),
        description="Minimum seconds to break between unfollows",
        type="integer",
        required=False
    ), dict(
        name="unfollow_break_max",
        key="unfollow_break_max",
        source=dict(argv=["--unfollow-break-max"]),
        description="Maximum seconds to break between unfollows",
        type="integer",
        required=False
    ), dict(
        name="HTTPS Proxy",
        key="proxies.https_proxy",
        source=dict(argv=["--https_proxy"]),
        description="HTTPS proxy ",
        required=False
    ), dict(
        name="HTTP Proxy ",
        key="proxies.http_proxy",
        source=dict(argv=["--proxies"]),
        description="HTTP Proxy",
        required=False
    ), dict(
        name="unfollow_not_following",
        key="unfollow_not_following",
        source=dict(argv=["--unfollow-not-following"], argv_options=dict(nargs='?', const=True)),
        description="Unfollow Condition: Unfollow those who do not follow you back",
        required=False
    ), dict(
        name="unfollow_inactive",
        key="unfollow_inactive",
        source=dict(argv=["--unfollow-inactive"], argv_options=dict(nargs='?', const=True)),
        description="Unfollow Condition: Unfollow those who have not posted in a while (inactive)",
        required=False
    ), dict(
        name="unfollow_probably_fake",
        key="unfollow_probably_fake",
        source=dict(argv=["--unfollow-probably-fake"], argv_options=dict(nargs='?', const=True)),
        description="Unfollow Condition: Unfollow accounts which skewed follow/follower ratio (probably fake)",
        required=False
    ), dict(
        name="unfollow_selebgram",
        key="unfollow_selebgram",
        source=dict(argv=["--unfollow-selebgram"], argv_options=dict(nargs='?', const=True)),
        description="Unfollow Condition: Unfollow (celebrity) accounts with too many followers and not enough following",
        required=False
    ), dict(
        name="unfollow_everyone",
        key="unfollow_everyone",
        source=dict(argv=["--unfollow-everyone"], argv_options=dict(nargs='?', const=True)),
        description="Unfollow Condition: Will unfollow everyone in unfollow queue (wildcard condition)",
        required=False
    ), dict(
        name="Verbosity",
        key="verbosity",
        source=dict(argv=['-v'], argv_options=dict(action='count')),
        description="verbosity level -v = INFO, -vv == DEBUG",
        required=False

    ), dict(
        name="configuration file",
        key="config.file",
        source=dict(argv=['-c']),
        description="Configuration file ",
        required=False

    ), dict(
        name="Show release version",
        key="show_version",
        source=dict(argv=["--version"], argv_options=dict(nargs='?', const=True)),
        description="Show Instabot version",
        required=False
    ), dict(
        name="Ignore updates",
        key="ignore_updates",
        source=dict(argv=["--ignore-updates"], argv_options=dict(nargs='?', const=True)),
        description="Ignore updates",
        required=False
    ), dict(
        name="Dump configuration",
        key="dump_configuration",
        source=dict(argv=["--dump"], argv_options=dict(nargs='?', const=True)),
        description="Dumps current configuration",
        required=False
    )

]

defaults = {'config42': OrderedDict(
    [
        ('argv', dict(handler=ArgParse, schema=schema)),
        ('env', {'prefix': 'INSTABOT'}),
        ('file', {'path': 'instabot.config.yml'}),
    ]
)
}


def get_last_version():
    url = "https://pypi.org/pypi/instabot-py/json"
    try:
        version = requests.get(url).json()['info']['version']
    except:
        version = None
    return version


def configure_logging(config):
    if config.get('verbosity'):
        verbosity = int(config.get('verbosity'))
        if verbosity == 1:
            level = logging.INFO
        elif verbosity > 1:
            level = logging.DEBUG
        config.set("logging.root.level", level)

    logging.config.dictConfig(config.get("logging"))


def main():
    config = ConfigManager()
    config.set_many(DEFAULT_CONFIG)
    _config = ConfigManager(schema=schema, defaults=defaults)
    config.set_many(_config.as_dict())
    config_file = _config.get('config.file')
    config.set_many(ConfigManager(schema=schema, path=config_file).as_dict())
    config.set_many(_config.as_dict())
    config.commit()

    configure_logging(config)
    if config.get('dump_configuration'):
        conf = config.as_dict()
        conf.pop('config42')
        conf.pop('dump_configuration')
        print(yaml.dump(conf))
        exit(0)
    if config.get('show_version'):
        print("Installed version {}".format(instabot_py.__version__))
        exit(0)

    if not config.get('ignore_updates'):
        last_version = get_last_version()
        if last_version and last_version != instabot_py.__version__:
            print("Newer version available: {}, The current version: {}".format(last_version, instabot_py.__version__))
            print("To update, please type \n python3 -m pip install instabot-py --upgrade --no-cache-dir ")
            print("")
            print("  > You can ignore warning, run the instabot with --ignore-updates flag")
            exit(0)

    try:
        bot = InstaBot(config=config)
        if config_file:
            bot.logger.info(f"Reading configuration ({len(_config.as_dict())} settings) from {config_file}")
        else:
            bot.logger.info(f"Use the default configuration, add '-c your-config.yml' to specify your config")

    except CredsMissing:
        print("You didn't provide your Instagram login & password or you didn't specify the configuration file")
        print("Try again :")
        print("")
        print("   instabot-py --login YOUR_LOGIN --password YOUR_PASSWORD")
        print("   instabot-py -c your-config.yml")
        print("You can export and modify the default configuration by typing the command below")
        print("    instabot-py --dump")
        exit(1)
    bot.mainloop()


if __name__ == "__main__":
    main()
