from collections import OrderedDict

import pytest
from config42 import ConfigManager


@pytest.fixture
def pwd(project_working_dir):
    return project_working_dir


@pytest.fixture
def cwd():
    from os.path import dirname, join
    cwd = join(dirname(__file__))
    return cwd


@pytest.fixture
def bot(tmp_path, cwd):
    from instabot_py import InstaBot
    import logging.config
    _config = ConfigManager(defaults={'config42': OrderedDict(
        [
            ('env', {'prefix': 'INSTABOT'}),
            ('file', {'path': cwd + '/files/instabot.config.yml'}),
        ]
    )})
    logging.basicConfig(level=logging.DEBUG)
    return InstaBot(**_config.as_dict(),
                    session_file=str(tmp_path / "requests.session"),
                    database={
                        "type": "sql",
                        "connection_string": "sqlite:///" + str(tmp_path / "sqlite.db")})


@pytest.fixture
def config(cwd):
    config = ConfigManager(defaults={'config42': OrderedDict(
        [
            ('env', {'prefix': 'TEST'}),
            ('file', {'path': cwd + '/files/config.yml'}),
        ]
    )})
    return config


@pytest.fixture
def get_medias(config, bot):
    return bot.get_media_id_by_tag(config.get("tags")[0])


@pytest.fixture
def one_media(get_medias):
    return get_medias[0]
