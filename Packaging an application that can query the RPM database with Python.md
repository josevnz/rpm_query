# Packaging an application to query an RPM database with Python

On a previous article I showed you how to write a script in Python that was able to get the list of RPM installed on a machine:

```shell
(rpm_query)$ rpmqa_simple.py --limit 20
linux-firmware-20210818: 395,099,476
code-1.61.2: 303,882,220
brave-browser-1.31.87: 293,857,731
libreoffice-core-7.0.6.2: 287,370,064
thunderbird-91.1.0: 271,239,962
firefox-92.0: 266,349,777
glibc-all-langpacks-2.32: 227,552,812
mysql-workbench-community-8.0.23: 190,641,403
java-11-openjdk-headless-11.0.13.0.8: 179,469,639
iwl7260-firmware-25.30.13.0: 148,167,043
docker-ce-cli-20.10.10: 145,890,250
google-noto-sans-cjk-ttc-fonts-20190416: 136,611,853
containerd.io-1.4.11: 113,368,911
ansible-2.9.25: 101,106,247
docker-ce-20.10.10: 100,134,880
ibus-1.5.23: 90,840,441
llvm-libs-11.0.0: 87,593,600
gcc-10.3.1: 84,899,923
cldr-emoji-annotation-38: 80,832,870
kernel-core-5.14.12: 79,447,964
```

The problem we are trying to solve now is how we can package our application, so it can be easily installed on other machines, including all the dependencies. I will show you how to use setuptools for that.

That's a lot to cover, so basic knowledge of Python is required. Even if you don't know much, the code is simple to follow, and the boilerplate code is small.

# Setup

I explained how to install this code on a [previous tutorial](https://github.com/josevnz/rpm_query/blob/main/Writting%20and%20Unit%20testing%20an%20application%20that%20can%20query%20the%20RPM%20database%20with%20Python.md) and the usage of [virtual environment](https://opensource.com/article/20/10/venv-python), but you can take a shortcut and just to this:

```shell
sudo dnf install -y python3-rpm
git clone git@github.com:josevnz/tutorials.git
cd rpm_query
python3 -m venv --system-site-packages ~/virtualenv/rpm_query
. ~/virtualenv/rpm_query/bin/activate
```

# Packaging and installing the distribution

Now that you're ready to deploy your application, you can package it, copy its wheel file, and then install it in a new virtual environment. First, you need to define a very important file: `setup.py`, which is used by [setuptools](https://opensource.com/article/21/11/packaging-python-setuptools).

The most important sections in the file below are:

* *_requires sections: build and installation dependencies
* packages: the location of your Python classes
* scripts: these are the scripts that the end user calls to interact with your libraries (if any)

```python
"""
Project packaging and deployment
More details: https://setuptools.pypa.io/en/latest/userguide/quickstart.html
"""
import os
from setuptools import setup
from reporter import __version__


def __read__(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setup(
    name="rpm_query",
    version=__version__,
    author="Jose Vicente Nunez Zuleta",
    author_email="kodegeek.com@protonmail.com",
    description=__doc__,
    license="Apache",
    keywords="rpm query",
    url="https://github.com/josevnz/rpm_query",
    packages=[
        'reporter'
    ],
    long_description=__read__('README.md'),
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
        "dearpygui==1.0.2"
    ],
    install_requires=[
        "rich==9.5.1",
    ],
    scripts=[
        "bin/rpmq_simple.py",
    ]
)
```

```shell
(rpm_query)$ python setup.py develop
```

By the way, once you are done testing you can remove development mode:

```shell
python setup.py develop --uninstall
```

The official documentation recommends migrating from a `setup.py` configuration to `setup.cfg`, but I decided to use `setup.py` because it's what I'm familiar with.


```shell
(rpm_query)$ python setup.py bdist_wheel
running bdist_wheel
...
```

Then you can install it on the same machine or a new machine, in a virtual environment:

```shell
(rpm_query)$ python setup.py install \
dist/rpm_query-1.0.0-py3-none-any.whl
```

By the way, once you are done testing you can remove development mode:

```shell
python setup.py develop --uninstall
```

# Uploading your application to a repository

The most common way to share Python code is to upload it to an artifact manager like Sonatype Nexus. For that, you can use a tool like [twine](https://twine.readthedocs.io/en/latest/).

```shell
(rpm_query)$ pip install twine
# Configure twine to upload to a repository without prompting a password, etc, by editing ~/.pypirc
...
(rpm_query)$ python upload --repository myprivaterepo \
dist/rpm_query-1.0.0-py3-none-any.whl
```

Setting this up is a lengthy topic by itself, which is out of scope for this article.

# What you've learned

This has been a lot of information, and here's a reminder of what I covered:

* Package your application with [setuptools](https://setuptools.pypa.io/en/latest/index.html) or a framework of your choice. Make installations and testing repeatable.

