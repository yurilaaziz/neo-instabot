def test_get_username_by_user_id(bot, config):
    usernames_ids = config.get("usernames_ids")
    for item in usernames_ids:
        username = item[0]
        userid = item[1]
        assert username == bot.get_username_by_user_id(userid)
