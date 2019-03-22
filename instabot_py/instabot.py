#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import atexit
import datetime
import importlib
import itertools
import json
import logging
import os
import pickle
import random
import re
import signal
import sqlite3
import sys
import time

from .sql_updates import check_already_followed, check_already_unfollowed
from .sql_updates import check_and_insert_user_agent
from .sql_updates import check_and_update, check_already_liked
from .sql_updates import (
    get_username_row_count,
    check_if_userid_exists,
    get_medias_to_unlike,
    update_media_complete,
)
from .sql_updates import get_username_to_unfollow_random
from .sql_updates import insert_media, insert_username, insert_unfollow_count

python_version_test = f"If you are reading this error, you are not running Python 3.6 or greater. Check 'python --version' or 'python3 --version'."

# Required Dependencies and Modules, offer to install them automatically
# Keep fake_useragent last, quirk for pythonanywhere
required_modules = ["requests", "instaloader", "threading", "fake_useragent"]

for modname in required_modules:
    try:
        # try to import the module normally and put it in globals
        globals()[modname] = importlib.import_module(modname)
    except ImportError as e:
        if modname != "fake_useragent":
            print(
                f"Failed to load module {modname}. Make sure you have installed correctly all dependencies."
            )
            if modname == "instaloader":
                print(
                    f"If instaloader keeps failing and you are running this script on a Raspberry, please visit this project's Wiki on GitHub (https://github.com/instabot-py/instabot.py/wiki) for more information."
                )
            quit()


