import os.path

from setuptools import setup, find_packages
try:
    import instabot_py
    __version__ = instabot_py.__version__
except:
    __version__ = "devel"

try:
    here = os.path.abspath(os.path.dirname(__file__))
    README = open(os.path.join(here, "README.md"), encoding="utf-8").read()
    with open(os.path.join(here, "requirements/base.txt"), encoding="utf-8") as f:
        required = [l.strip("\n") for l in f if l.strip("\n") and not l.startswith("#")]
except IOError:
    required = []
    README = ""

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
