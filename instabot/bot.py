#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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
import time

import instaloader
import requests
from config42 import ConfigManager

import instabot
from instabot.default_config import DEFAULT_CONFIG
from instabot.persistence.manager import PersistenceManager


class CredsMissing(Exception):
    """ Raised when the Instagram credentials are missing"""
    message = "Instagram credentials are missing."

    def __str__(self):
        return CredsMissing.message


class InstaBot:
    """
    Instabot.py

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

    def __init__(self, config=None, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        if not config:
            self.config = ConfigManager(defaults=DEFAULT_CONFIG)
            self.config.set_many(kwargs)
        else:
            self.config = config

        login = self.config.get("login")
        password = self.config.get("password")
        if login is None or password is None:
            raise CredsMissing()

        self.persistence = PersistenceManager(self.config.get("database"))
        self.persistence.bot = self
        self.session_file = self.config.get("session_file")

        self.user_agent = random.sample(self.config.get("list_of_ua"), 1)[0]
        self.bot_start = datetime.datetime.now()
        self.bot_start_ts = time.time()
        self.start_at_h = self.config.get("start_at_h")
        self.start_at_m = self.config.get("start_at_m")
        self.end_at_h = self.config.get("end_at_h")
        self.end_at_m = self.config.get("end_at_m")
        self.window_check_every = self.config.get("window_check_every")
        self.unfollow_break_min = self.config.get("unfollow_break_min")
        self.unfollow_break_max = self.config.get("unfollow_break_max")
        self.user_blacklist = self.config.get("user_blacklist")
        self.tag_blacklist = self.config.get("tag_blacklist")
        self.unfollow_whitelist = self.config.get("unfollow_whitelist")
        self.comment_list = self.config.get("comment_list")

        self.instaloader = instaloader.Instaloader()

        # Unfollow Criteria & Options
        self.unfollow_recent_feed = self.str2bool(self.config.get("unfollow_recent_feed"))
        self.unfollow_not_following = self.str2bool(
            self.config.get("unfollow_not_following")
        )
        self.unfollow_inactive = self.str2bool(self.config.get("unfollow_inactive"))
        self.unfollow_probably_fake = self.str2bool(
            self.config.get("unfollow_probably_fake")
        )
        self.unfollow_selebgram = self.str2bool(self.config.get("unfollow_selebgram"))
        self.unfollow_everyone = self.str2bool(self.config.get("unfollow_everyone"))

        self.time_in_day = ((self.end_at_h - self.start_at_h) % 24 * 60 * 60) + (
                (self.end_at_m - self.start_at_m) % 60 * 60)

        # Like
        self.like_per_run = int(self.config.get("like_per_run"))

        if self.like_per_run > 0:
            self.like_delay = self.time_in_day / self.like_per_run

        # Unlike
        self.time_till_unlike = self.config.get("time_till_unlike")
        self.unlike_per_run = int(self.config.get("unlike_per_run"))
        if self.unlike_per_run > 0:
            self.unlike_delay = self.time_in_day / self.unlike_per_run

        # Follow
        self.follow_time = self.config.get("follow_time")
        self.follow_per_run = int(self.config.get("follow_per_run"))
        self.follow_delay = self.config.get("follow_delay")
        if self.follow_per_run > 0 and not self.follow_delay:
            self.follow_delay = self.time_in_day / self.follow_per_run

        # Unfollow
        self.unfollow_per_run = int(self.config.get("unfollow_per_run"))
        self.unfollow_delay = self.config.get("unfollow_delay")
        if self.unfollow_per_run > 0 and not self.unfollow_delay:
            self.unfollow_delay = self.time_in_day / self.unfollow_per_run

        # Comment
        self.comments_per_run = int(self.config.get("comments_per_run"))
        self.comments_delay = self.config.get("comments_delay")
        if self.comments_per_run > 0 and not self.comments_delay:
            self.comments_delay = self.time_in_day / self.comments_per_run

        # Don't like if media have more than n likes.
        self.media_max_like = self.config.get("media_max_like")
        # Don't like if media have less than n likes.
        self.media_min_like = self.config.get("media_min_like")
        # Don't follow if user have more than n followers.
        self.user_max_follow = self.config.get("user_max_follow")
        # Don't follow if user have less than n followers.
        self.user_min_follow = self.config.get("user_min_follow")

        # Auto mod seting:
        # Default list of tag.
        self.tag_list = self.config.get("tag_list")
        # Default keywords.
        self.keywords = self.config.get("keywords")
        # Get random tag, from tag_list, and like (1 to n) times.
        self.max_like_for_one_tag = self.config.get("max_like_for_one_tag")
        # log_mod 0 to console, 1 to file
        self.log_mod = self.config.get("log_mod")

        self.s = requests.Session()
        self.c = requests.Session()

        self.proxies = self.config.get('proxies')
        if self.proxies:
            self.logger.debug(f"using proxy configuration {self.proxies}")
            self.s.proxies.update(self.proxies)
            self.c.proxies.update(self.proxies)

        # All counters.
        self.like_counter = 0
        self.unlike_counter = 0
        self.follow_counter = 0
        self.unfollow_counter = 0
        self.comments_counter = 0

        self.user_id = 0
        self.login_status = False
        self.user_login = login.lower()
        self.user_password = password
        self.unfollow_from_feed = False
        self.medias = []

        self.media_on_feed = []
        self.media_by_user = []
        self.current_owner = ""
        self.error_400 = 0
        self.error_400_to_ban = self.config.get("error_400_to_ban")
        self.ban_sleep_time = self.config.get("ban_sleep_time")
        self.unwanted_username_list = self.config.get("unwanted_username_list")
        now_time = datetime.datetime.now()
        self.logger.info(
            "Instabot v{} started at {}:".format(instabot.__version__, now_time.strftime("%d.%m.%Y %H:%M")))
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
        self.login()
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        atexit.register(self.cleanup)

    def url_user(self, username):
        return self.url_user_detail % username

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
                "Accept-Language": self.config.get("accept_language"),
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

        if self.session_file and os.path.isfile(self.session_file):
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
            if login.status_code not in (200, 400):
                # Handling Other Status Codes and making debug easier!!
                self.logger.debug("Login Request didn't return 200 as status code!")
                self.logger.debug(
                    "Here is more info for debugging or creating an issue"
                    "==============="
                    "Response Status:{login.status_code}"
                    "==============="
                    "Response Content:{login.text}"
                    "==============="
                    "Response Header:{login.headers}"
                    "==============="
                )
                return
            else:
                self.logger.debug("Login request succeeded ")

            loginResponse = login.json()
            try:
                self.csrftoken = login.cookies["csrftoken"]
                self.s.headers.update({"X-CSRFToken": self.csrftoken})
            except Exception as exc:
                self.logger.warning("Something wrong with login")
                self.logger.debug(login.text)
                self.logger.exception(exc)
            if loginResponse.get("errors"):
                self.logger.error(
                    "Something is wrong with Instagram! Please try again later..."
                )
                self.logger.error(loginResponse["errors"]["error"])

            elif loginResponse.get("message") == "checkpoint_required":
                try:
                    if "instagram.com" in loginResponse["checkpoint_url"]:
                        challenge_url = loginResponse["checkpoint_url"]
                    else:
                        challenge_url = f"https://instagram.com{loginResponse['checkpoint_url']}"
                    self.logger.info(f"Challenge required at {challenge_url}")
                    with self.s as clg:
                        clg.headers.update(
                            {
                                "Accept": "*/*",
                                "Accept-Language": self.config.get("accept_language"),
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
                    return False
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
                if self.session_file and os.path.isfile(self.session_file):
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
                "Logout: likes - %i, Unlikes -%i, Follows - %i, Unfollows - %i, Comments - %i."
                % (
                    self.like_counter,
                    self.unlike_counter,
                    self.follow_counter,
                    self.unfollow_counter,
                    self.comments_counter,
                )
        )
        self.logger.info(log_string)
        work_time = now_time - self.bot_start
        self.logger.info(f"Bot work time: {work_time}")

        try:
            _ = self.s.post(self.url_logout, data={"csrfmiddlewaretoken": self.csrftoken})
            self.logger.info("Logout success!")
            self.login_status = False
        except Exception as exc:
            logging.error("Logout error!")
            logging.exception("exc")

    def cleanup(self, *_):

        if self.login_status and self.session_file is None:
            self.logout()
        self.prog_run = False

    def get_media_id_by_tag(self, tag):
        """ Get media ID set, by your hashtag or location """
        medias = None
        if tag.startswith("l:"):
            tag = tag.replace("l:", "")
            self.logger.info(f"Get Media by location: {tag}")
            url_location = self.url_location % (tag)
            r = self.s.get(url_location)
            try:
                all_data = json.loads(r.text)
                medias = list(
                    all_data["graphql"]["location"]["edge_location_to_media"]["edges"]
                )
            except Exception as exc:

                self.logger.exception(exc)
        else:
            self.logger.debug(f"Get Media by tag: {tag}")
            url_tag = self.url_tag % (tag)
            r = self.s.get(url_tag)
            try:
                all_data = json.loads(r.text)
                medias = list(
                    all_data["graphql"]["hashtag"]["edge_hashtag_to_media"]["edges"]
                )
            except Exception as exc:
                self.logger.exception(exc)

        return medias

    def get_media_url(self, media_id=None, shortcode=None):
        """ Get Media Code or Full Url from Media ID """
        if shortcode:
            return self.url_media % shortcode
        elif media_id:
            media_id = int(media_id)
            alphabet = (
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
            )
            shortened_id = ""
            while media_id > 0:
                media_id, idx = divmod(media_id, 64)
                shortened_id = alphabet[idx] + shortened_id

            return self.url_media % shortened_id

    def get_username_by_user_id(self, user_id):
        try:
            profile = instaloader.Profile.from_id(self.instaloader.context, user_id)
            return profile.username
        except Exception as exc:
            logging.exception(exc)

    def media_contains_blacklisted_tag(self, media):
        try:
            if len(media["node"]["edge_media_to_caption"]["edges"]) > 1:
                caption = media["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"].encode(
                    "ascii", errors="ignore")

                tag_blacklist = set(self.tag_blacklist)
                tags = {tag.decode("ASCII").strip("#").lower()
                        for tag in caption.split()
                        if (tag.decode("ASCII")).startswith("#")}
                matching_tags = tags.intersection(tag_blacklist)
                if matching_tags:
                    self.logger.debug("Media ignored tag(s): {}".format(", ".join(matching_tags)))
                    return True
        except Exception as exc:
            self.logger.warning("Except on media_contains_blacklisted_tag")
            self.logger.exception(exc)

    def verify_media_misc(self, media):
        if media["node"]["owner"]["id"] == self.user_id:
            self.logger.debug("Keep calm - It's your own media ;)")
            return True

        if self.persistence.check_already_liked(media_id=media["node"]["id"]):
            self.logger.info("Keep calm - It's already liked ;)")
            return True

    def verify_media_owner_blacklisted(self, media):

        for username, userid, in self.user_blacklist.items():
            if media["node"]["owner"]["id"] == userid:
                self.logger.debug(
                    f"Media owned by blacklisted user: {username}"
                )
                return True

    def verify_media_number_of_likes(self, media):
        like_count = media["node"]["edge_liked_by"]["count"]
        return (like_count <= self.media_max_like and like_count >= self.media_min_like) \
               or (self.media_max_like == 0 and like_count >= self.media_min_like) \
               or (self.media_min_like == 0 and like_count <= self.media_max_like) \
               or (self.media_min_like == 0 and self.media_max_like == 0)

    def verify_media(self, media):
        return not self.verify_media_misc(media) \
               and not self.media_contains_blacklisted_tag(media) \
               and not self.verify_media_number_of_likes(media) \
               and not self.verify_media_owner_blacklisted(media)

    def like(self, media_id):
        """ Send http request to like media by ID """
        media_to_like_url = self.get_media_url(media_id)

        try:
            self.logger.debug(f"Trying to like media: id: {media_id}, url: {media_to_like_url}")
            resp = self.s.post(self.url_likes % (media_id))
        except Exception as exc:
            logging.exception(exc)
            return False

        if resp.status_code == 200:
            # Like is successful, all is ok!
            self.error_400 = 0
            self.like_counter += 1
            self.persistence.insert_media(media_id=media_id, status="200")
            self.logger.info(f"Liked media #{self.like_counter}: id: {media_id}, " \
                             f"url: {media_to_like_url}")
            return True
        elif resp.status_code == 400:
            self.logger.info(f"Could not like media: id: {media_id}, "
                             f"url: {media_to_like_url}. Reason: {resp.text}")
            self.persistence.insert_media(media_id=media_id, status="400", )

        else:
            self.persistence.insert_media(
                media_id=media_id,
                status=str(resp.status_code),
            )
            self.logger.debug(f"Could not like media: id: {media_id}, "
                              f"url: {media_to_like_url}, status code: {resp.status_code}. "
                              f"Reason: {resp.text}")

        return False

    def unlike(self, media_id):
        """ Send http request to unlike media by ID """
        url_unlike = self.url_unlike % (media_id)
        try:
            resp = self.s.post(url_unlike)
        except Exception as exc:
            logging.exception(exc)
            return None

        if resp.status_code == 200:
            self.persistence.update_media_complete(media_id)
            self.unlike_counter += 1
            self.logger.info(
                f"Media Unliked: # {self.unlike_counter} id: {media_id}, url: {self.get_media_url(media_id)}")
            return True
        elif resp.status_code == 400 and resp.text == 'missing media':
            self.persistence.update_media_complete(media_id)
            self.logger.info(
                f"Could not unlike media: id: {media_id}, url: {self.get_media_url(media_id)}. It seems "
                f"this media is no longer exist.")
        else:
            self.logger.critical(f"Could not unlike media: id: {media_id}, url: {self.get_media_url(media_id)}. "
                                 f"Status code : {resp.status_code} Reason: {resp.text}")

        return False

    def comment(self, media_id, comment_text):
        """ Send http request to comment """
        self.logger.info(f"Trying to comment: {media_id} {self.get_media_url(media_id)}")
        url_comment = self.url_comment % (media_id)
        try:
            resp = self.s.post(url_comment, data={"comment_text": comment_text})
        except Exception as exc:
            logging.exception(exc)
            return False

        if resp.status_code == 200:
            self.comments_counter += 1
            self.logger.info(f"Comment: {comment_text}. #{self.comments_counter}.")
            return True

    def follow(self, user_id, username=None):
        """ Send http request to follow """
        if self.login_status:
            url_follow = self.url_follow % user_id
            if username is None:
                username = self.get_username_by_user_id(user_id=user_id)
            try:
                resp = self.s.post(url_follow)
                if resp.status_code == 200:
                    self.follow_counter += 1
                    self.logger.info(f"Followed: {self.url_user(username)} #{self.follow_counter}.")
                    self.persistence.insert_username(user_id=user_id, username=username)
                return resp
            except:
                logging.exception("Except on follow!")
        return False

    def unfollow(self, user_id, username=""):
        """ Send http request to unfollow """
        try:
            resp = self.s.post(self.url_unfollow % (user_id))
        except Exception as exc:
            logging.critical("Error while requesting the unfollow endpoint")
            logging.exception(exc)
            return False

        if resp.status_code == 200:
            self.unfollow_counter += 1
            self.logger.info(f"Unfollowed: {self.url_user(username)} #{self.unfollow_counter}.")
            self.persistence.insert_unfollow_count(user_id=user_id)
            return True
        else:
            return False

    def run_during_time_window(self):
        # TODO this method is subject of deprecation

        now = datetime.datetime.now()
        # distance between start time and now
        dns = self.time_dist(
            datetime.time(self.start_at_h, self.start_at_m), now.time()
        )
        # distance between end time and now
        dne = self.time_dist(
            datetime.time(self.end_at_h, self.end_at_m), now.time()
        )
        if not ((dns == 0 or dne < dns) and dne != 0):
            self.logger.info(f"Pause for {self.ban_sleep_time} seconds")
            time.sleep(self.window_check_every)
            return False
        else:
            return True

    def loop_controller(self):
        # 400 errors,
        if self.error_400 >= self.error_400_to_ban:
            self.logger.info(f"Bot receives {self.error_400} HTTP_400_Error(s), You're maybe banned! ")
            self.logger.info(f"Pause for {self.ban_sleep_time} seconds")
            time.sleep(self.generate_time(self.ban_sleep_time))
            self.error_400 = 0

        # exceed counters, program halt
        if self.like_counter > self.like_per_run \
                and self.follow_counter > self.follow_per_run \
                and self.unfollow_counter > self.unfollow_per_run \
                and self.comments_counter > self.comments_per_run:
            self.prog_run = False

        if self.iteration_ready("follow") or self.iteration_ready("unfollow") \
                or self.iteration_ready("unlike") or self.iteration_ready("like") \
                or self.iteration_ready("comments"):
            return True
        else:
            time.sleep(1)
            return False

    def run(self):
        medias = []
        while self.prog_run and self.login_status:
            if not self.run_during_time_window():
                continue
            if not self.loop_controller():
                continue

            if len(medias) == 0:
                tag = random.choice(self.tag_list)
                medias_raw = self.get_media_id_by_tag(tag)
                self.logger.debug(f"Retrieved {len(medias_raw)} medias")
                max_tag_like_count = random.randint(1, self.max_like_for_one_tag)
                medias = self.remove_already_liked_medias(medias_raw)[:max_tag_like_count]
                self.logger.debug(
                    f"Select {max_tag_like_count} medias to process. Increase max_like_for_one_tag value for more processing medias ")
                continue

            media = medias.pop()
            self.new_auto_mod_like(media)
            self.new_auto_mod_unlike()
            self.new_auto_mod_follow(media)
            self.new_auto_mod_unfollow()
            self.new_auto_mod_comments(media)

        self.logger.info("Exit from loop GoodBye")

    def remove_already_liked_medias(self, medias):
        return [media for media in medias if
                not self.persistence.check_already_liked(media_id=media["node"]["id"])]

    def new_auto_mod_like(self, media):
        if self.iteration_ready("like") and media:
            self.init_next_interation("like")
            media_id = media['node']['id']
            if self.like(media_id):
                return True

    def new_auto_mod_unlike(self):
        if self.iteration_ready("unlike"):
            self.init_next_interation("unlike")
            media_id = self.persistence.get_medias_to_unlike()
            if media_id:
                self.logger.debug("Trying to unlike media")
                if self.unlike(media_id):
                    return True
            else:
                self.logger.debug("Nothing to unlike")

    def get_followers_count(self, username):
        try:
            resp = self.s.get(self.url_user_detail % (username))
            all_data = json.loads(
                re.search(
                    "window._sharedData = (.*?);</script>", resp.text, re.DOTALL
                ).group(1)
            )
            followers_count = all_data["entry_data"]["ProfilePage"][0]["graphql"][
                "user"
            ]["edge_followed_by"]["count"]
        except Exception as exc:
            self.logger.exception(exc)
            followers_count = 0
        return followers_count

    def verify_account_name(self, username):
        if not (self.keywords and len(self.keywords) > 0):
            return True

        for keyword in self.keywords:
            if username.find(keyword) >= 0:
                return True

        try:
            url = self.url_user_detail % (username)
            r = self.s.get(url)
            all_data = json.loads(
                re.search(
                    "window._sharedData = (.*?);</script>",
                    r.text,
                    re.DOTALL,
                ).group(1)
            )
            biography = all_data["entry_data"]["ProfilePage"][0][
                "graphql"
            ]["user"]["biography"]

            if biography:
                for keyword in self.keywords:
                    if biography.find(keyword) >= 0:
                        return True
        except Exception as exc:
            self.logger.debug(f"Cannot retrieve user:{username}'s biography")
            self.logger.exception(exc)

        self.logger.debug(
            f"Won't follow {username}: does not meet keywords requirement. Keywords not found."
        )

    def verify_account_followers(self, username):
        if self.user_min_follow == 0 and self.user_max_follow == 0:
            return True

        try:
            followers = self.get_followers_count(username)
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

        except Exception as exc:
            self.logger.exception(exc)

    def verify_account(self, username):
        return username != self.login \
               and self.verify_account_name(username) \
               and self.verify_account_followers(username)

    def new_auto_mod_follow(self, media):
        if self.iteration_ready("follow") and self.follow_per_run != 0 and media:
            self.init_next_interation("follow")
            user_id = media["node"]["owner"]["id"]
            username = self.get_username_by_user_id(user_id)

            if not self.verify_account(username):
                self.logger.debug(f"Not following {username}, the account doesn't meet requirements")
                return False

            if self.persistence.check_already_followed(user_id=user_id):
                self.logger.debug(f"Already followed before {username}")
                return False

            log_string = f"Trying to follow: {username}"
            self.logger.debug(log_string)

            if self.follow(user_id=user_id, username=username):
                return True

    def populate_from_feed(self):
        medias = self.get_medias_from_recent_feed()

        try:
            for mediafeed_user in medias:
                feed_username = mediafeed_user["node"]["owner"]["username"]
                feed_user_id = mediafeed_user["node"]["owner"]["id"]
                # print(self.persistence.check_if_userid_exists( userid=feed_user_id))
                if not self.persistence.check_if_userid_exists(userid=feed_user_id):
                    self.persistence.insert_username(
                        user_id=feed_user_id, username=feed_username
                    )
                    self.logger.debug(f"Inserted user {feed_username} from recent feed")
        except Exception as exc:
            self.logger.warning("Notice: could not populate from recent feed")
            self.logger.exception(exc)

    def new_auto_mod_unfollow(self):
        if self.iteration_ready("unfollow"):
            self.init_next_interation("unfollow")
            user = self.persistence.get_username_to_unfollow_random()
            if user:
                self.logger.debug(f"Trying to unfollow #{self.unfollow_counter + 1}: {user}")
                if self.auto_unfollow(user):
                    return True

    # new Method splitted from new_auto_mod_unfollow
    def new_auto_mod_unfollow_from_feed(self):
        if self.unfollow_from_feed:
            try:
                if (
                        time.time() > self.next_iteration["Populate"]
                        and self.unfollow_recent_feed is True
                ):
                    self.populate_from_feed()
                    self.next_iteration["Populate"] = time.time() + (
                        self.generate_time(360)
                    )
            except Exception as exc:
                self.logger.warning(
                    "Notice: Could not populate from recent feed right now"
                )
                self.logger.exception(exc)

            log_string = f"Trying to unfollow #{self.unfollow_counter + 1}:"
            self.logger.debug(log_string)
            self.auto_unfollow()
            self.next_iteration["Unfollow"] = time.time() + self.generate_time(
                self.unfollow_delay
            )

    def auto_unfollow(self, user):
        user_id = user.id
        user_name = user.username
        if not user_name:
            _username = self.get_username_by_user_id(user_id=user_id)
            if _username:
                user_name = _username
            else:
                self.logger.debug(f"Cannot resolve username from user id: {current_id}")
                return False

        if self.verify_unfollow(user_name):
            return self.unfollow(user_id, user_name)
        else:
            self.persistence.insert_unfollow_count(user_id=user_id)
            return True

    def verify_unfollow(self, user_name):
        user_info = self.get_user_info(user_name)
        if not user_info:
            return False

        if self.unfollow_everyone:
            self.logger.debug("Ignore verifications, Unfollow everyone flag is set")
            return True

        self.logger.debug(f"Getting user info : {user_name} - "
                          f"Followers : {user_info.get('followers')} - "
                          f"Following : {user_info.get('follows')} - "
                          f"Media : {user_info.get('medias')}")

        if user_name in self.unfollow_whitelist:
            self.logger.debug("This account {user_name} is marked in the whitelist")
            return False
        if not self.account_is_followed_by_you(user_info):
            self.logger.debug("You're not follwing this account")
            return False

        if self.account_is_selebgram(user_info) and self.unfollow_selebgram:
            self.logger.debug("This account is a selebgram account")
            return True

        if self.account_is_fake(user_info) and self.unfollow_probably_fake:
            self.logger.debug("This account is a fake account")
            return True

        if not self.account_is_active(user_info) and self.unfollow_inactive:
            self.logger.debug("This account is not active")
            return True

        if not self.account_is_following_you(user_info) and self.unfollow_not_following:
            self.logger.debug("This account is not following you")
            return True

        return False

    def get_user_info(self, user_name):
        url_tag = self.url_user_detail % (user_name)
        try:
            r = self.s.get(url_tag)
            if r.text.find("The link you followed may be broken, or the page may have been removed.") >= 0:
                self.logger.debug(f"This account was deleted : {user_name}")
                return False
            raw_data = re.search("window._sharedData = (.*?);</script>", r.text, re.DOTALL).group(1)
            user_data = json.loads(raw_data)["entry_data"]["ProfilePage"][0]["graphql"]["user"]
            user_info = dict(follows=user_data["edge_follow"]["count"],
                             followers=user_data["edge_followed_by"]["count"],
                             medias=user_data["edge_owner_to_timeline_media"]["count"],
                             follows_viewer=user_data["follows_viewer"],
                             followed_by_viewer=user_data["followed_by_viewer"],
                             requested_by_viewer=user_data["requested_by_viewer"],
                             has_requested_viewer=user_data["has_requested_viewer"])
            return user_info
        except Exception as exc:
            self.logger.exception(exc)
            return None

    def account_is_selebgram(self, user_info):
        return user_info.get("follows") == 0 or (user_info.get("followers") / user_info.get("follows") > 2)

    def account_is_fake(self, user_info):
        return user_info.get("followers") == 0 or (user_info.get("follows") / user_info.get("followers") > 2)

    def account_is_active(self, user_info):
        return user_info.get("medias") > 0 \
               and (user_info.get("follows") / user_info.get("medias") < 25) \
               and (user_info.get("followers") / user_info.get("medias") < 25)

    def account_is_following_you(self, user_info):
        return user_info.get("follows_viewer") or user_info.get("has_requested_viewer")

    def account_is_followed_by_you(self, user_info):
        return user_info.get("followed_by_viewer") or user_info.get("requested_by_viewer")

    def new_auto_mod_comments(self, media):
        if self.iteration_ready("comments") and self.verify_media_before_comment(media):
            self.init_next_interation("comments")
            comment_text = self.generate_comment()
            if "@username@" in comment_text:
                comment_text = comment_text.replace("@username@", media["node"]["owner"]["username"])

            media_id = media["node"]["id"]

            if not self.comment(media_id, comment_text):
                self.persistence.insert_media(media["node"]["id"], "Error")

    def init_next_interation(self, action):
        self.next_iteration[action] = self.generate_time(
            getattr(self, action + "_delay", -2 * time.time())) + time.time()

    def iteration_ready(self, action):
        action_counter = getattr(self, action + "_counter", 0)
        action_counter_per_run = getattr(self, action + "_per_run", 0)
        registered_time = self.next_iteration.get(action, 0)
        return action_counter < action_counter_per_run and registered_time >= 0 and time.time() > registered_time

    def generate_time(self, time):
        """ Make some random for next iteration"""
        return time * 0.9 + time * 0.2 * random.random()

    def generate_comment(self):
        c_list = list(itertools.product(*self.comment_list))

        repl = [("  ", " "), (" .", "."), (" !", "!")]
        res = " ".join(random.choice(c_list))
        for s, r in repl:
            res = res.replace(s, r)
        return res.capitalize()

    def verify_media_before_comment(self, media):
        media_code = media["node"]["shortcode"]
        url_check = self.url_media % (media_code)
        try:
            resp = self.s.get(url_check)
        except Exception as exc:
            self.logger.warning(f"Couldn't comment post {url_check}")
            self.logger.exception(exc)
            return False

        if "dialog-404" in resp.text:
            self.logger.warning(
                f"Tried to comment {media_code} but it doesn't exist (404). Resuming..."
            )
            return False

        if resp.status_code == 200:
            raw_data = re.search("window._sharedData = (.*?);", resp.text, re.DOTALL).group(1)
            all_data = json.loads(raw_data)["entry_data"]["PostPage"][0]

            if all_data["graphql"]["shortcode_media"]["owner"]["id"] == self.user_id:
                self.logger.debug("This media is yours.")
                return False
            try:
                edges = all_data["graphql"]["shortcode_media"].get("edge_media_to_comment", None)
                if not edges:
                    edges = all_data["graphql"]["shortcode_media"].get("edge_media_to_parent_comment", None)

                comments = list(edges["edges"])
            except Exception as exc:
                self.logger.critical("Cannot retrieve comments from media. ")
                self.logger.exception(exc)

            for comment in comments:
                if comment["node"]["owner"]["id"] == self.user_id:
                    self.logger.debug("Media is already commented")
                    return False

            return True
        elif resp.status_code == 404:
            self.logger.warning(f"{media_code} doesn't exist (404).")
            return False

    def get_medias_from_recent_feed(self):
        self.logger.debug(f"{self.user_login} : Get media id on recent feed")
        url_tag = "https://www.instagram.com/"
        try:
            r = self.s.get(url_tag)
            jsondata = re.search("additionalDataLoaded\('feed',({.*})\);", r.text).group(1)
            all_data = json.loads(jsondata.strip())
            media_on_feed = list(all_data["user"]["edge_web_feed_timeline"]["edges"])
            self.logger.debug(f"Media in recent feed = {len(media_on_feed)}")

        except Exception as exc:
            logging.exception(exc)
            media_on_feed = []
        return media_on_feed

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
