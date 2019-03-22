def test_import():
    from instabot_py import InstaBot
    bot = InstaBot(login='useruser_test', password='fake_password')
    assert bot is not None
