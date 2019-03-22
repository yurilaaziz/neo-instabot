#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import re
import time


def get_user_info(self, username):
    current_user = username
    log_string = "Getting user info : %s" % current_user
    self.write_log(log_string)
    if self.login_status == 1:
        url_tag = self.url_user_detail % (current_user)
        if self.login_status == 1:
            r = self.s.get(url_tag)
            if (
                    r.text.find(
                        "The link you followed may be broken, or the page may have been removed."
                    )
                    != -1
            ):
                log_string = (
                        "Looks like account was deleted, skipping : %s" % current_user
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
            self.current_user_info = user_info
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
            log_string = "Follower : %i" % (follower)
            self.write_log(log_string)
            log_string = "Following : %s" % (follows)
            self.write_log(log_string)
            log_string = "Media : %i" % (media)
            self.write_log(log_string)
            if follows == 0 or follower / follows > 2:
                self.is_selebgram = True
                self.is_fake_account = False
                self.write_log("   >>>This is probably Selebgram account")
            elif follower == 0 or follows / follower > 2:
                self.is_fake_account = True
                self.is_selebgram = False
                self.write_log("   >>>This is probably Fake account")
            else:
                self.is_selebgram = False
                self.is_fake_account = False
                self.write_log("   >>>This is a normal account")

            if media > 0 and follows / media < 25 and follower / media < 25:
                self.is_active_user = True
                self.write_log("   >>>This user is active")
            else:
                self.is_active_user = False
                self.write_log("   >>>This user is passive")

            if follow_viewer or has_requested_viewer:
                self.is_follower = True
                self.write_log("   >>>This account is following you")
            else:
                self.is_follower = False
                self.write_log("   >>>This account is NOT following you")

            if followed_by_viewer or requested_by_viewer:
                self.is_following = True
                self.write_log("   >>>You are following this account")

            else:
                self.is_following = False
                self.write_log("   >>>You are NOT following this account")

        else:
            logging.exception("Except on auto_unfollow!")
            time.sleep(3)
            return False
    else:
        return 0
