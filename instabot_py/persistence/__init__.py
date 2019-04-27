class PersistenceBase:
    def check_already_liked(self, media_id):
        """ controls if media already liked before """
        raise NotImplementedError()

    def check_already_followed(self, user_id):
        """ controls if user already followed before """
        raise NotImplementedError()

    def check_already_unfollowed(self, user_id):
        """ controls if user was already unfollowed before """
        raise NotImplementedError()

    def insert_media(self, media_id, status):
        """ insert media to medias """
        raise NotImplementedError()

    def insert_username(self, user_id, username):
        """ insert user_id to usernames """
        raise NotImplementedError()

    def insert_unfollow_count(self, user_id=False, username=False):
        """ track unfollow count for new futures """
        raise NotImplementedError()

    def get_username_random(self):
        """ Gets random username """
        raise NotImplementedError()

    def get_username_to_unfollow_random(self):
        """ Gets random username that is older than follow_time and has zero unfollow_count """
        raise NotImplementedError()

    def get_username_row_count(self):
        """ Gets the number of usernames in table """
        raise NotImplementedError()

    def get_medias_to_unlike(self):
        """ Gets random medias that is older than unlike_time"""
        raise NotImplementedError()

    def update_media_complete(self, media_id):
        """ update media to medias """
        raise NotImplementedError()

    def check_if_userid_exists(self, userid):
        """ Checks if username exists """
        raise NotImplementedError()

    def check_and_insert_user_agent(self, user_agent):
        """ Check user agent  """
        raise NotImplementedError()
