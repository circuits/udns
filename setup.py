#!/usr/bin/env python


from glob import glob
from os import getcwd, path


from setuptools import setup, find_packages


setup(
    name="microdns",
    version="0.0.1",
    description="micro dns server",
    long_description="{0:s}\n\n{1:s}".format(
        open("README.rst").read(), open("CHANGES.rst").read()
    ),
    author="James Mills",
    author_email="James Mills, prologic at shortcircuit dot net dot au",
    url="http://bitbucket.org/prologic/microdns/",
    download_url="http://bitbucket.org/prologic/microdns/downloads/",
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Communications :: Chat :: Internet Relay Chat",
    ],
    license="MIT",
    keywords="microdns dns server",
    platforms="POSIX",
    packages=find_packages("."),
    include_package_data=True,
    scripts=glob("bin/*"),
    # install_requires=(
    #     "circuits",
    # ),
    entry_points={
        "console_scripts": [
            "microdns=microdns.main:main",
        ]
    },
    test_suite="tests.main.main",
    zip_safe=False
)