class InstaBot:
    """
    Instabot.py version 1.2.4

    """

    database_name = None
    session_file = None
    follows_db = None
    follows_db_c = None

    url = "https://www.instagram.com/"
    url_tag = "https://www.instagram.com/explore/tags/%s/?__a=1"
    url_location = "https://www.instagram.com/explore/locations/%s/?__a=1"
    url_likes = "https://www.instagram.com/web/likes/%s/like/"
    url_unlike = "https://www.instagram.com/web/likes/%s/unlike/"
    url_comment = "https://www.instagram.com/web/comments/%s/add/"
    url_follow = "https://www.instagram.com/web/friendships/%s/follow/"
    url_unfollow = "https://www.instagram.com/web/friendships/%s/unfollow/"
    url_login = "https://www.instagram.com/accounts/login/ajax/"
    url_logout = "https://www.instagram.com/accounts/logout/"
    url_media_detail = "https://www.instagram.com/p/%s/?__a=1"
    url_media = "https://www.instagram.com/p/%s/"
    url_user_detail = "https://www.instagram.com/%s/"
    api_user_detail = "https://i.instagram.com/api/v1/users/%s/info/"
    instabot_repo_update = (
        "https://github.com/instabot-py/instabot.py/raw/master/version.txt"
    )

    user_agent = "" ""
    accept_language = "en-US,en;q=0.5"

    # If instagram ban you - query return 400 error.
    error_400 = 0
    # If you have 3 400 error in row - looks like you banned.
    error_400_to_ban = 3
    # If InstaBot think you are banned - going to sleep.
    ban_sleep_time = 3 * 60 * 60

    # All counter.
    bot_mode = 0
    like_counter = 0
    follow_counter = 0
    unfollow_counter = 0
    comments_counter = 0
    current_user = "hajka"
    current_index = 0
    current_id = "abcds"
    # List of user_id, that bot follow
    bot_follow_list = []
    user_info_list = []
    user_list = []
    ex_user_list = []
    unwanted_username_list = []
    is_checked = False
    is_selebgram = False
    is_fake_account = False
    is_active_user = False
    is_following = False
    is_follower = False
    is_rejected = False
    is_self_checking = False
    is_by_tag = False
    is_follower_number = 0

    self_following = 0
    self_follower = 0

    # Log setting.
    logging.basicConfig(filename="errors.log", level=logging.INFO)
    log_file_path = ""
    log_file = 0

    # Other.
    user_id = 0
    media_by_tag = 0
    media_on_feed = []
    media_by_user = []
    login_status = False
    by_location = False

    # Running Times
    start_at_h = 0
    start_at_m = 0
    end_at_h = 23
    end_at_m = 59

    # For new_auto_mod
    next_iteration = {
        "Like": 0,
        "Unlike": 0,
        "Follow": 0,
        "Unfollow": 0,
        "Comments": 0,
        "Populate": 0,
    }
    prog_run = True

    def __init__(
        self,
        login,
        password,
        like_per_day=1000,
        unlike_per_day=0,
        media_max_like=150,
        media_min_like=0,
        user_max_follow=0,
        user_min_follow=0,
        follow_per_day=0,
        time_till_unlike=3 * 24 * 60 * 60,  # Cannot be zero
        follow_time=5 * 60 * 60,  # Cannot be zero
        follow_time_enabled=True,
        unfollow_per_day=0,
        unfollow_recent_feed=True,
        start_at_h=0,
        start_at_m=0,
        end_at_h=23,
        end_at_m=59,
        database_name=None,
        session_file=None,
        unfollow_not_following=True,
        unfollow_inactive=True,
        unfollow_probably_fake=True,
        unfollow_selebgram=False,
        unfollow_everyone=False,
        # False = disabled, None = Will use default username.session notation, string = will use that as filename
        comment_list=[
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
        ],
        comments_per_day=0,
        tag_list=["cat", "car", "dog"],
        max_like_for_one_tag=5,
        unfollow_break_min=15,
        unfollow_break_max=30,
        log_mod=0,
        proxy="",
        user_blacklist={},
        tag_blacklist=[],
        unwanted_username_list=[],
        unfollow_whitelist=[],
    ):

        if session_file is not None and session_file is not False:
            self.session_file = session_file
        elif session_file is False:
            self.session_file = None
        else:
            self.session_file = f"{login.lower()}.session"

        if database_name is not None:
            self.database_name = database_name
        else:
            self.database_name = f"{login.lower()}.db"
        self.follows_db = sqlite3.connect(
            self.database_name, timeout=0, isolation_level=None
        )
        self.follows_db_c = self.follows_db.cursor()
        check_and_update(self)
        list_of_ua = [
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; FSL 7.0.6.01001)",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; FSL 7.0.7.01001)",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; FSL 7.0.5.01003)",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0",
            "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8",
            "Mozilla/5.0 (Windows NT 5.1; rv:13.0) Gecko/20100101 Firefox/13.0.1",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:11.0) Gecko/20100101 Firefox/11.0",
            "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0; .NET CLR 1.0.3705)",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)",
            "Opera/9.80 (Windows NT 5.1; U; en) Presto/2.10.289 Version/12.01",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)",
            "Mozilla/5.0 (Windows NT 5.1; rv:5.0.1) Gecko/20100101 Firefox/5.0.1",
            "Mozilla/5.0 (Windows NT 6.1; rv:5.0) Gecko/20100101 Firefox/5.02",
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.112 Safari/535.1",
            "Mozilla/4.0 (compatible; MSIE 6.0; MSIE 5.5; Windows NT 5.0) Opera 7.02 Bork-edition [en]",
        ]
        try:
            fallback = random.sample(list_of_ua, 1)
            fake_ua = fake_useragent.UserAgent(fallback=fallback[0])
            self.user_agent = check_and_insert_user_agent(self, str(fake_ua))
        except:
            fake_ua = random.sample(list_of_ua, 1)
            self.user_agent = check_and_insert_user_agent(self, str(fake_ua[0]))

        self.current_version = 1_553_282_075

        self.bot_start = datetime.datetime.now()
        self.bot_start_ts = time.time()
        self.start_at_h = start_at_h
        self.start_at_m = start_at_m
        self.end_at_h = end_at_h
        self.end_at_m = end_at_m
        self.unfollow_break_min = unfollow_break_min
        self.unfollow_break_max = unfollow_break_max
        self.user_blacklist = user_blacklist
        self.tag_blacklist = tag_blacklist
        self.unfollow_whitelist = unfollow_whitelist
        self.comment_list = comment_list
        self.instaloader = instaloader.Instaloader()

        # Unfollow Criteria & Options
        self.unfollow_recent_feed = unfollow_recent_feed
        self.unfollow_not_following = unfollow_not_following
        self.unfollow_inactive = unfollow_inactive
        self.unfollow_probably_fake = unfollow_probably_fake
        self.unfollow_selebgram = unfollow_selebgram
        self.unfollow_everyone = unfollow_everyone

        self.time_in_day = 24 * 60 * 60
        # Like
        self.like_per_day = like_per_day
        if self.like_per_day != 0:
            self.like_delay = self.time_in_day / self.like_per_day

        # Unlike
        self.time_till_unlike = time_till_unlike
        self.unlike_per_day = unlike_per_day
        if self.unlike_per_day != 0:
            self.unlike_per_day = self.time_in_day / self.unlike_per_day

        # Follow
        self.follow_time = follow_time  # Cannot be zero
        self.follow_time_enabled = follow_time_enabled
        self.follow_per_day = follow_per_day
        if self.follow_per_day != 0:
            self.follow_delay = self.time_in_day / self.follow_per_day

        # Unfollow
        self.unfollow_per_day = unfollow_per_day
        if self.unfollow_per_day != 0:
            self.unfollow_delay = self.time_in_day / self.unfollow_per_day

        # Comment
        self.comments_per_day = comments_per_day
        if self.comments_per_day != 0:
            self.comments_delay = self.time_in_day / self.comments_per_day

        # Don't like if media have more than n likes.
        self.media_max_like = media_max_like
        # Don't like if media have less than n likes.
        self.media_min_like = media_min_like
        # Don't follow if user have more than n followers.
        self.user_max_follow = user_max_follow
        # Don't follow if user have less than n followers.
        self.user_min_follow = user_min_follow

        # Auto mod seting:
        # Default list of tag.
        self.tag_list = tag_list
        # Get random tag, from tag_list, and like (1 to n) times.
        self.max_like_for_one_tag = max_like_for_one_tag
        # log_mod 0 to console, 1 to file
        self.log_mod = log_mod
        self.s = requests.Session()
        self.c = requests.Session()
        # if you need proxy make something like this:
        # self.s.proxies = {"https" : "http://proxyip:proxyport"}
        # by @ageorgios
        if proxy != "":
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            self.s.proxies.update(proxies)
            self.c.proxies.update(proxies)
        # convert login to lower
        self.user_login = login.lower()
        self.user_password = password
        self.bot_mode = 0
        self.media_by_tag = []
        self.media_on_feed = []
        self.media_by_user = []
        self.current_user_info = ""
        self.unwanted_username_list = unwanted_username_list
        now_time = datetime.datetime.now()
        self.check_for_bot_update()
        log_string = "Instabot v1.2.5/0 started at %s:" % (
            now_time.strftime("%d.%m.%Y %H:%M")
        )
        self.write_log(log_string)
        self.login()
        self.populate_user_blacklist()
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        atexit.register(self.cleanup)
        self.instaload = instaloader.Instaloader()

    def check_for_bot_update(self):
        self.write_log("Checking for updates...")

        try:
            # CHANGE THIS TO OFFICIAL REPO IF KEPT
            updated_timestamp = self.c.get(self.instabot_repo_update)
            if int(updated_timestamp.text) > self.current_version:
                self.write_log(
                    "> UPDATE AVAILABLE Please update Instabot 'python3 -m pip install instabot-py --upgrade' "
                )
            else:
                self.write_log("You are running the latest stable version")
        except:
            self.write_log("Could not check for updates")

    def get_user_id_by_username(self, user_name):
        url_info = self.url_user_detail % (user_name)
        info = self.s.get(url_info)
        json_info = json.loads(
            re.search(
                "window._sharedData = (.*?);</script>", info.text, re.DOTALL
            ).group(1)
        )
        id_user = json_info["entry_data"]["ProfilePage"][0]["graphql"]["user"]["id"]
        return id_user

    def populate_user_blacklist(self):
        for user in self.user_blacklist:
            user_id_url = self.url_user_detail % (user)
            info = self.s.get(user_id_url)

            # prevent error if 'Account of user was deleted or link is invalid
            from json import JSONDecodeError

            try:
                all_data = json.loads(
                    re.search(
                        "window._sharedData = (.*?);</script>", info.text, re.DOTALL
                    ).group(1)
                )
            except JSONDecodeError as e:
                self.write_log(
                    f"Account of user {user} was deleted or link is " "invalid"
                )
            else:
                # prevent exception if user have no media
                id_user = all_data["entry_data"]["ProfilePage"][0]["graphql"]["user"][
                    "id"
                ]
                # Update the user_name with the user_id
                self.user_blacklist[user] = id_user
                self.write_log(f"Blacklisted user {user} added with ID: {id_user}")
                time.sleep(5 * random.random())

    def login(self):

        successfulLogin = False

        self.s.headers.update(
            {
                "Accept": "*/*",
                "Accept-Language": self.accept_language,
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Host": "www.instagram.com",
                "Origin": "https://www.instagram.com",
                "Referer": "https://www.instagram.com/",
                "User-Agent": self.user_agent,
                "X-Instagram-AJAX": "1",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

        if self.session_file is not None and os.path.isfile(self.session_file):
            self.write_log(f"Found session file {self.session_file}")
            successfulLogin = True
            with open(self.session_file, "rb") as i:
                cookies = pickle.load(i)
                self.s.cookies.update(cookies)
        else:
            self.write_log("Trying to login as {}...".format(self.user_login))
            self.login_post = {
                "username": self.user_login,
                "password": self.user_password,
            }
            r = self.s.get(self.url)
            csrf_token = re.search('(?<="csrf_token":")\w+', r.text).group(0)
            self.s.headers.update({"X-CSRFToken": csrf_token})
            time.sleep(5 * random.random())
            login = self.s.post(
                self.url_login, data=self.login_post, allow_redirects=True
            )
            if (
                login.status_code != 200 and login.status_code != 400
            ):  # Handling Other Status Codes and making debug easier!!
                self.write_log("Request didn't return 200 as status code!")
                self.write_log("Here is more info for debbugin or creating an issue")
                print("=" * 15)
                print("Response Status: ", login.status_code)
                print("=" * 15)
                print("Response Content:\n", login.text)
                print("=" * 15)
                print("Response Header:\n", login.headers)
                print("=" * 15)
                return

            loginResponse = login.json()
            try:
                self.csrftoken = login.cookies["csrftoken"]
                self.s.headers.update({"X-CSRFToken": login.cookies["csrftoken"]})
            except Exception as e:
                self.write_log("Something wrong with login")
                self.write_log(login.text)
            if loginResponse.get("errors"):
                self.write_log(
                    "Something is wrong with Instagram! Please try again later..."
                )
                for error in loginResponse["errors"]["error"]:
                    self.write_log(f"Error =>{error}")
                return
            if loginResponse.get("message") == "checkpoint_required":
                try:
                    if "instagram.com" in loginResponse["checkpoint_url"]:
                        challenge_url = loginResponse["checkpoint_url"]
                    else:
                        challenge_url = (
                            f"https://instagram.com{loginResponse['checkpoint_url']}"
                        )
                    self.write_log(f"Challenge required at {challenge_url}")
                    with self.s as clg:
                        clg.headers.update(
                            {
                                "Accept": "*/*",
                                "Accept-Language": self.accept_language,
                                "Accept-Encoding": "gzip, deflate, br",
                                "Connection": "keep-alive",
                                "Host": "www.instagram.com",
                                "Origin": "https://www.instagram.com",
                                "User-Agent": self.user_agent,
                                "X-Instagram-AJAX": "1",
                                "Content-Type": "application/x-www-form-urlencoded",
                                "x-requested-with": "XMLHttpRequest",
                            }
                        )
                        # Get challenge page
                        challenge_request_explore = clg.get(challenge_url)

                        # Get CSRF Token from challenge page
                        challenge_csrf_token = re.search(
                            '(?<="csrf_token":")\w+', challenge_request_explore.text
                        ).group(0)
                        # Get Rollout Hash from challenge page
                        rollout_hash = re.search(
                            '(?<="rollout_hash":")\w+', challenge_request_explore.text
                        ).group(0)

                        # Ask for option 1 from challenge, which is usually Email or Phone
                        challenge_post = {"choice": 1}

                        # Update headers for challenge submit page
                        clg.headers.update({"X-CSRFToken": challenge_csrf_token})
                        clg.headers.update({"Referer": challenge_url})

                        # Request instagram to send a code
                        challenge_request_code = clg.post(
                            challenge_url, data=challenge_post, allow_redirects=True
                        )

                        # User should receive a code soon, ask for it
                        challenge_userinput_code = input(
                            "Challenge Required.\n\nEnter the code sent to your mail/phone: "
                        )
                        challenge_security_post = {
                            "security_code": int(challenge_userinput_code)
                        }

                        complete_challenge = clg.post(
                            challenge_url,
                            data=challenge_security_post,
                            allow_redirects=True,
                        )
                        if complete_challenge.status_code != 200:
                            self.write_log("Entered code is wrong, Try again later!")
                            return
                        self.csrftoken = complete_challenge.cookies["csrftoken"]
                        self.s.headers.update(
                            {"X-CSRFToken": self.csrftoken, "X-Instagram-AJAX": "1"}
                        )
                        successfulLogin = complete_challenge.status_code == 200

                except Exception as err:
                    print(f"Login failed, response: \n\n{login.text} {err}")
                    quit()
            elif loginResponse.get("authenticated") is False:
                self.write_log("Login error! Check your login data!")
                return

            else:
                rollout_hash = re.search('(?<="rollout_hash":")\w+', r.text).group(0)
                self.s.headers.update({"X-Instagram-AJAX": rollout_hash})
                successfulLogin = True
            # ig_vw=1536; ig_pr=1.25; ig_vh=772;  ig_or=landscape-primary;
            self.s.cookies["csrftoken"] = self.csrftoken
            self.s.cookies["ig_vw"] = "1536"
            self.s.cookies["ig_pr"] = "1.25"
            self.s.cookies["ig_vh"] = "772"
            self.s.cookies["ig_or"] = "landscape-primary"
            time.sleep(5 * random.random())

        if successfulLogin:
            r = self.s.get("https://www.instagram.com/")
            self.csrftoken = re.search('(?<="csrf_token":")\w+', r.text).group(0)
            self.s.cookies["csrftoken"] = self.csrftoken
            self.s.headers.update({"X-CSRFToken": self.csrftoken})
            finder = r.text.find(self.user_login)
            if finder != -1:
                self.user_id = self.get_user_id_by_username(self.user_login)
                self.login_status = True
                self.write_log(f"{self.user_login} login success!\n")
                if self.session_file is not None:
                    self.write_log(
                        f"Saving cookies to session file {self.session_file}"
                    )
                    with open(self.session_file, "wb") as output:
                        pickle.dump(self.s.cookies, output, pickle.HIGHEST_PROTOCOL)
            else:
                self.login_status = False
                self.write_log("Login error! Check your login data!")
                if self.session_file is not None and os.path.isfile(self.session_file):
                    try:
                        os.remove(self.session_file)
                    except:
                        self.write_log(
                            "Could not delete session file. Please delete manually"
                        )

                self.prog_run = False
        else:
            self.write_log("Login error! Connection error!")

    def logout(self):
        now_time = datetime.datetime.now()
        log_string = (
            "Logout: likes - %i, follow - %i, unfollow - %i, comments - %i."
            % (
                self.like_counter,
                self.follow_counter,
                self.unfollow_counter,
                self.comments_counter,
            )
        )
        self.write_log(log_string)
        work_time = datetime.datetime.now() - self.bot_start
        self.write_log(f"Bot work time: {work_time}")

        try:
            logout_post = {"csrfmiddlewaretoken": self.csrftoken}
            logout = self.s.post(self.url_logout, data=logout_post)
            self.write_log("Logout success!")
            self.login_status = False
        except:
            logging.exception("Logout error!")

    def cleanup(self, *_):
        # Unfollow all bot follow
        # if self.follow_counter >= self.unfollow_counter:
        #     for i in range(len(self.bot_follow_list)):
        #         f = self.bot_follow_list[0]
        #         if check_already_unfollowed(self, f[0]):
        #             log_string = "Already unfollowed before, skipping: %s" % (f[0])
        #             self.write_log(log_string)
        #         else:
        #             log_string = "Trying to unfollow: %s" % (f[0])
        #             self.write_log(log_string)
        #             self.unfollow_on_cleanup(f[0])
        #             sleeptime = random.randint(
        #                 self.unfollow_break_min, self.unfollow_break_max
        #             )
        #             log_string = "Pausing for %i seconds... %i of %i" % (
        #                 sleeptime,
        #                 self.unfollow_counter,
        #                 self.follow_counter,
        #             )
        #             self.write_log(log_string)
        #             time.sleep(sleeptime)
        #         self.bot_follow_list.remove(f)

        # Logout
        if self.login_status and self.session_file is None:
            self.logout()
        self.prog_run = False

    def get_media_id_by_tag(self, tag):
        """ Get media ID set, by your hashtag or location """

        if self.login_status:
            if tag.startswith("l:"):
                tag = tag.replace("l:", "")
                self.by_location = True
                self.write_log(f"Get Media by location: {tag}")
                if self.login_status == 1:
                    url_location = self.url_location % (tag)
                    try:
                        r = self.s.get(url_location)
                        all_data = json.loads(r.text)
                        self.media_by_tag = list(
                            all_data["graphql"]["location"]["edge_location_to_media"][
                                "edges"
                            ]
                        )
                    except:
                        self.media_by_tag = []
                        self.write_log("Except on get_media!")
                        logging.exception("get_media_id_by_tag")
                else:
                    return 0

            else:
                self.by_location = False
                self.write_log(f"Get Media by tag: {tag}")
                if self.login_status == 1:
                    url_tag = self.url_tag % (tag)
                    try:
                        r = self.s.get(url_tag)
                        all_data = json.loads(r.text)
                        self.media_by_tag = list(
                            all_data["graphql"]["hashtag"]["edge_hashtag_to_media"][
                                "edges"
                            ]
                        )
                    except:
                        self.media_by_tag = []
                        self.write_log("Except on get_media!")
                        logging.exception("get_media_id_by_tag")
                else:
                    return 0

    def get_instagram_url_from_media_id(self, media_id, url_flag=True, only_code=None):
        """ Get Media Code or Full Url from Media ID Thanks to Nikished """
        media_id = int(media_id)
        if url_flag is False:
            return ""
        else:
            alphabet = (
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
            )
            shortened_id = ""
            while media_id > 0:
                media_id, idx = divmod(media_id, 64)
                shortened_id = alphabet[idx] + shortened_id
            if only_code:
                return shortened_id
            else:
                return f"instagram.com/p/{shortened_id}/"

    def get_username_by_media_id(self, media_id):
        """ Get username by media ID Thanks to Nikished """

        if self.login_status:
            if self.login_status == 1:
                media_id_url = self.get_instagram_url_from_media_id(
                    int(media_id), only_code=True
                )
                url_media = self.url_media_detail % (media_id_url)
                try:
                    r = self.s.get(url_media)
                    all_data = json.loads(r.text)

                    username = str(
                        all_data["graphql"]["shortcode_media"]["owner"]["username"]
                    )
                    self.write_log(
                        "media_id="
                        + media_id
                        + ", media_id_url="
                        + media_id_url
                        + ", username_by_media_id="
                        + username
                    )
                    return username
                except:
                    logging.exception("username_by_mediaid exception")
                    return False
            else:
                return ""

    def get_username_by_user_id(self, user_id):
        if self.login_status:
            try:
                profile = instaloader.Profile.from_id(self.instaload.context, user_id)
                username = profile.username
                return username
            except:
                logging.exception("Except on get_username_by_user_id")
                return False
        else:
            return False

    def like_all_exist_media(self, media_size=-1, delay=True):
        """ Like all media ID that have self.media_by_tag """

        if self.login_status:
            if self.media_by_tag != 0:
                i = 0
                for d in self.media_by_tag:
                    # Media count by this tag.
                    if media_size > 0 or media_size < 0:
                        media_size -= 1
                        l_c = self.media_by_tag[i]["node"]["edge_liked_by"]["count"]
                        if (
                            (l_c <= self.media_max_like and l_c >= self.media_min_like)
                            or (self.media_max_like == 0 and l_c >= self.media_min_like)
                            or (self.media_min_like == 0 and l_c <= self.media_max_like)
                            or (self.media_min_like == 0 and self.media_max_like == 0)
                        ):
                            for (
                                blacklisted_user_name,
                                blacklisted_user_id,
                            ) in self.user_blacklist.items():
                                if (
                                    self.media_by_tag[i]["node"]["owner"]["id"]
                                    == blacklisted_user_id
                                ):
                                    self.write_log(
                                        f"Not liking media owned by blacklisted user: {blacklisted_user_name}"
                                    )
                                    return False
                            if (
                                self.media_by_tag[i]["node"]["owner"]["id"]
                                == self.user_id
                            ):
                                self.write_log("Keep calm - It's your own media ;)")
                                return False

                            if (
                                check_already_liked(
                                    self, media_id=self.media_by_tag[i]["node"]["id"]
                                )
                                == 1
                            ):
                                self.write_log("Keep calm - It's already liked ;)")
                                return False
                            try:
                                if (
                                    len(
                                        self.media_by_tag[i]["node"][
                                            "edge_media_to_caption"
                                        ]["edges"]
                                    )
                                    > 1
                                ):
                                    caption = self.media_by_tag[i]["node"][
                                        "edge_media_to_caption"
                                    ]["edges"][0]["node"]["text"].encode(
                                        "ascii", errors="ignore"
                                    )
                                    tag_blacklist = set(self.tag_blacklist)
                                    if sys.version_info[0] == 3:
                                        tags = {
                                            str.lower((tag.decode("ASCII")).strip("#"))
                                            for tag in caption.split()
                                            if (tag.decode("ASCII")).startswith("#")
                                        }
                                    else:
                                        tags = {
                                            unicode.lower(
                                                (tag.decode("ASCII")).strip("#")
                                            )
                                            for tag in caption.split()
                                            if (tag.decode("ASCII")).startswith("#")
                                        }

                                    if tags.intersection(tag_blacklist):
                                        matching_tags = ", ".join(
                                            tags.intersection(tag_blacklist)
                                        )
                                        self.write_log(
                                            f"Not liking media with blacklisted tag(s): {matching_tags}"
                                        )
                                        return False
                            except:
                                logging.exception("Except on like_all_exist_media")
                                return False

                            log_string = (
                                "Trying to like media: %s\n                 %s"
                                % (
                                    self.media_by_tag[i]["node"]["id"],
                                    self.url_media
                                    % self.media_by_tag[i]["node"]["shortcode"],
                                )
                            )
                            self.write_log(log_string)
                            like = self.like(self.media_by_tag[i]["node"]["id"])
                            # comment = self.comment(self.media_by_tag[i]['id'], 'Cool!')
                            # follow = self.follow(self.media_by_tag[i]["owner"]["id"])
                            if like != 0:
                                if like.status_code == 200:
                                    # Like, all ok!
                                    self.error_400 = 0
                                    self.like_counter += 1
                                    log_string = f"Liked: {self.media_by_tag[i]['node']['id']}. Like #{self.like_counter}."
                                    insert_media(
                                        self,
                                        media_id=self.media_by_tag[i]["node"]["id"],
                                        status="200",
                                    )
                                    self.write_log(log_string)
                                elif like.status_code == 400:
                                    self.write_log(
                                        f"Not liked: {like.status_code} message {like.text}"
                                    )
                                    insert_media(
                                        self,
                                        media_id=self.media_by_tag[i]["node"]["id"],
                                        status="400",
                                    )
                                    # Some error. If repeated - can be ban!
                                    if self.error_400 >= self.error_400_to_ban:
                                        # Look like you banned!
                                        time.sleep(self.ban_sleep_time)
                                    else:
                                        self.error_400 += 1
                                else:
                                    insert_media(
                                        self,
                                        media_id=self.media_by_tag[i]["node"]["id"],
                                        status=str(like.status_code),
                                    )
                                    self.write_log(
                                        f"Not liked: {like.status_code} message {like.text}"
                                    )
                                    return False
                                    # Some error.
                                i += 1
                                if delay:
                                    time.sleep(
                                        self.like_delay * 0.9
                                        + self.like_delay * 0.2 * random.random()
                                    )
                                else:
                                    return True
                            else:
                                return False
                        else:
                            return False
                    else:
                        return False
            else:
                self.write_log("No media to like!")

    def like(self, media_id):
        """ Send http request to like media by ID """
        if self.login_status:
            url_likes = self.url_likes % (media_id)
            try:
                like = self.s.post(url_likes)
                last_liked_media_id = media_id
            except:
                logging.exception("Except on like!")
                like = 0
            return like

    def unlike(self, media_id):
        """ Send http request to unlike media by ID """
        if self.login_status:
            url_unlike = self.url_unlike % (media_id)
            try:
                unlike = self.s.post(url_unlike)
            except:
                logging.exception("Except on unlike!")
                unlike = 0
            return unlike

    def comment(self, media_id, comment_text):
        """ Send http request to comment """
        if self.login_status:
            comment_post = {"comment_text": comment_text}
            url_comment = self.url_comment % (media_id)
            try:
                comment = self.s.post(url_comment, data=comment_post)
                if comment.status_code == 200:
                    self.comments_counter += 1
                    log_string = f"Write: {comment_text}. #{self.comments_counter}."
                    self.write_log(log_string)
                return comment
            except:
                logging.exception("Except on comment!")
        return False

    def follow(self, user_id, username=None):
        """ Send http request to follow """
        if self.login_status:
            url_follow = self.url_follow % (user_id)
            if username is None:
                username = self.get_username_by_user_id(user_id=user_id)
            try:
                follow = self.s.post(url_follow)
                if follow.status_code == 200:
                    self.follow_counter += 1
                    log_string = f"Followed: {user_id} #{self.follow_counter}."
                    self.write_log(log_string)
                    insert_username(self, user_id=user_id, username=username)
                return follow
            except:
                logging.exception("Except on follow!")
        return False

    def unfollow(self, user_id):
        """ Send http request to unfollow """
        if self.login_status:
            url_unfollow = self.url_unfollow % (user_id)
            try:
                unfollow = self.s.post(url_unfollow)
                if unfollow.status_code == 200:
                    self.unfollow_counter += 1
                    log_string = f"Unfollowed: {user_id} #{self.unfollow_counter}."
                    self.write_log(log_string)
                    insert_unfollow_count(self, user_id=user_id)
                return unfollow
            except:
                logging.exception("Exept on unfollow!")
        return False

    def unfollow_on_cleanup(self, user_id):
        """ Unfollow on cleanup by @rjmayott """
        if self.login_status:
            url_unfollow = self.url_unfollow % (user_id)
            try:
                unfollow = self.s.post(url_unfollow)
                if unfollow.status_code == 200:
                    self.unfollow_counter += 1
                    log_string = f"Unfollow: {user_id} #{self.unfollow_counter} of {self.follow_counter}."
                    self.write_log(log_string)
                    insert_unfollow_count(self, user_id=user_id)
                else:
                    log_string = (
                        "Slow Down - Pausing for 5 minutes to avoid getting banned"
                    )
                    self.write_log(log_string)
                    time.sleep(300)
                    unfollow = self.s.post(url_unfollow)
                    if unfollow.status_code == 200:
                        self.unfollow_counter += 1
                        log_string = f"Unfollow: {user_id} #{self.unfollow_counter} of {self.follow_counter}."
                        self.write_log(log_string)
                        insert_unfollow_count(self, user_id=user_id)
                    else:
                        log_string = "Still no good :( Skipping and pausing for another 5 minutes"
                        self.write_log(log_string)
                        time.sleep(300)
                    return False
                return unfollow
            except:
                logging.exception("Except on unfollow.")
        return False

    # Backwards Compatibility for old example.py files
    def auto_mod(self):
        self.mainloop()

    def new_auto_mod(self):
        self.mainloop()

    def mainloop(self):
        while self.prog_run and self.login_status:
            now = datetime.datetime.now()
            if datetime.time(
                self.start_at_h, self.start_at_m
            ) <= now.time() and now.time() <= datetime.time(
                self.end_at_h, self.end_at_m
            ):
                # ------------------- Get media_id -------------------
                if len(self.media_by_tag) == 0:
                    self.get_media_id_by_tag(random.choice(self.tag_list))
                    self.this_tag_like_count = 0
                    self.max_tag_like_count = random.randint(
                        1, self.max_like_for_one_tag
                    )
                    self.remove_already_liked()
                # ------------------- Like -------------------
                self.new_auto_mod_like()
                # ------------------- Unlike -------------------
                self.new_auto_mod_unlike()
                # ------------------- Follow -------------------
                self.new_auto_mod_follow()
                # ------------------- Unfollow -------------------
                self.new_auto_mod_unfollow()
                # ------------------- Comment -------------------
                self.new_auto_mod_comments()
                # Bot iteration in 1 sec
                time.sleep(1)
                # print("Tic!")
            else:
                print(
                    "!!sleeping until {hour}:{min}".format(
                        hour=self.start_at_h, min=self.start_at_m
                    ),
                    end="\r",
                )
                time.sleep(100)
        self.write_log("Exit Program... GoodBye")
        sys.exit(0)

    def remove_already_liked(self):
        # This logstring has caused TOO many questions, it serves no good telling them
        # duplicates are removed -- this is expected behaviour after all
        # self.write_log("Removing already liked medias..")
        x = 0
        while x < len(self.media_by_tag):
            if (
                check_already_liked(self, media_id=self.media_by_tag[x]["node"]["id"])
                == 1
            ):
                self.media_by_tag.remove(self.media_by_tag[x])
            else:
                x += 1

    def new_auto_mod_like(self):
        if (
            time.time() > self.next_iteration["Like"]
            and self.like_per_day != 0
            and len(self.media_by_tag) > 0
        ):
            # You have media_id to like:
            if self.like_all_exist_media(media_size=1, delay=False):
                # If like go to sleep:
                self.next_iteration["Like"] = time.time() + self.add_time(
                    self.like_delay
                )
                # Count this tag likes:
                self.this_tag_like_count += 1
                if self.this_tag_like_count >= self.max_tag_like_count:
                    self.media_by_tag = [0]
            # Del first media_id
        try:
            del self.media_by_tag[0]
        except:
            print("Could not remove media")

    def new_auto_mod_unlike(self):
        if time.time() > self.next_iteration["Unlike"] and self.unlike_per_day != 0:
            media = get_medias_to_unlike(self)
            if media:
                self.write_log("Trying to unlike media")
                self.auto_unlike()
                self.next_iteration["Unlike"] = time.time() + self.add_time(
                    self.unfollow_delay
                )

    def new_auto_mod_follow(self):
        username = None
        if time.time() < self.next_iteration["Follow"]:
            return
        if (
            time.time() > self.next_iteration["Follow"]
            and self.follow_per_day != 0
            and len(self.media_by_tag) > 0
        ):
            if self.media_by_tag[0]["node"]["owner"]["id"] == self.user_id:
                self.write_log("Keep calm - It's your own profile ;)")
                return

            if self.user_min_follow != 0 or self.user_max_follow != 0:
                try:
                    username = self.get_username_by_user_id(
                        self.media_by_tag[0]["node"]["owner"]["id"]
                    )
                    url = self.url_user_detail % (username)
                    r = self.s.get(url)
                    all_data = json.loads(
                        re.search(
                            "window._sharedData = (.*?);</script>", r.text, re.DOTALL
                        ).group(1)
                    )
                    followers = all_data["entry_data"]["ProfilePage"][0]["graphql"][
                        "user"
                    ]["edge_followed_by"]["count"]

                    if followers < self.user_min_follow:
                        self.write_log(
                            f"Won't follow {username}: does not meet user_min_follow requirement"
                        )
                        return

                    if self.user_max_follow != 0 and followers > self.user_max_follow:
                        self.write_log(
                            f"Won't follow {username}: does not meet user_max_follow requirement"
                        )
                        return

                except Exception:
                    pass
            if (
                check_already_followed(
                    self, user_id=self.media_by_tag[0]["node"]["owner"]["id"]
                )
                == 1
            ):
                self.write_log(
                    f"Already followed before {self.media_by_tag[0]['node']['owner']['id']}"
                )
                self.next_iteration["Follow"] = time.time() + self.add_time(
                    self.follow_delay / 2
                )
                return

            log_string = (
                f"Trying to follow: {self.media_by_tag[0]['node']['owner']['id']}"
            )
            self.write_log(log_string)
            self.next_iteration["Follow"] = time.time() + self.add_time(
                self.follow_delay
            )

            if (
                self.follow(
                    user_id=self.media_by_tag[0]["node"]["owner"]["id"],
                    username=username,
                )
                is not False
            ):
                self.bot_follow_list.append(
                    [self.media_by_tag[0]["node"]["owner"]["id"], time.time()]
                )
                self.next_iteration["Follow"] = time.time() + self.add_time(
                    self.follow_delay
                )

    def populate_from_feed(self):
        self.get_media_id_recent_feed()

        try:
            for mediafeed_user in self.media_on_feed:
                feed_username = mediafeed_user["node"]["owner"]["username"]
                feed_user_id = mediafeed_user["node"]["owner"]["id"]
                # print(check_if_userid_exists(self, userid=feed_user_id))
                if check_if_userid_exists(self, userid=feed_user_id) is False:
                    insert_username(self, user_id=feed_user_id, username=feed_username)
                    self.write_log(f"Inserted user {feed_username} from recent feed")
        except:
            self.write_log("Notice: could not populate from recent feed")

    def new_auto_mod_unfollow(self):
        if time.time() > self.next_iteration["Unfollow"] and self.unfollow_per_day != 0:

            if (time.time() - self.bot_start_ts) < 30:
                # let bot initialize
                return
            if get_username_row_count(self) < 20:
                self.write_log(
                    f"> Waiting for database to populate before unfollowing (progress {str(get_username_row_count(self))} /20)"
                )

                if self.unfollow_recent_feed is True:
                    self.write_log("Will try to populate using recent feed")
                    self.populate_from_feed()

                self.next_iteration["Unfollow"] = time.time() + (
                    self.add_time(self.unfollow_delay) / 2
                )
                return  # DB doesn't have enough followers yet

            if self.bot_mode == 0 or self.bot_mode == 3:

                try:
                    if (
                        time.time() > self.next_iteration["Populate"]
                        and self.unfollow_recent_feed is True
                    ):
                        self.populate_from_feed()
                        self.next_iteration["Populate"] = time.time() + (
                            self.add_time(360)
                        )
                except:
                    self.write_log(
                        "Notice: Could not populate from recent feed right now"
                    )

                log_string = f"Trying to unfollow #{self.unfollow_counter + 1}:"
                self.write_log(log_string)
                self.auto_unfollow()
                self.next_iteration["Unfollow"] = time.time() + self.add_time(
                    self.unfollow_delay
                )

    def new_auto_mod_comments(self):
        if (
            time.time() > self.next_iteration["Comments"]
            and self.comments_per_day != 0
            and len(self.media_by_tag) > 0
            and self.check_exisiting_comment(self.media_by_tag[0]["node"]["shortcode"])
            is False
        ):
            comment_text = self.generate_comment()
            log_string = f"Trying to comment: {self.media_by_tag[0]['node']['id']}"
            self.write_log(log_string)
            if (
                self.comment(self.media_by_tag[0]["node"]["id"], comment_text)
                is not False
            ):
                self.next_iteration["Comments"] = time.time() + self.add_time(
                    self.comments_delay
                )

    def add_time(self, time):
        """ Make some random for next iteration"""
        return time * 0.9 + time * 0.2 * random.random()

    def generate_comment(self):
        c_list = list(itertools.product(*self.comment_list))

        repl = [("  ", " "), (" .", "."), (" !", "!")]
        res = " ".join(random.choice(c_list))
        for s, r in repl:
            res = res.replace(s, r)
        return res.capitalize()

    def check_exisiting_comment(self, media_code):
        url_check = self.url_media % (media_code)
        try:
            check_comment = self.s.get(url_check)
            if check_comment.status_code == 200:

                if "dialog-404" in check_comment.text:
                    self.write_log(
                        f"Tried to comment {media_code} but it doesn't exist (404). Resuming..."
                    )
                    del self.media_by_tag[0]
                    return True

                all_data = json.loads(
                    re.search(
                        "window._sharedData = (.*?);", check_comment.text, re.DOTALL
                    ).group(1)
                )["entry_data"]["PostPage"][
                    0
                ]  # window._sharedData = (.*?);
                if (
                    all_data["graphql"]["shortcode_media"]["owner"]["id"]
                    == self.user_id
                ):
                    self.write_log("Keep calm - It's your own media ;)")
                    # Del media to don't loop on it
                    del self.media_by_tag[0]
                    return True
                try:
                    comment_list = list(
                        all_data["graphql"]["shortcode_media"]["edge_media_to_comment"][
                            "edges"
                        ]
                    )
                except:
                    comment_list = list(
                        all_data["graphql"]["shortcode_media"][
                            "edge_media_to_parent_comment"
                        ]["edges"]
                    )

                for d in comment_list:
                    if d["node"]["owner"]["id"] == self.user_id:
                        self.write_log("Keep calm - Media already commented ;)")
                        # Del media to don't loop on it
                        del self.media_by_tag[0]
                        return True
                return False
            elif check_comment.status_code == 404:
                insert_media(
                    self,
                    self.media_by_tag[0]["node"]["id"],
                    str(check_comment.status_code),
                )
                self.write_log(
                    f"Tried to comment {media_code} but it doesn't exist (404). Resuming..."
                )
                del self.media_by_tag[0]
                return True
            else:
                insert_media(
                    self,
                    self.media_by_tag[0]["node"]["id"],
                    str(check_comment.status_code),
                )
                self.media_by_tag.remove(self.media_by_tag[0])
                return True
        except:
            self.write_log("Couldn't comment post, resuming.")
            del self.media_by_tag[0]
            return True

    def auto_unlike(self):
        checking = True
        while checking:
            media_to_unlike = get_medias_to_unlike(self)
            if media_to_unlike:
                request = self.unlike(media_to_unlike)
                if request.status_code == 200:
                    update_media_complete(self, media_to_unlike)
                else:
                    self.write_log("Couldn't unlike media, resuming.")
                    checking = False
            else:
                self.write_log("no medias to unlike")
                checking = False

    def auto_unfollow(self):
        checking = True
        while checking:
            username_row = get_username_to_unfollow_random(self)
            if not username_row:
                self.write_log("Looks like there is nobody to unfollow.")
                return False
            current_id = username_row[0]
            current_user = username_row[1]
            unfollow_count = username_row[2]

            if not current_user:
                current_user = self.get_username_by_user_id(user_id=current_id)
            if not current_user:
                log_string = "api limit reached from instagram. Will try later"
                self.write_log(log_string)
                return False
            for wluser in self.unfollow_whitelist:
                if wluser == current_user:
                    log_string = "found whitelist user, starting search again"
                    self.write_log(log_string)
                    break
            else:
                checking = False

        if self.login_status:
            log_string = f"Getting user info : {current_user}"
            self.write_log(log_string)
            if self.login_status == 1:
                url_tag = self.url_user_detail % (current_user)
                try:
                    r = self.s.get(url_tag)
                    if (
                        r.text.find(
                            "The link you followed may be broken, or the page may have been removed."
                        )
                        != -1
                    ):
                        log_string = (
                            f"Looks like account was deleted, skipping : {current_user}"
                        )
                        self.write_log(log_string)
                        insert_unfollow_count(self, user_id=current_id)
                        time.sleep(3)
                        return False
                    all_data = json.loads(
                        re.search(
                            "window._sharedData = (.*?);</script>", r.text, re.DOTALL
                        ).group(1)
                    )["entry_data"]["ProfilePage"][0]

                    user_info = all_data["graphql"]["user"]
                    i = 0
                    log_string = "Checking user info.."
                    self.write_log(log_string)

                    follows = user_info["edge_follow"]["count"]
                    follower = user_info["edge_followed_by"]["count"]
                    media = user_info["edge_owner_to_timeline_media"]["count"]
                    follow_viewer = user_info["follows_viewer"]
                    followed_by_viewer = user_info["followed_by_viewer"]
                    requested_by_viewer = user_info["requested_by_viewer"]
                    has_requested_viewer = user_info["has_requested_viewer"]
                    log_string = f"Follower : {follower}"
                    self.write_log(log_string)
                    log_string = f"Following : {follows}"
                    self.write_log(log_string)
                    log_string = f"Media : {media}"
                    self.write_log(log_string)
                    self.is_selebgram = False
                    self.is_fake_account = False
                    self.is_active_user = True
                    self.is_follower = True
                    if follows == 0 or follower / follows > 2:
                        if self.unfollow_selebgram is True:
                            self.is_selebgram = True
                            self.is_fake_account = False
                            self.write_log("   >This is probably Selebgram account")

                    elif follower == 0 or follows / follower > 2:
                        if self.unfollow_probably_fake is True:
                            self.is_fake_account = True
                            self.is_selebgram = False
                            self.write_log("   >This is probably Fake account")
                    else:
                        self.is_selebgram = False
                        self.is_fake_account = False
                        self.write_log("   >This is a normal account")

                    if media > 0 and follows / media < 25 and follower / media < 25:
                        self.is_active_user = True
                        self.write_log("   >This user is active")
                    else:
                        if self.unfollow_inactive is True:
                            self.is_active_user = False
                            self.write_log("   >This user is passive")

                    if follow_viewer or has_requested_viewer:
                        self.is_follower = True
                        self.write_log("   >This account is following you")
                    else:
                        if self.unfollow_not_following is True:
                            self.is_follower = False
                            self.write_log("   >This account is NOT following you")

                    if followed_by_viewer or requested_by_viewer:
                        self.is_following = True
                        self.write_log("   >You are following this account")

                    else:
                        self.is_following = False
                        self.write_log("   >You are NOT following this account")

                except:
                    logging.exception("Except on auto_unfollow!")
                    time.sleep(3)
                    return False
            else:
                return False

            if (
                self.is_selebgram is not False
                or self.is_fake_account is not False
                or self.is_active_user is not True
                or self.is_follower is not True
            ):
                self.write_log(current_user)
                self.unfollow(current_id)
                # don't insert unfollow count as it is done now inside unfollow()
                # insert_unfollow_count(self, user_id=current_id)
            elif self.unfollow_everyone is True:
                self.write_log(current_user)
                self.unfollow(current_id)
            elif self.is_following is not True:
                # we are not following this account, hence we unfollowed it, let's keep track
                insert_unfollow_count(self, user_id=current_id)

    def unfollow_recent_feed(self):

        if len(self.media_on_feed) == 0:
            self.get_media_id_recent_feed()

        if (
            len(self.media_on_feed) != 0
            and self.is_follower_number < 5
            and time.time() > self.next_iteration["Unfollow"]
            and self.unfollow_per_day != 0
        ):
            self.get_media_id_recent_feed()
            chooser = random.randint(0, len(self.media_on_feed) - 1)
            self.current_user = self.media_on_feed[chooser]["node"]["owner"]["username"]
            self.current_id = self.media_on_feed[chooser]["node"]["owner"]["id"]

            current_user = self.current_user
            current_id = self.current_id

            if self.login_status:
                log_string = f"Getting user info : {current_user}"
                self.write_log(log_string)
            if self.login_status == 1:
                url_tag = self.url_user_detail % (current_user)
                try:
                    r = self.s.get(url_tag)
                    if (
                        r.text.find(
                            "The link you followed may be broken, or the page may have been removed."
                        )
                        != -1
                    ):
                        log_string = (
                            f"Looks like account was deleted, skipping : {current_user}"
                        )
                        self.write_log(log_string)
                        insert_unfollow_count(self, user_id=current_id)
                        time.sleep(3)
                        return False
                    all_data = json.loads(
                        re.search(
                            "window._sharedData = (.*?);</script>", r.text, re.DOTALL
                        ).group(1)
                    )["entry_data"]["ProfilePage"][0]

                    user_info = all_data["graphql"]["user"]
                    i = 0
                    log_string = "Checking user info.."
                    self.write_log(log_string)

                    follows = user_info["edge_follow"]["count"]
                    follower = user_info["edge_followed_by"]["count"]
                    media = user_info["edge_owner_to_timeline_media"]["count"]
                    follow_viewer = user_info["follows_viewer"]
                    followed_by_viewer = user_info["followed_by_viewer"]
                    requested_by_viewer = user_info["requested_by_viewer"]
                    has_requested_viewer = user_info["has_requested_viewer"]
                    log_string = f"Follower : {follower}"
                    self.write_log(log_string)
                    log_string = f"Following : {follows}"
                    self.write_log(log_string)
                    log_string = f"Media : {media}"
                    self.write_log(log_string)
                    if follows == 0 or follower / follows > 2:
                        self.is_selebgram = True
                        self.is_fake_account = False
                        self.write_log("   >This is probably Selebgram account")

                    elif follower == 0 or follows / follower > 2:
                        self.is_fake_account = True
                        self.is_selebgram = False
                        self.write_log("   >This is probably Fake account")
                    else:
                        self.is_selebgram = False
                        self.is_fake_account = False
                        self.write_log("   >This is a normal account")

                    if media > 0 and follows / media < 25 and follower / media < 25:
                        self.is_active_user = True
                        self.write_log("   >This user is active")
                    else:
                        self.is_active_user = False
                        self.write_log("   >This user is passive")

                    if follow_viewer or has_requested_viewer:
                        self.is_follower = True
                        self.write_log("   >This account is following you")
                    else:
                        self.is_follower = False
                        self.write_log("   >This account is NOT following you")

                    if followed_by_viewer or requested_by_viewer:
                        self.is_following = True
                        self.write_log("   >You are following this account")

                    else:
                        self.is_following = False
                        self.write_log("   >You are NOT following this account")

                except:
                    logging.exception("Except on auto_unfollow!")
                    time.sleep(3)
                    return False
            else:
                return False

            if (
                self.is_selebgram is not False
                or self.is_fake_account is not False
                or self.is_active_user is not True
                or self.is_follower is not True
            ):
                self.write_log(current_user)
                self.unfollow(current_id)
                self.next_iteration["Unfollow"] = time.time() + self.add_time(
                    self.unfollow_delay
                )
                # don't insert unfollow count as it is done now inside unfollow()
                # insert_unfollow_count(self, user_id=current_id)
            elif self.is_following is not True:
                # we are not following this account, hence we unfollowed it, let's keep track
                insert_unfollow_count(self, user_id=current_id)
        time.sleep(8)

    def get_media_id_recent_feed(self):
        if self.login_status:
            now_time = datetime.datetime.now()
            log_string = f"{self.user_login} : Get media id on recent feed"
            self.write_log(log_string)
            if self.login_status == 1:
                url_tag = "https://www.instagram.com/"
                try:
                    r = self.s.get(url_tag)

                    jsondata = re.search(
                        "additionalDataLoaded\('feed',({.*})\);", r.text
                    ).group(1)
                    all_data = json.loads(jsondata.strip())

                    self.media_on_feed = list(
                        all_data["user"]["edge_web_feed_timeline"]["edges"]
                    )

                    log_string = f"Media in recent feed = {len(self.media_on_feed)}"
                    self.write_log(log_string)
                except:
                    logging.exception("get_media_id_recent_feed")
                    self.media_on_feed = []
                    time.sleep(20)
                    return 0
            else:
                return 0

    def write_log(self, log_text):
        """ Write log by print() or logger """

        if self.log_mod == 0:
            try:
                now_time = datetime.datetime.now()
                print(f"{now_time.strftime('%d.%m.%Y_%H:%M')} {log_text}")
            except UnicodeEncodeError:
                print("Your text has unicode problem!")
        elif self.log_mod == 1:
            # Create log_file if not exist.
            if self.log_file == 0:
                self.log_file = 1
                now_time = datetime.datetime.now()
                self.log_full_path = "%s%s_%s.log" % (
                    self.log_file_path,
                    self.user_login,
                    now_time.strftime("%d.%m.%Y_%H:%M"),
                )
                formatter = logging.Formatter("%(asctime)s - %(name)s " "- %(message)s")
                self.logger = logging.getLogger(self.user_login)
                self.hdrl = logging.FileHandler(self.log_full_path, mode="w")
                self.hdrl.setFormatter(formatter)
                self.logger.setLevel(level=logging.INFO)
                self.logger.addHandler(self.hdrl)
            # Log to log file.
            try:
                self.logger.info(log_text)
            except UnicodeEncodeError:
                print("Your text has unicode problem!")
