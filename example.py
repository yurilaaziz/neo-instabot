#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time

from src import InstaBot
from src.check_status import check_status
from src.feed_scanner import feed_scanner
from src.follow_protocol import follow_protocol
from src.unfollow_protocol import unfollow_protocol

bot = InstaBot(
    login="username",  # Enter username (lowercase). Do not enter email!
    password="password",
    like_per_day=1000,
    comments_per_day=0,
    tag_list=["follow4follow", "f4f", "cute", "l:212999109"],
    tag_blacklist=["rain", "thunderstorm"],
    user_blacklist={},
    max_like_for_one_tag=50,
    follow_per_day=300,
    follow_time=1 * 60 * 60,
    unfollow_per_day=300,
    unlike_per_day=0,
    unfollow_recent_feed=True,  # If True, the bot will also unfollow people who dont follow you using the recent feed. Default: True
    time_till_unlike=3 * 24 * 60 * 60,  # 3 days
    unfollow_break_min=15,
    unfollow_break_max=30,
    user_max_follow=0,
    # session_file=False, # Set to False to disable persistent session, or specify custom session_file (ie ='myusername.session')
    user_min_follow=0,
    log_mod=0,
    proxy="",
    # List of list of words, each of which will be used to generate comment
    # For example: "This shot feels wow!"
    comment_list=[
        ["this", "the", "your"],
        ["photo", "picture", "pic", "shot"],
        ["is", "looks", "is 👉", "is really"],
        [
            "great",
            "super",
            "good",
            "very good",
            "good",
            "wow",
            "WOW",
            "cool",
            "GREAT",
            "magnificent",
            "magical",
            "very cool",
            "stylish",
            "beautiful",
            "so beautiful",
            "so stylish",
            "so professional",
            "lovely",
            "so lovely",
            "very lovely",
            "glorious",
            "so glorious",
            "very glorious",
            "adorable",
            "excellent",
            "amazing",
        ],
        [".", "🙌", "... 👏", "!", "! 😍", "😎"],
    ],
    # Use unwanted_username_list to block usernames containing a string
    # Will do partial matches; i.e. 'mozart' will block 'legend_mozart'
    # 'free_followers' will be blocked because it contains 'free'
    unwanted_username_list=[
        "second",
        "stuff",
        "art",
        "project",
        "love",
        "life",
        "food",
        "blog",
        "free",
        "keren",
        "photo",
        "graphy",
        "indo",
        "travel",
        "art",
        "shop",
        "store",
        "sex",
        "toko",
        "jual",
        "online",
        "murah",
        "jam",
        "kaos",
        "case",
        "baju",
        "fashion",
        "corp",
        "tas",
        "butik",
        "grosir",
        "karpet",
        "sosis",
        "salon",
        "skin",
        "care",
        "cloth",
        "tech",
        "rental",
        "kamera",
        "beauty",
        "express",
        "kredit",
        "collection",
        "impor",
        "preloved",
        "follow",
        "follower",
        "gain",
        ".id",
        "_id",
        "bags",
    ],
    unfollow_whitelist=["example_user_1", "example_user_2"],
    # Enable the following to schedule the bot. Uses 24H
    # end_at_h = 23, # Hour you want the bot to stop
    # end_at_m = 30, # Minute you want the bot stop, in this example 23:30
    # start_at_h = 9, # Hour you want the bot to start
    # start_at_m = 10, # Minute you want the bot to start, in this example 9:10 (am).
)

bot.mainloop()
