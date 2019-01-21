#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function
from instabot_py.unfollow_protocol import unfollow_protocol
from instabot_py.follow_protocol import follow_protocol
from instabot_py.feed_scanner import feed_scanner
from instabot_py.check_status import check_status
from instabot_py import InstaBot
import configparser
import os
import sys
import time
import json
import sys
import re

python_version_test = f"If you are reading this error, you are not running Python 3.6 or greater. Check 'python --version' or 'python3 --version'."

try:
    from pip._internal import main
except:
    print(">>> Please install the latest version of pip")


config_location = "config.ini"
config = configparser.ConfigParser()


def setupinteractive(config, config_location="config.ini"):
    if os.path.isfile(config_location):
        config.read(config_location)

    configsettings = {
        "password": "req",
        "like_per_day": "opt",
        "comments_per_day": "opt",
        "max_like_for_one_tag": "opt",
        "follow_per_day": "opt",
        "follow_time": "opt",
        "unfollow_per_day": "opt",
        "unfollow_break_min": "opt",
        "unfollow_break_max": "opt",
        "tag_list": "opt",
    }

    config["DEFAULT"] = {
        "username": "none",
        "password": "none",
        "like_per_day": 709,
        "comments_per_day": 31,
        "max_like_for_one_tag": 36,
        "follow_per_day": 310,
        "follow_time": 3600,
        "unfollow_per_day": 297,
        "unfollow_break_min": 3,
        "unfollow_break_max": 17,
        "log_mod": 0,
        "proxy": "",
    }

    config["DEFAULT"]["comment_list"] = json.dumps(
        [
            ["this", "the", "your"],
            ["photo", "picture", "pic", "shot", "snapshot"],
            ["is", "looks", "feels", "is really"],
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
            [".", "..", "...", "!", "!!", "!!!"],
        ]
    )

    config["DEFAULT"]["tag_list"] = json.dumps(
        ["follow4follow", "f4f", "cute", "l:212999109"]
    )

    config["DEFAULT"]["tag_blacklist"] = json.dumps(["rain", "thunderstorm"])

    config["DEFAULT"]["unwanted_username_list"] = json.dumps(
        [
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
        ]
    )

    config["DEFAULT"]["unfollow_whitelist"] = json.dumps(
        ["example_user_1", "example_user_2"]
    )

    print(
        "\n\n     >>> Setup Wizard >>>\n________________________________________________"
    )
    confusername = None
    while confusername is None or len(confusername) < 3:
        confusername = str(input("Please enter the username you wish to configure: "))
        if confusername is None or len(confusername) < 3:
            print("This field is required.")

    if confusername in config:
        print("User already configured. Modifying...")
        existing_user = True
    else:
        config.add_section(confusername)
        existing_user = False

    config[confusername]["username"] = confusername

    print("    >>> TIP: Press Enter to skip and set default values")
    for setting, reqset in configsettings.items():

        requiredset = None
        if existing_user:
            prompt_text = "Previous set value: "
            section = confusername
        else:
            prompt_text = "Enter for defaults: "
            section = "DEFAULT"

        while requiredset is None:
            if reqset is "req":
                confvar = input(f"Enter value for '{setting}' (Required): ")
                if confvar == "":
                    print("This field is required")
                else:
                    config[confusername][setting] = str(confvar)
                    requiredset = "done"
            else:
                if setting == "tag_list":
                    print(
                        "\n\nAttention!\n\nEnter the hashtags you would like to target separated with commas.\n For example:\n      follow4follow, instagood, f2f, instalifo\n\n"
                    )
                    confvar = input("Enter tags (or skip to defaults): ")
                else:
                    confvar = input(
                        f"Enter value for '{setting} ({prompt_text}{config[section][setting]}):"
                    )
                if setting == "tag_list" and confvar != "":
                    confvar = re.sub(r"\s+", "", confvar)
                    confvar = re.sub(r"#", "", confvar)
                    tags_list = confvar.split(",")
                    config[confusername][setting] = str(json.dumps(tags_list))
                elif confvar == "":
                    # print('Entering default: '+ config[section][setting])
                    if setting != "tag_list":
                        config[confusername][setting] = config[section][setting]
                else:
                    config[confusername][setting] = str(confvar)
                requiredset = "done"

    print("\nWriting to file...")
    with open(config_location, "w") as configfile:
        config.write(configfile)

    print("Config updated! Re-run script to login.")

    exit()


if not os.path.isfile(config_location):
    overwrite_answer = None
    while overwrite_answer not in ("yes", "no", "n", "y"):
        overwrite_answer = input(
            "Config file does not exist. Would you like to setup now? (yes/no): "
        )
        if overwrite_answer == "no" or overwrite_answer == "n":
            exit()
    setupinteractive(config, config_location)

askusername = None
loaded_with_argv = False

try:
    if len(sys.argv[1]) > 3:
        askusername = sys.argv[1]
        loaded_with_argv = True
except:
    askusername = None

config.read(config_location)

if askusername is None:
    askusername = input(
        '     _________LOGIN_________\n     (To change user settings, type "config")\n\n     Please enter your username: '
    )

if askusername == "config":
    setupinteractive(config, config_location)
elif askusername in config:
    print(f"     Loading settings for {askusername}!")
    if loaded_with_argv is False:
        try:
            print(
                f"     (Tip: Log in directly by running '{sys.argv[0]} {askusername}')'"
            )
        except:
            print(
                "     (Tip: Log in directly by appending your username at the end of the script)"
            )

else:
    if "yes" in input(
        "Could not find user in settings. Would you like to add now? (yes/no): "
    ):
        setupinteractive(config, config_location)
    else:
        exit()

usrconfig = askusername

print("\n\n     >>> Starting bot >>>\n________________________________________________")

bot = InstaBot(
    login=config[usrconfig]["username"],
    password=config[usrconfig]["password"],
    like_per_day=int(config[usrconfig]["like_per_day"]),
    comments_per_day=int(config[usrconfig]["comments_per_day"]),
    tag_list=json.loads(config[usrconfig]["tag_list"]),
    tag_blacklist=json.loads(config[usrconfig]["tag_blacklist"]),
    user_blacklist={},
    max_like_for_one_tag=int(config[usrconfig]["max_like_for_one_tag"]),
    follow_per_day=int(config[usrconfig]["follow_per_day"]),
    follow_time=int(config[usrconfig]["follow_time"]),
    unfollow_per_day=int(config[usrconfig]["unfollow_per_day"]),
    unfollow_break_min=int(config[usrconfig]["unfollow_break_min"]),
    unfollow_break_max=int(config[usrconfig]["unfollow_break_max"]),
    log_mod=int(config[usrconfig]["log_mod"]),
    proxy=config[usrconfig]["proxy"],
    # List of list of words, each of which will be used to generate comment
    # For example: "This shot feels wow!"
    comment_list=json.loads(config[usrconfig]["comment_list"]),
    # Use unwanted_username_list to block usernames containing a string
    # Will do partial matches; i.e. 'mozart' will block 'legend_mozart'
    # 'free_followers' will be blocked because it contains 'free'
    unwanted_username_list=json.loads(config[usrconfig]["unwanted_username_list"]),
    unfollow_whitelist=json.loads(config[usrconfig]["unfollow_whitelist"]),
    database_name=f"{usrconfig}.db",
    session_file=f"{usrconfig}.session",
)

while True:
    bot.new_auto_mod()
