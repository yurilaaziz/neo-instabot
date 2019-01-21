from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required = [l.strip('\n') for l in f if
                l.strip('\n') and not l.startswith('#')]


"""
Building python Wheels:
1 : python3 -m venv venv; .venv/bin/activate ; pip install --upgrade setuptools wheel 
2 : python setup.py sdist bdist_wheel
3 : twine upload dist/*
"""
setup(
    name="instabot-py",
    packages=find_packages(),
    version='0.2',
    license='MIT',
    description="Instagram python Bot",
    author="Pasha Lev",
    author_email="levpasha@gmail.com",
    url="https://github.com/instabot-py/instabot.py",
    download_url='https://github.com/instabot-py/instabot.py/tarball/0.1',
    keywords="instagram bot, Instagram API hack",
    install_requires=required,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
#        'Programming Language :: Python :: 3.4', # It's higly recommended to support 3.4 and 3.5
#        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
