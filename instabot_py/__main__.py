#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import json
import os
import re
import sys

if os.name != "nt":
    from blessings import Terminal

    OS_IS_NT = False
    TERM = Terminal()
else:
    OS_IS_NT = True

from instabot_py import InstaBot

python_version_test = f"If you are reading this error, you are not running Python 3.6 or greater. Check 'python --version' or 'python3 --version'."

config_location = "instabot.config.ini"
config = configparser.ConfigParser()


def ask_question(_q, label="", tip="", prepend="", header=" Instabot Configurator "):
    if OS_IS_NT:
        print(f"\n")
        print(f"=============\n{label}")
        print(f"{tip}")
        return input(f"{_q} : {prepend}")

    with TERM.fullscreen():
        with TERM.location(int((TERM.width / 2) - (len(header) / 2)), 1):
            print(TERM.white_on_blue(header))
        with TERM.location(1, TERM.height - 5):
            print(TERM.italic(TERM.white_on_black(label)))

        with TERM.location(
                int((TERM.width / 2) - (len(tip) / 2)), int((TERM.height / 2) + 3)
        ):
            print(TERM.italic(TERM.white_on_black(tip)))

        with TERM.location(
                int(TERM.width - ((TERM.width / 2) + (len(_q) / 2))),
                int(TERM.height / 2) - 2,
        ):
            print(TERM.bold(_q))

        with TERM.location(
                int((TERM.width / 2) - (len(_q) / 2)), int(TERM.height / 2) + 1
        ):
            print("-" * len(_q), end="")

        with TERM.location(
                int(TERM.width - ((TERM.width / 2) + (len(_q) / 2))), int((TERM.height / 2))
        ):
            print(prepend, end="")
            _input = input()
        TERM.clear_eos()
        return _input


