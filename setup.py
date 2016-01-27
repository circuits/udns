#!/usr/bin/env python


from glob import glob


from setuptools import setup, find_packages


setup(
    name="udns",
    version="0.0.2",
    description="micro dns server",
    long_description="{0:s}\n\n{1:s}".format(
        open("README.rst").read(), open("CHANGES.rst").read()
    ),
    author="James Mills",
    author_email="James Mills, prologic at shortcircuit dot net dot au",
    url="https://github.com/prologic/udns/",
    download_url="https://github.org/com/udns/releases/",
    classifiers=[
        "Development Status :: 4 - Beta",
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
    keywords="micro dns server udns",
    platforms="POSIX",
    packages=find_packages("."),
    include_package_data=True,
    scripts=glob("bin/*"),
    dependency_links=[
        "https://github.com/kiddouk/redisco/archive/master.zip#egg=redisco-0.2.4"  # noqa
    ],
    install_requires=(
        "circuits==3.0",
        "dnslib==0.9.3",
        "redisco==0.2.4",
        "cachetools==0.4.0",
    ),
    entry_points={
        "console_scripts": [
            "udnsd=udns.server:main",
            "udnsc=udns.client:main",
        ]
    },
    test_suite="tests.main.main",
    zip_safe=False
)
