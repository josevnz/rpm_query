"""
Project packaging and deployment
More details: https://setuptools.pypa.io/en/latest/userguide/quickstart.html
"""
import os

import setuptools
from setuptools import setup
from reporter import __version__


def __read__(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setup(
    name="rpm_query",
    version=__version__,
    author="Jose Vicente Nunez Zuleta",
    long_description_content_type="text/markdown",
    long_description=__read__('README.md'),
    author_email="kodegeek.com@protonmail.com",
    description=__doc__,
    license="Apache",
    keywords="rpm query",
    url="https://github.com/josevnz/rpm_query",
    package_dir={"": "reporter"},
    packages=setuptools.find_packages(where="reporter"),
    # https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Environment :: X11 Applications",
        "Intended Audience :: System Administrators"
        "License :: OSI Approved :: Apache Software License"
    ],
    setup_requires=[
        "setuptools==49.1.3",
        "wheel==0.37.0",
        "rich==9.5.1",
        "dearpygui==1.1"
    ],
    install_requires=[
        "rich==9.5.1",
    ],
    scripts=[
        "bin/rpmq_simple.py",
        "bin/rpmq_rich.py",
        "bin/rpmq_dearpygui.py",
        "bin/rpmq_tkinter.py"
    ],
    python_requires=">=3.9",
)