def setupinteractive(config, config_location="instabot.config.ini"):
    if os.path.isfile(config_location):
        config.read(config_location)
    elif os.path.isfile("config.ini"):
        config.read("config.ini")

    configsettings = {
        "password": "req",
        "like_per_day": "opt",
        "comments_per_day": "opt",
        "max_like_for_one_tag": "opt",
        "follow_per_day": "opt",
        "follow_time": "opt",
        "unfollow_per_day": "opt",
        "tag_list": "opt",
        "unfollow_selebgram": "opt",
        "unfollow_probably_fake": "opt",
        "unfollow_inactive": "opt",
        "unfollow_recent_feed": "opt",
    }

    configsettings_labels = {
        "like_per_day": "The bot will adjust its speed to LIKE this amount of posts in a 24H period (max ~1200, new accounts accounts ~250)",
        "follow_per_day": "The bot will adjust its speed to FOLLOW this amount of accounts in a 24H period (max ~290)",
        "follow_time": "After following an account, the bot will wait this amount of SECONDS before it checks if an account should be unfollowed (if it meets the unfollow criteria)",
        "unfollow_per_day": "The bot will adjust its speed to UNFOLLOW this amount of accounts in a 24H period (max ~250)",
        "unfollow_selebgram": "(Unfollow Criteria) Unfollow accounts that are possibly celebrities/influencers (True/False)",
        "unfollow_probably_fake": "(Unfollow Criteria) Unfollow accounts w/ few followers and high following (True/False)",
        "unfollow_inactive": "(Unfollow Criteria) Unfollow accounts that seem to be inactive (True/False)",
        "unfollow_recent_feed": "Fetches acounts from your recent feed and queues them for unfollow if they meet the (Unfollow Criteria) (True/False)",
    }

    config["DEFAULT"] = {
        "username": "none",
        "password": "none",
        "like_per_day": 709,
        "comments_per_day": 31,
        "max_like_for_one_tag": 36,
        "follow_per_day": 260,
        "follow_time": 36000,
        "unfollow_per_day": 247,
        "unfollow_break_min": 3,
        "unfollow_break_max": 17,
        "log_mod": 0,
        "proxy": "",
        "unfollow_selebgram": "False",
        "unfollow_probably_fake": "True",
        "unfollow_inactive": "True",
        "unfollow_recent_feed": "False",
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

    confusername = None
    while confusername is None or len(confusername) < 3:
        confusername = str(
            ask_question(
                "Please enter the username you wish to configure:",
                prepend="@",
                tip="Your username is NOT your email or your phone number!",
            )
        )
        confusername.lower()
        if confusername[0] == "@":
            confusername = confusername[1:]
        # if confusername is None or len(confusername) < 3:
        # print("This field is required.")

    if confusername in config:
        # print("User already configured. Modifying...")
        existing_user = True
    else:
        config.add_section(confusername)
        existing_user = False

    config[confusername]["username"] = confusername

    # print("    >>> TIP: Press Enter to skip and set default values")
    for setting, reqset in configsettings.items():

        requiredset = None
        if existing_user:
            prompt_text = f"Press Enter for previous value: "
            section = confusername
        else:
            prompt_text = f"Press Enter for default: "
            section = "DEFAULT"

        while requiredset is None:
            if reqset is "req":
                confvar = ask_question(
                    f"Enter value for '{setting}':", tip="This field is required"
                )
                if confvar == "" or len(confvar) < 3:
                    print("This field is required")
                else:
                    config[confusername][setting] = str(confvar)
                    requiredset = "done"
            else:
                if setting == "tag_list":
                    confvar = ask_question(
                        "Enter tags (or skip to defaults):",
                        tip="Enter the hashtags you would like to target separated with commas",
                        label="Example: follow4follow, instagood, f2f, instalifo",
                    )
                else:
                    if setting in configsettings_labels:
                        if OS_IS_NT:
                            _label = f"{setting} : {configsettings_labels[setting]}"
                        else:
                            _label = f"{TERM.underline(setting)} : {configsettings_labels[setting]}"
                    else:
                        _label = ""
                    confvar = ask_question(
                        f"Enter value for '{setting}':",
                        label=_label,
                        tip=f"{prompt_text}{config[section][setting]}",
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


def interactive(askusername=None, loaded_with_argv=False):
    if not os.path.isfile(config_location) and not os.path.isfile("config.ini"):
        overwrite_answer = None
        while overwrite_answer not in ("yes", "no", "n", "y"):
            overwrite_answer = ask_question(
                "Config file does not exist. Would you like to setup now? (yes/no): "
            )
            overwrite_answer = overwrite_answer.lower()
            if overwrite_answer == "no" or overwrite_answer == "n":
                exit()
        setupinteractive(config, config_location)

    if os.path.isfile(config_location):
        config.read(config_location)
    elif os.path.isfile("config.ini"):
        config.read("config.ini")

    while askusername is None:
        askusername = ask_question(
            "Please enter your username:",
            tip='To change user settings, type "config"',
            header=" Instabot Login",
            prepend="@",
        )
        askusername = askusername.lower()
        if len(askusername) < 3:
            askusername = None

    if askusername[0] == "@":
        askusername = askusername[1:]

    if askusername == "config":
        setupinteractive(config, config_location)
    elif askusername in config:
        print(f"     Loading settings for {askusername}!")
        if os.path.isfile(config_location):
            print(f"     Config: {os.path.abspath(config_location)} ")
        else:
            print(f"     Config: {os.path.abspath('config.ini')} ")
        if loaded_with_argv is False:
            print(
                f"     (Tip: Log in directly by running 'instabot-py {askusername}')'"
            )
    else:
        if "yes" in ask_question(
                "Could not find user in settings. Would you like to add now? (yes/no): "
        ):
            setupinteractive(config, config_location)
        else:
            exit()

    print("\n     ______Starting bot_____")

    configdict = dict(config.items(askusername))

    for _setting, _value in configdict.items():

        try:
            if "{" in _value or "[" in _value:
                json.loads(_value)
                configdict[_setting] = json.loads(_value)
            else:
                raise ValueError
        except ValueError:
            if _value.isdigit() is True:
                configdict[_setting] = int(_value)
            if _value.lower == "true":
                configdict[_setting] = True
            if _value.lower == "false":
                configdict[_setting] = False
            if _value.lower == "none":
                configdict[_setting] = None
            pass

    configdict["login"] = configdict.pop("username")
    return configdict


if __name__ == "__main__":
    if len(sys.argv) > 1:
        param = sys.argv[1].lower()
        if param == "--":
            configdict = {}
        else:
            configdict = interactive(param, loaded_with_argv=True)
    else:
        configdict = interactive()

    bot = InstaBot(**configdict)
    bot.mainloop()
