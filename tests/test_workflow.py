def test_like_unlike(bot, one_media):
    assert bot.new_auto_mod_like(one_media)
    bot.time_till_unlike = 0
    assert bot.new_auto_mod_unlike()


def test_follow_unfollow(bot, one_media):
    assert bot.new_auto_mod_follow(one_media)
    assert bot.new_auto_mod_unfollow()


def test_comment(bot, one_media):
    assert bot.new_auto_mod_comments(one_media)
