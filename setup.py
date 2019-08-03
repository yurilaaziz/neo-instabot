import os.path

from pkg_resources import get_distribution, DistributionNotFound
from setuptools import setup, find_packages

try:
    here = os.path.abspath(os.path.dirname(__file__))
    README = open(os.path.join(here, "README.md"), encoding="utf-8").read()
    with open(os.path.join(here, "requirements/base.txt"), encoding="utf-8") as f:
        required = [l.strip("\n") for l in f if l.strip("\n") and not l.startswith("#")]
except IOError:
    required = []
    README = ""

try:
    _dist = get_distribution('instabot_py')
    dist_loc = os.path.normcase(_dist.location)
    here = os.path.normcase(__file__)
    if not here.startswith(os.path.join(dist_loc, 'instabot_py')):
        raise DistributionNotFound
except DistributionNotFound:
    __version__ = 'Please install this project with setup.py'
else:
    __version__ = _dist.version

setup(
    name="instabot-py",
    packages=find_packages(),
    version=__version__,
    python_requires=">3.6.1",
    license="MIT",
    description="Instagram Python Bot",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Pasha Lev",
    author_email="levpasha@gmail.com",
    url="https://github.com/instabot-py/instabot.py",
    download_url="https://github.com/instabot-py/instabot.py/tarball/master",
    keywords="instagram bot, Instagram API hack",
    install_requires=required,
    entry_points={"console_scripts": ["instabot-py = instabot_py.__main__:main",
                                      "instabot-interactive = instabot_py.interactive:main"
                                      ]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
