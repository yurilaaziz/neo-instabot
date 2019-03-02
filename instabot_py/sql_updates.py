# -*- coding: utf-8 -*-
from datetime import datetime, timedelta


def check_and_update(self):
    """ At the Program start, i does look for the sql updates """
    self.follows_db_c.execute(
        "CREATE TABLE IF NOT EXISTS usernames (username varchar(300))"
    )
    self.follows_db_c.execute(
        "CREATE TABLE IF NOT EXISTS medias (media_id varchar(300))"
    )
    table_info = self.follows_db_c.execute("pragma table_info(medias)")
    table_column_status = [o for o in table_info if o[1] == "status"]
    if not table_column_status:
        self.follows_db_c.execute("ALTER TABLE medias ADD COLUMN status integer")
    table_info = self.follows_db_c.execute("pragma table_info(medias)")
    table_column_status = [o for o in table_info if o[1] == "datetime"]
    if not table_column_status:
        self.follows_db_c.execute("ALTER TABLE medias ADD COLUMN datetime TEXT")
    table_info = self.follows_db_c.execute("pragma table_info(medias)")
    table_column_status = [o for o in table_info if o[1] == "code"]
    if not table_column_status:
        self.follows_db_c.execute("ALTER TABLE medias ADD COLUMN code TEXT")
    table_info = self.follows_db_c.execute("pragma table_info(usernames)")
    table_column_status = [o for o in table_info if o[1] == "username_id"]
    if not table_column_status:
        qry = """
            CREATE TABLE "usernames_new" ( `username_id` varchar ( 300 ), `username` TEXT  );
            INSERT INTO "usernames_new" (username) Select username from usernames;
            DROP TABLE "usernames";
            ALTER TABLE "usernames_new" RENAME TO "usernames";
              """
        self.follows_db_c.executescript(qry)
    table_info = self.follows_db_c.execute("pragma table_info(usernames)")
    table_column_status = [o for o in table_info if o[1] == "unfollow_count"]
    if not table_column_status:
        self.follows_db_c.execute(
            "ALTER TABLE usernames ADD COLUMN unfollow_count INTEGER DEFAULT 0"
        )
    table_info = self.follows_db_c.execute("pragma table_info(usernames)")
    table_column_status = [o for o in table_info if o[1] == "last_followed_time"]
    if not table_column_status:
        self.follows_db_c.execute(
            "ALTER TABLE usernames ADD COLUMN last_followed_time TEXT"
        )
    table_info = self.follows_db_c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='settings';"
    ).fetchone()
    if not table_info:
        qry = """
            CREATE TABLE "settings" ( `settings_name` TEXT, `settings_val` TEXT  );
              """
        self.follows_db_c.execute(qry)
    # table_column_status = [o for o in table_info if o[1] == "last_followed_time"]
    # if not table_column_status:
    #    self.follows_db_c.execute("ALTER TABLE usernames ADD COLUMN last_followed_time TEXT")


def check_already_liked(self, media_id):
    """ controls if media already liked before """
    if (
            self.follows_db_c.execute(
                "SELECT EXISTS(SELECT 1 FROM medias WHERE media_id='"
                + media_id
                + "' LIMIT 1)"
            ).fetchone()[0]
            > 0
    ):
        return 1
    return 0


def check_already_followed(self, user_id):
    """ controls if user already followed before """
    if (
            self.follows_db_c.execute(
                "SELECT EXISTS(SELECT 1 FROM usernames WHERE username_id='"
                + user_id
                + "' LIMIT 1)"
            ).fetchone()[0]
            > 0
    ):
        return 1
    return 0


def check_already_unfollowed(self, user_id):
    """ controls if user was already unfollowed before """
    if (
            self.follows_db_c.execute(
                "SELECT EXISTS(SELECT 1 FROM usernames WHERE username_id='"
                + user_id
                + "' AND unfollow_count > 0 LIMIT 1)"
            ).fetchone()[0]
            > 0
    ):
        return 1
    return 0


def insert_media(self, media_id, status):
    """ insert media to medias """
    now = datetime.now()
    self.follows_db_c.execute(
        "INSERT INTO medias (media_id, status, datetime) VALUES('"
        + media_id
        + "','"
        + status
        + "','"
        + str(now)
        + "')"
    )


