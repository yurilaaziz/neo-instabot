#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging.config
from collections import OrderedDict

from config42 import ConfigManager
from config42.handlers import ArgParse

from instabot_py import InstaBot
from instabot_py.default_config import DEFAULT_CONFIG

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
        required=False

    ), dict(
        name="media_max_like",
        key="media_max_like",
        source=dict(argv=["--media-max-like"]),
        description="Maximum number of likes on photos to like (set to 0 to disable)",
        required=False

    ), dict(
        name="media_min_like",
        key="media_min_like",
        source=dict(argv=["--media-min-like"]),
        description="Minimum number of likes on photos to like (set to 0 to disable)",
        required=False

    ), dict(
        name="follow_per_run",
        key="follow_per_run",
        source=dict(argv=["--follow-per-run"]),
        description="Users to follow per day",
        required=False

    ), dict(
        name="follow_time",
        key="follow_time",
        source=dict(argv=["--follow-time"]),
        description="Seconds to wait before unfollowing",
        required=False

    ), dict(
        name="user_min_follow",
        key="user_min_follow",
        source=dict(argv=["--user-min-follow"]),
        description="Check user before following them if they have X minimum of followers. Set 0 to disable",
        required=False

    ), dict(
        name="user_max_follow",
        key="user_max_follow",
        source=dict(argv=["--user-max-follow"]),
        description="Check user before following them if they have X maximum of followers. Set 0 to disable",
        required=False

    ), dict(
        name="unfollow_per_run",
        key="unfollow_per_run",
        source=dict(argv=["--unfollow-per-run"]),
        description="Users to unfollow per day",
        required=False

    ), dict(
        name="unfollow_recent_feed",
        key="unfollow_recent_feed",
        source=dict(argv=["--unfollow-recent-feed"]),
        description="If enabled, will populate database with users from recent feed and unfollow if they meet the conditions. Disable if you only want the bot to unfollow people it has previously followed.",
        required=False
    ), dict(
        name="unlike_per_run",
        key="unlike_per_run",
        source=dict(argv=["--unlike-per-run"]),
        description="Number of media to unlike that the bot has previously liked. Set to 0 to disable.",
        required=False
    ), dict(
        name="time_till_unlike",
        key="time_till_unlike",
        source=dict(argv=["--time-till-unlike"]),
        description="How long to wait after liking media before u",
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
        required=False
    ), dict(
        name="unfollow_break_min",
        key="unfollow_break_min",
        source=dict(argv=["--unfollow-break-min"]),
        description="Minimum seconds to break between unfollows",
        required=False
    ), dict(
        name="unfollow_break_max",
        key="unfollow_break_max",
        source=dict(argv=["--unfollow-break-max"]),
        description="Maximum seconds to break between unfollows",
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
        source=dict(argv=["--unfollow-not-following"]),
        description="Unfollow Condition: Unfollow those who do not follow you back",
        required=False
    ), dict(
        name="unfollow_inactive",
        key="unfollow_inactive",
        source=dict(argv=["--unfollow-inactive"]),
        description="Unfollow Condition: Unfollow those who have not posted in a while (inactive)",
        required=False
    ), dict(
        name="unfollow_probably_fake",
        key="unfollow_probably_fake",
        source=dict(argv=["--unfollow-probably-fake"]),
        description="Unfollow Condition: Unfollow accounts which skewed follow/follower ratio (probably fake)",
        required=False
    ), dict(
        name="unfollow_selebgram",
        key="unfollow_selebgram",
        source=dict(argv=["--unfollow-selebgram"]),
        description="Unfollow Condition: Unfollow (celebrity) accounts with too many followers and not enough following",
        required=False
    ), dict(
        name="unfollow_everyone",
        key="unfollow_everyone",
        source=dict(argv=["--unfollow-everyone"]),
        description="Unfollow Condition: Will unfollow everyone in unfollow queue (wildcard condition)",
        required=False
    ), dict(
        name="Legacy Interactive Mode",
        key="interactive",
        source=dict(argv=["-i", "--interactive"]),
        description="Activate Interactive Mode ",
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

    )

]
defaults = {'config42': OrderedDict(
    [
        ('argv', dict(handler=ArgParse, schema=schema)),
        ('env', {'prefix': 'INSTABOT'}),
        # ('file', {'path': 'instabot.config.yml'}),
    ]
)
}


def main():
    config = ConfigManager()
    config.set_many(DEFAULT_CONFIG)
    _config = ConfigManager(schema=schema, defaults=defaults)
    config.set_many(_config.as_dict())
    config.set_many(ConfigManager(path=_config.get('config.file')).as_dict())
    config.set_many(_config.as_dict())
    config.commit()
    if config.get('verbosity'):
        verbosity = int(config.get('verbosity'))
        if verbosity == 1:
            level = logging.INFO
        elif verbosity > 1:
            level = logging.DEBUG
        config.set("logging.root.level", level)

    logging.config.dictConfig(config.get("logging"))
    bot = InstaBot(config=config)
    bot.mainloop()


if __name__ == "__main__":
    main()
