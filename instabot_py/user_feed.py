#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time

from .user_info import get_user_info


def get_media_id_user_feed(self):
    if self.login_status:
        if self.is_by_tag != True:
            log_string = "======> Get media id by user: %s <======" % (
                self.current_user
            )
            if self.is_checked != True:
                get_user_info(self, self.current_user)
            if (
                    self.is_fake_account != True
                    and self.is_active_user != False
                    and self.is_selebgram != True
                    or self.is_by_tag != False
            ):
                url = "https://www.instagram.com/%s/" % (self.current_user)
        self.write_log(log_string)

        if (
                self.login_status == 1
                and self.is_fake_account != True
                and self.is_active_user != False
                and self.is_selebgram != True
                or self.is_by_tag != False
        ):
            try:

                self.media_by_user = list(
                    self.current_user_info["edge_owner_to_timeline_media"]["edges"]
                )
                log_string = "Get media by user success!"
                self.write_log(log_string)
            except:
                self.media_by_user = []
                self.write_log("XXXXXXX Except on get_media! XXXXXXX")
                time.sleep(60)
                return 0
        else:
            log_string = (
                    "Reject this account \n=================== \nReason : \n   Is Selebgram : %s \n   Is Fake Account : %s \n   Is Active User : %s \n"
                    % (self.is_selebgram, self.is_fake_account, self.is_active_user)
            )
            self.write_log(log_string)
            self.is_rejected = True
            self.media_by_user = []
            self.media_on_feed = []
            return 0
