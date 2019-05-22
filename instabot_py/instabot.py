#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import atexit
import datetime
import itertools
import json
import logging
import os
import pickle
import random
import re
import signal
import sys
import time

import instaloader
import requests

from instabot_py.config import config
from instabot_py.persistence.manager import PersistenceManager


class InstaBot:
    """
    Instabot.py version 1.2.4

    """

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

    def __init__(self, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        config.set_many(kwargs)
        login = config.get("login")
        password = config.get("password")
        if login is None or password is None:
            raise Exception("Account details are missing")

        config.set("session_file", f"{login.lower()}.session", default=True)

        self.persistence = PersistenceManager(config.get('database'))
        self.persistence.bot = self
        self.session_file = config.get("session_file")

        self.user_agent = random.sample(config.get("list_of_ua"), 1)[0]

        self.current_version = 1556087528

        self.bot_start = datetime.datetime.now()
        self.bot_start_ts = time.time()
        self.start_at_h = config.get("start_at_h")
        self.start_at_m = config.get("start_at_m")
        self.end_at_h = config.get("end_at_h")
        self.end_at_m = config.get("end_at_m")
        self.unfollow_break_min = config.get("unfollow_break_min")
        self.unfollow_break_max = config.get("unfollow_break_max")
        self.user_blacklist = config.get("user_blacklist")
        self.tag_blacklist = config.get("tag_blacklist")
        self.unfollow_whitelist = config.get("unfollow_whitelist")
        self.comment_list = config.get("comment_list")

        self.instaloader = instaloader.Instaloader()

        # Unfollow Criteria & Options
        self.unfollow_recent_feed = self.str2bool(config.get("unfollow_recent_feed"))
        self.unfollow_not_following = self.str2bool(config.get("unfollow_not_following"))
        self.unfollow_inactive = self.str2bool(config.get("unfollow_inactive"))
        self.unfollow_probably_fake = self.str2bool(config.get("unfollow_probably_fake"))
        self.unfollow_selebgram = self.str2bool(config.get("unfollow_selebgram"))
        self.unfollow_everyone = self.str2bool(config.get("unfollow_everyone"))

        self.time_in_day = 24 * 60 * 60
        # Like
        self.like_per_day = config.get("like_per_day")

        if self.like_per_day > 0:
            self.like_delay = self.time_in_day / self.like_per_day

        # Unlike
        self.time_till_unlike = config.get("time_till_unlike")
        self.unlike_per_day = config.get("unlike_per_day")
        if self.unlike_per_day > 0:
            self.unlike_delay = self.time_in_day / self.unlike_per_day

        # Follow
        self.follow_time = config.get("follow_time")  # Cannot be zero
        self.follow_time_enabled = self.str2bool(config.get("follow_time_enabled"))
        self.follow_per_day = config.get("follow_per_day")
        if self.follow_per_day > 0:
            self.follow_delay = self.time_in_day / self.follow_per_day

        # Unfollow
        self.unfollow_per_day = config.get("unfollow_per_day")
        if self.unfollow_per_day > 0:
            self.unfollow_delay = self.time_in_day / self.unfollow_per_day

        # Comment
        self.comments_per_day = config.get("comments_per_day")
        if self.comments_per_day > 0:
            self.comments_delay = self.time_in_day / self.comments_per_day

        # Don't like if media have more than n likes.
        self.media_max_like = config.get("media_max_like")
        # Don't like if media have less than n likes.
        self.media_min_like = config.get("media_min_like")
        # Don't follow if user have more than n followers.
        self.user_max_follow = config.get("user_max_follow")
        # Don't follow if user have less than n followers.
        self.user_min_follow = config.get("user_min_follow")

        # Auto mod seting:
        # Default list of tag.
        self.tag_list = config.get("tag_list")
        # Get random tag, from tag_list, and like (1 to n) times.
        self.max_like_for_one_tag = config.get("max_like_for_one_tag")
        # log_mod 0 to console, 1 to file
        self.log_mod = config.get("log_mod")
        self.s = requests.Session()
        self.c = requests.Session()
        # if you need proxy make something like this:
        # self.s.proxies = {"https" : "http://proxyip:proxyport"}
        # by @ageorgios
        if config.get("http_proxy") and config.get("https_proxy"):
            proxies = {
                "http": f"http://{config.get('http_proxy')}",
                "https": f"http://{config.get('https_proxy')}"
            }
            self.s.proxies.update(proxies)
            self.c.proxies.update(proxies)

        # All counter.
        self.bot_mode = 0
        self.like_counter = 0
        self.follow_counter = 0
        self.unfollow_counter = 0
        self.comments_counter = 0
        self.current_user = "hajka"
        self.current_index = 0
        self.current_id = "abcds"
        # List of user_id, that bot follow
        self.bot_follow_list = []
        self.user_info_list = []
        self.user_list = []
        self.ex_user_list = []
        self.unwanted_username_list = []
        self.is_checked = False
        self.is_selebgram = False
        self.is_fake_account = False
        self.is_active_user = False
        self.is_following = False
        self.is_follower = False
        self.is_rejected = False
        self.is_self_checking = False
        self.is_by_tag = False
        self.is_follower_number = 0

        self.user_id = 0
        self.login_status = False
        self.by_location = False

        self.user_login = login.lower()
        self.user_password = password
        self.bot_mode = 0
        self.media_by_tag = []
        self.media_on_feed = []
        self.media_by_user = []
        self.current_user_info = ""
        self.current_owner = ""
        self.error_400 = 0
        self.unwanted_username_list = config.get("unwanted_username_list")
        now_time = datetime.datetime.now()
        self.check_for_bot_update()
        log_string = "Instabot v1.2.5/0 started at %s:" % (
            now_time.strftime("%d.%m.%Y %H:%M")
        )
        self.logger.info(log_string)
        self.login()
        self.prog_run = True
        self.next_iteration = {
            "Like": 0,
            "Unlike": 0,
            "Follow": 0,
            "Unfollow": 0,
            "Comments": 0,
            "Populate": 0,
        }

        self.populate_user_blacklist()
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        atexit.register(self.cleanup)
        self.instaload = instaloader.Instaloader()

    def url_user(self, username):
        return self.url_user_detail % username

    def check_for_bot_update(self):
        self.logger.info("Checking for updates...")

        try:
            # CHANGE THIS TO OFFICIAL REPO IF KEPT
            updated_timestamp = self.c.get(self.instabot_repo_update)
            if int(updated_timestamp.text) > self.current_version:
                self.logger.info(
                    "> UPDATE AVAILABLE Please update Instabot 'python3 -m pip install instabot-py --upgrade' "
                )
            else:
                self.logger.info("You are running the latest stable version")
        except Exception as exc:
            self.logger.warning("Could not check for updates")
            self.logger.exception(exc)

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
                self.logger.info(
                    f"Account of user {user} was deleted or link is " "invalid"
                )
            else:
                # prevent exception if user have no media
                id_user = all_data["entry_data"]["ProfilePage"][0]["graphql"]["user"][
                    "id"
                ]
                # Update the user_name with the user_id
                self.user_blacklist[user] = id_user
                self.logger.info(f"Blacklisted user {user} added with ID: {id_user}")
                time.sleep(5 * random.random())

    def login(self):

        successfulLogin = False

        self.s.headers.update(
            {
                "Accept": "*/*",
                "Accept-Language": config.get("accept_language"),
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
            self.logger.info(f"Found session file {self.session_file}")
            successfulLogin = True
            with open(self.session_file, "rb") as i:
                cookies = pickle.load(i)
                self.s.cookies.update(cookies)
        else:
            self.logger.info("Trying to login as {}...".format(self.user_login))
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
                self.logger.info("Request didn't return 200 as status code!")
                self.logger.critical("Here is more info for debugging or creating an issue"
                                     "==============="
                                     "Response Status:{login.status_code}"
                                     "==============="
                                     "Response Content:{login.text}"
                                     "==============="
                                     "Response Header:{login.headers}"
                                     "===============")
                return

            loginResponse = login.json()
            try:
                self.csrftoken = login.cookies["csrftoken"]
                self.s.headers.update({"X-CSRFToken": login.cookies["csrftoken"]})
            except Exception as exc:
                self.logger.warning("Something wrong with login")
                self.logger.debug(login.text)
                self.logger.exception(exc)
            if loginResponse.get("errors"):
                self.logger.error(
                    "Something is wrong with Instagram! Please try again later..."
                )
                for error in loginResponse["errors"]["error"]:
                    self.logger.error(f"Error =>{error}")
                return
            if loginResponse.get("message") == "checkpoint_required":
                try:
                    if "instagram.com" in loginResponse["checkpoint_url"]:
                        challenge_url = loginResponse["checkpoint_url"]
                    else:
                        challenge_url = (
                            f"https://instagram.com{loginResponse['checkpoint_url']}"
                        )
                    self.logger.info(f"Challenge required at {challenge_url}")
                    with self.s as clg:
                        clg.headers.update(
                            {
                                "Accept": "*/*",
                                "Accept-Language": config.get("accept_language"),
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
                            self.logger.info("Entered code is wrong, Try again later!")
                            return
                        self.csrftoken = complete_challenge.cookies["csrftoken"]
                        self.s.headers.update(
                            {"X-CSRFToken": self.csrftoken, "X-Instagram-AJAX": "1"}
                        )
                        successfulLogin = complete_challenge.status_code == 200

                except Exception as err:
                    self.logger.debug(f"Login failed, response: \n\n{login.text} {err}")
                    quit()
            elif loginResponse.get("authenticated") is False:
                self.logger.error("Login error! Check your login data!")
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
                self.logger.info(f"{self.user_login} login success!\n")
                if self.session_file is not None:
                    self.logger.info(
                        f"Saving cookies to session file {self.session_file}"
                    )
                    with open(self.session_file, "wb") as output:
                        pickle.dump(self.s.cookies, output, pickle.HIGHEST_PROTOCOL)
            else:
                self.login_status = False
                self.logger.error("Login error! Check your login data!")
                if self.session_file is not None and os.path.isfile(self.session_file):
                    try:
                        os.remove(self.session_file)
                    except:
                        self.logger.info(
                            "Could not delete session file. Please delete manually"
                        )

                self.prog_run = False
        else:
            self.logger.error("Login error! Connection error!")

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
        self.logger.info(log_string)
        work_time = datetime.datetime.now() - self.bot_start
        self.logger.info(f"Bot work time: {work_time}")

        try:
            logout_post = {"csrfmiddlewaretoken": self.csrftoken}
            logout = self.s.post(self.url_logout, data=logout_post)
            self.logger.info("Logout success!")
            self.login_status = False
        except:
            logging.exception("Logout error!")

    def cleanup(self, *_):

        if self.login_status and self.session_file is None:
            self.logout()
        self.prog_run = False

    def get_media_id_by_tag(self, tag):
        """ Get media ID set, by your hashtag or location """

        if self.login_status:
            if tag.startswith("l:"):
                tag = tag.replace("l:", "")
                self.by_location = True
                self.logger.info(f"Get Media by location: {tag}")
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
                    except Exception as exc:
                        self.media_by_tag = []
                        self.logger.warning("Except on get_media!")
                        self.logger.exception(exc)
                else:
                    return 0

            else:
                self.by_location = False
                self.logger.debug(f"Get Media by tag: {tag}")
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
                        self.logger.warning("Except on get_media!")
                        self.logger.exception("get_media_id_by_tag")
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
                                    self.logger.debug(
                                        f"Not liking media owned by blacklisted user: {blacklisted_user_name}"
                                    )
                                    return False
                            if (
                                    self.media_by_tag[i]["node"]["owner"]["id"]
                                    == self.user_id
                            ):
                                self.logger.debug("Keep calm - It's your own media ;)")
                                return False

                            if (
                                    self.persistence.check_already_liked(
                                        media_id=self.media_by_tag[i]["node"]["id"]
                                    )
                            ):
                                self.logger.info("Keep calm - It's already liked ;)")
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
                                        self.logger.debug(
                                            f"Not liking media with blacklisted tag(s): {matching_tags}"
                                        )
                                        return False
                            except Exception as exc:
                                self.logger.warning("Except on like_all_exist_media")
                                self.logger.exception(exc)
                                return False

                            self.logger.debug(
                                "Trying to like media: %s, %s"
                                % (
                                    self.media_by_tag[i]["node"]["id"],
                                    self.url_media
                                    % self.media_by_tag[i]["node"]["shortcode"],
                                )
                            )
                            like = self.like(self.media_by_tag[i]["node"]["id"])
                            # comment = self.comment(self.media_by_tag[i]['id'], 'Cool!')
                            # follow = self.follow(self.media_by_tag[i]["owner"]["id"])
                            if like != 0:
                                if like.status_code == 200:
                                    # Like, all ok!
                                    self.error_400 = 0
                                    self.like_counter += 1
                                    log_string = f"Liked: {self.media_by_tag[i]['node']['id']}. Like #{self.like_counter} {self.url_media % self.media_by_tag[i]['node']['shortcode']}."

                                    self.persistence.insert_media(

                                        media_id=self.media_by_tag[i]["node"]["id"],
                                        status="200",
                                    )
                                    self.logger.info(log_string)
                                elif like.status_code == 400:
                                    self.logger.info(
                                        f"Not liked: {like.status_code} message {like.text}"
                                    )
                                    self.persistence.insert_media(

                                        media_id=self.media_by_tag[i]["node"]["id"],
                                        status="400",
                                    )
                                    # Some error. If repeated - can be ban!
                                    if self.error_400 >= config.get("error_400_to_ban"):
                                        # Look like you banned!
                                        time.sleep(config.get("ban_sleep_time"))
                                    else:
                                        self.error_400 += 1
                                else:
                                    self.persistence.insert_media(

                                        media_id=self.media_by_tag[i]["node"]["id"],
                                        status=str(like.status_code),
                                    )
                                    self.logger.debug(
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
                self.logger.debug("No media to like!")

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
                    self.logger.info(log_string)
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
                    log_string = f"Followed: {self.url_user(username)} #{self.follow_counter}."
                    self.logger.info(log_string)
                    self.persistence.insert_username(user_id=user_id, username=username)
                return follow
            except:
                logging.exception("Except on follow!")
        return False

    def unfollow(self, user_id, username=""):
        """ Send http request to unfollow """
        if self.login_status:
            url_unfollow = self.url_unfollow % (user_id)
            try:
                unfollow = self.s.post(url_unfollow)
                if unfollow.status_code == 200:
                    self.unfollow_counter += 1
                    log_string = f"Unfollowed: {self.url_user(username)} #{self.unfollow_counter}."
                    self.logger.info(log_string)
                    self.persistence.insert_unfollow_count(user_id=user_id)
                return unfollow
            except:
                logging.exception("Exept on unfollow!")
        return False

    # Backwards Compatibility for old example.py files
    def auto_mod(self):
        self.mainloop()

    def new_auto_mod(self):
        self.mainloop()

    def mainloop(self):
        while self.prog_run and self.login_status:
            now = datetime.datetime.now()
            # distance between start time and now
            dns = self.time_dist(datetime.time(self.start_at_h,
                                               self.start_at_m),
                                 now.time())
            # distance between end time and now
            dne = self.time_dist(datetime.time(self.end_at_h,
                                               self.end_at_m),
                                 now.time())
            if (dns == 0 or dne < dns) and dne != 0:
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
                self.logger.debug("Tic!")
            else:
                self.logger.debug(
                    "Sleeping until {hour}:{min}".format(
                        hour=self.start_at_h, min=self.start_at_m
                    )
                )
                time.sleep(100)
        self.logger.info("Exit Program... GoodBye")
        sys.exit(0)

    def remove_already_liked(self):
        # This logstring has caused TOO many questions, it serves no good telling them
        # duplicates are removed -- this is expected behaviour after all
        # self.logger.info("Removing already liked medias..")
        x = 0
        while x < len(self.media_by_tag):
            if (
                    self.persistence.check_already_liked(media_id=self.media_by_tag[x]["node"]["id"])

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
            self.logger.debug("Could not remove media")

    def new_auto_mod_unlike(self):
        if time.time() > self.next_iteration["Unlike"] and self.unlike_per_day != 0:
            media = self.persistence.get_medias_to_unlike()
            if media:
                self.logger.debug("Trying to unlike media")
                self.auto_unlike()
                self.next_iteration["Unlike"] = time.time() + self.add_time(
                    self.unlike_per_day
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
                self.logger.debug("Keep calm - It's your own profile ;)")
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
                        self.logger.info(
                            f"Won't follow {username}: does not meet user_min_follow requirement"
                        )
                        return

                    if self.user_max_follow != 0 and followers > self.user_max_follow:
                        self.logger.info(
                            f"Won't follow {username}: does not meet user_max_follow requirement"
                        )
                        return

                except Exception:
                    pass
            if (
                    self.persistence.check_already_followed(
                        user_id=self.media_by_tag[0]["node"]["owner"]["id"]
                    )
            ):
                self.logger.debug(
                    f"Already followed before {self.media_by_tag[0]['node']['owner']['id']}"
                )
                self.next_iteration["Follow"] = time.time() + self.add_time(
                    self.follow_delay / 2
                )
                return

            log_string = (
                f"Trying to follow: {self.media_by_tag[0]['node']['owner']['id']}"
            )
            self.logger.debug(log_string)
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
                # print(self.persistence.check_if_userid_exists( userid=feed_user_id))
                if not self.persistence.check_if_userid_exists(userid=feed_user_id):
                    self.persistence.insert_username(user_id=feed_user_id, username=feed_username)
                    self.logger.debug(f"Inserted user {feed_username} from recent feed")
        except Exception as exc:
            self.logger.warning("Notice: could not populate from recent feed")
            self.logger.exception(exc)

    def new_auto_mod_unfollow(self):
        if time.time() > self.next_iteration["Unfollow"] and self.unfollow_per_day != 0:

            if (time.time() - self.bot_start_ts) < 30:
                # let bot initialize
                return
            if self.persistence.get_username_row_count() < 20:
                self.logger.debug(
                    f"> Waiting for database to populate before unfollowing (progress {str(self.persistence.get_username_row_count())} /20)"
                )

                if self.unfollow_recent_feed is True:
                    self.logger.debug("Will try to populate using recent feed")
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
                except Exception as exc:
                    self.logger.warning(
                        "Notice: Could not populate from recent feed right now"
                    )
                    self.logger.exception(exc)

                log_string = f"Trying to unfollow #{self.unfollow_counter + 1}:"
                self.logger.debug(log_string)
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
            if "@username@" in comment_text:
                comment_text = comment_text.replace("@username@", self.current_owner)

            media_id = self.media_by_tag[0]["node"]["id"]
            log_string = f"Trying to comment: {media_id}\n                 " \
                         f"https://www.{self.get_instagram_url_from_media_id(media_id)}"
            self.logger.info(log_string)

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
                    self.logger.warning(
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

                self.current_owner = all_data["graphql"]["shortcode_media"]["owner"][
                    "username"
                ]

                if (
                        all_data["graphql"]["shortcode_media"]["owner"]["id"]
                        == self.user_id
                ):
                    self.logger.debug("Keep calm - It's your own media ;)")
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
                        self.logger.debug("Keep calm - Media already commented ;)")
                        # Del media to don't loop on it
                        del self.media_by_tag[0]
                        return True
                return False
            elif check_comment.status_code == 404:
                self.persistence.insert_media(

                    self.media_by_tag[0]["node"]["id"],
                    str(check_comment.status_code),
                )
                self.logger.warning(
                    f"Tried to comment {media_code} but it doesn't exist (404). Resuming..."
                )
                del self.media_by_tag[0]
                return True
            else:
                self.persistence.insert_media(

                    self.media_by_tag[0]["node"]["id"],
                    str(check_comment.status_code),
                )
                self.media_by_tag.remove(self.media_by_tag[0])
                return True
        except Exception as exc:
            self.logger.warning(f"Couldn't comment post, resuming. {url_check}")
            self.logger.exception(exc)
            del self.media_by_tag[0]
            return True

    def auto_unlike(self):
        checking = True
        while checking:
            media_to_unlike = self.persistence.get_medias_to_unlike()
            if media_to_unlike:
                request = self.unlike(media_to_unlike)
                if request.status_code == 200:
                    self.persistence.update_media_complete(media_to_unlike)
                else:
                    self.logger.critical("Couldn't unlike media, resuming.")
                    checking = False
            else:
                self.logger.debug("no medias to unlike")
                checking = False

    def auto_unfollow(self):
        checking = True
        while checking:
            follower = self.persistence.get_username_to_unfollow_random()
            if not follower:
                self.logger.debug("Looks like there is nobody to unfollow.")
                return False
            current_id = follower.id
            current_user = follower.username
            if not current_user:
                current_user = self.get_username_by_user_id(user_id=current_id)
            if not current_user:
                log_string = "api limit reached from instagram. Will try later"
                self.logger.warning(log_string)
                return False
            if current_user in self.unfollow_whitelist:
                log_string = "found whitelist user, not unfollowing"
                # problem, if just one user in unfollowlist -> might create inf. loop. therefore just skip round
                self.logger.debug(log_string)
                return False
            else:
                checking = False

        if self.login_status:
            log_string = f"Getting user info : {current_user}"
            self.logger.debug(log_string)
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
                        self.logger.debug(log_string)
                        self.persistence.insert_unfollow_count(user_id=current_id)
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
                    self.logger.debug(log_string)

                    follows = user_info["edge_follow"]["count"]
                    follower = user_info["edge_followed_by"]["count"]
                    media = user_info["edge_owner_to_timeline_media"]["count"]
                    follow_viewer = user_info["follows_viewer"]
                    followed_by_viewer = user_info["followed_by_viewer"]
                    requested_by_viewer = user_info["requested_by_viewer"]
                    has_requested_viewer = user_info["has_requested_viewer"]
                    log_string = f"Follower : {follower}"
                    self.logger.debug(log_string)
                    log_string = f"Following : {follows}"
                    self.logger.debug(log_string)
                    log_string = f"Media : {media}"
                    self.logger.debug(log_string)
                    self.is_selebgram = False
                    self.is_fake_account = False
                    self.is_active_user = True
                    self.is_follower = True
                    if follows == 0 or follower / follows > 2:
                        if self.unfollow_selebgram is True:
                            self.is_selebgram = True
                            self.is_fake_account = False
                            self.logger.debug("   >This is probably Selebgram account")

                    elif follower == 0 or follows / follower > 2:
                        if self.unfollow_probably_fake is True:
                            self.is_fake_account = True
                            self.is_selebgram = False
                            self.logger.debug("   >This is probably Fake account")
                    else:
                        self.is_selebgram = False
                        self.is_fake_account = False
                        self.logger.debug("   >This is a normal account")

                    if media > 0 and follows / media < 25 and follower / media < 25:
                        self.is_active_user = True
                        self.logger.debug("   >This user is active")
                    else:
                        if self.unfollow_inactive is True:
                            self.is_active_user = False
                            self.logger.debug("   >This user is passive")

                    if follow_viewer or has_requested_viewer:
                        self.is_follower = True
                        self.logger.debug("   >This account is following you")
                    else:
                        if self.unfollow_not_following is True:
                            self.is_follower = False
                            self.logger.debug("   >This account is NOT following you")

                    if followed_by_viewer or requested_by_viewer:
                        self.is_following = True
                        self.logger.debug("   >You are following this account")

                    else:
                        self.is_following = False
                        self.logger.debug("   >You are NOT following this account")

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
                self.unfollow(current_id, current_user)
                # don't insert unfollow count as it is done now inside unfollow()
                # self.persistence.insert_unfollow_count( user_id=current_id)
            elif self.unfollow_everyone is True:
                self.logger.debug(f"current_user :{current_user}")
                self.unfollow(current_id, current_user)
            elif self.is_following is not True:
                # we are not following this account, hence we unfollowed it, let's keep track
                self.persistence.insert_unfollow_count(user_id=current_id)

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
                self.logger.debug(log_string)
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
                        self.logger.debug(log_string)
                        self.persistence.insert_unfollow_count(user_id=current_id)
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
                    self.logger.debug(log_string)

                    follows = user_info["edge_follow"]["count"]
                    follower = user_info["edge_followed_by"]["count"]
                    media = user_info["edge_owner_to_timeline_media"]["count"]
                    follow_viewer = user_info["follows_viewer"]
                    followed_by_viewer = user_info["followed_by_viewer"]
                    requested_by_viewer = user_info["requested_by_viewer"]
                    has_requested_viewer = user_info["has_requested_viewer"]
                    log_string = f"Follower : {follower}"
                    self.logger.debug(log_string)
                    log_string = f"Following : {follows}"
                    self.logger.debug(log_string)
                    log_string = f"Media : {media}"
                    self.logger.debug(log_string)
                    if follows == 0 or follower / follows > 2:
                        self.is_selebgram = True
                        self.is_fake_account = False
                        self.logger.debug("   >This is probably Selebgram account")

                    elif follower == 0 or follows / follower > 2:
                        self.is_fake_account = True
                        self.is_selebgram = False
                        self.logger.debug("   >This is probably Fake account")
                    else:
                        self.is_selebgram = False
                        self.is_fake_account = False
                        self.logger.debug("   >This is a normal account")

                    if media > 0 and follows / media < 25 and follower / media < 25:
                        self.is_active_user = True
                        self.logger.debug("   >This user is active")
                    else:
                        self.is_active_user = False
                        self.logger.debug("   >This user is passive")

                    if follow_viewer or has_requested_viewer:
                        self.is_follower = True
                        self.logger.debug("   >This account is following you")
                    else:
                        self.is_follower = False
                        self.logger.debug("   >This account is NOT following you")

                    if followed_by_viewer or requested_by_viewer:
                        self.is_following = True
                        self.logger.debug("   >You are following this account")

                    else:
                        self.is_following = False
                        self.logger.debug("   >You are NOT following this account")

                except Exception as exc:
                    self.logger.warning("Except on auto_unfollow!")
                    self.logger.exception(exc)
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
                self.logger.debug(f"current_user: {current_user}")
                self.unfollow(current_id, current_user)
                self.next_iteration["Unfollow"] = time.time() + self.add_time(
                    self.unfollow_delay
                )
                # don't insert unfollow count as it is done now inside unfollow()
                # self.persistence.insert_unfollow_count( user_id=current_id)
            elif self.is_following is not True:
                # we are not following this account, hence we unfollowed it, let's keep track
                self.persistence.insert_unfollow_count(user_id=current_id)
        time.sleep(8)

    def get_media_id_recent_feed(self):
        if self.login_status:
            now_time = datetime.datetime.now()
            log_string = f"{self.user_login} : Get media id on recent feed"
            self.logger.debug(log_string)
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
                    self.logger.debug(log_string)
                except:
                    logging.exception("get_media_id_recent_feed")
                    self.media_on_feed = []
                    time.sleep(20)
                    return 0
            else:
                return 0

    @staticmethod
    def time_dist(to_time, from_time):
        """
        Method to compare time.
        In terms of minutes result is
        from_time + result == to_time
        Args:
            to_time: datetime.time() object.
            from_time: datetime.time() object.
        Returns: int
            how much minutes between from_time and to_time
            if to_time < from_time then it means that
                to_time is on the next day.
        """
        to_t = to_time.hour * 60 + to_time.minute
        from_t = from_time.hour * 60 + from_time.minute
        midnight_t = 24 * 60
        return (midnight_t - from_t) + to_t if to_t < from_t else to_t - from_t

    @staticmethod
    def str2bool(value):
        return str(value).lower() in ["yes", "true"]