def insert_username(self, user_id, username):
    """ insert user_id to usernames """
    now = datetime.now()
    self.follows_db_c.execute(
        "INSERT INTO usernames (username_id, username, last_followed_time) \
                               VALUES('"
        + user_id
        + "','"
        + username
        + "','"
        + str(now)
        + "')"
    )


def insert_unfollow_count(self, user_id=False, username=False):
    """ track unfollow count for new futures """
    if user_id:
        qry = (
                "UPDATE usernames \
                  SET unfollow_count = unfollow_count + 1 \
                  WHERE username_id ='"
                + user_id
                + "'"
        )
        self.follows_db_c.execute(qry)
    elif username:
        qry = (
                "UPDATE usernames \
                  SET unfollow_count = unfollow_count + 1 \
                  WHERE username ='"
                + username
                + "'"
        )
        self.follows_db_c.execute(qry)
    else:
        return False


def get_usernames_first(self):
    """ Gets first element of usernames table """
    username = self.follows_db_c.execute("SELECT * FROM usernames LIMIT 1")
    if username:
        return username
    else:
        return False


def get_usernames(self):
    """ Gets usernames table """
    usernames = self.follows_db_c.execute("SELECT * FROM usernames")
    if usernames:
        return usernames
    else:
        return False


def get_username_random(self):
    """ Gets random username """
    username = self.follows_db_c.execute(
        "SELECT * FROM usernames WHERE unfollow_count=0 ORDER BY RANDOM() LIMIT 1"
    ).fetchone()
    if username:
        return username
    else:
        return False


def get_username_to_unfollow_random(self):
    """ Gets random username that is older than follow_time and has zero unfollow_count """
    now_time = datetime.now()
    cut_off_time = now_time - timedelta(seconds=self.follow_time)
    username = self.follows_db_c.execute(
        "SELECT * FROM usernames WHERE \
    DATETIME(last_followed_time) < DATETIME('"
        + str(cut_off_time)
        + "') \
    AND unfollow_count=0 ORDER BY RANDOM() LIMIT 1"
    ).fetchone()
    if username:
        return username
    elif self.follow_time_enabled is False:
        username = self.follows_db_c.execute(
            "SELECT * FROM usernames WHERE \
        unfollow_count=0 ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        if username:
            return username
        else:
            return False
    else:
        return False


def get_username_row_count(self):
    """ Gets the number of usernames in table """
    count = self.follows_db_c.execute("select count(*) from usernames").fetchone()
    if count:
        return count[0]
    else:
        return False


def get_medias_to_unlike(self):
    """ Gets random medias that is older than unlike_time"""
    now_time = datetime.now()
    cut_off_time = now_time - timedelta(seconds=self.time_till_unlike)
    media = self.follows_db_c.execute(
        "SELECT media_id FROM medias WHERE \
    DATETIME(datetime) < DATETIME('"
        + str(cut_off_time)
        + "') \
    AND status=200 ORDER BY RANDOM() LIMIT 1"
    ).fetchone()
    if media:
        return media[0]
    return False


def update_media_complete(self, media_id):
    """ update media to medias """
    qry = "UPDATE medias SET status='201' WHERE media_id ='" + media_id + "'"
    self.follows_db_c.execute(qry)


def check_if_userid_exists(self, userid):
    """ Checks if username exists """
    # print("select count(*) from usernames WHERE username_id = " + userid)
    count = self.follows_db_c.execute(
        "select count(*) from usernames WHERE username_id = " + userid
    ).fetchone()
    if count:
        if count[0] > 0:
            return True
        else:
            return False
    else:
        return False


def check_and_insert_user_agent(self, user_agent):
    """ Check user agent  """
    qry = "SELECT settings_val from settings where settings_name = 'USERAGENT'"
    result_check = self.follows_db_c.execute(qry).fetchone()
    if result_check:
        result_get = result_check[0]
        return result_get
    else:
        qry_insert = (
                """
                        INSERT INTO settings (settings_name, settings_val)
                        VALUES ('USERAGENT', '%s')
                         """
                % user_agent
        )
        self.follows_db_c.execute(qry_insert)
        return check_and_insert_user_agent(self, user_agent)
