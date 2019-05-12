import os

from setuptools import setup, find_packages

try:
    here = os.path.abspath(os.path.dirname(__file__))
    README = open(os.path.join(here, "README.md"), encoding="utf-8").read()
    with open(os.path.join(here, "requirements/base.txt"), encoding="utf-8") as f:
        required = [l.strip("\n") for l in f if l.strip("\n") and not l.startswith("#")]
except IOError:
    required = []
    README = ""

"""
Building python Wheels:
1 : python3 -m venv venv; .venv/bin/activate ; pip install --upgrade setuptools wheel
2 : python setup.py sdist bdist_wheel
3 : twine upload dist/*
"""

setup(
    name="instabot-py",
    packages=find_packages(),
    version="0.4.7",
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
    entry_points={"console_scripts": ["instabot-py = instabot_py.__main__:main"]},
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
