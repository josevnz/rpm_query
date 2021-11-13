# Unit testing and packaging an application to query an RPM database with Python

When you install software on a Linux system, your package manager keeps track of what's installed, what it's dependent upon, what it provides, and much more.
The usual way to look at that metadata is through your package manager.
The RPM database, for example, can be queried from the command line with the `rpm` command, which supports some very nice formatting options. For example, to get a list of all packages sorted by size, you can do the following:

```shell=
$ rpm -qa --queryformat "%{NAME}-%{VERSION} %{SIZE}\n"|sort -r -k 2 -n
...
linux-firmware-20200421 256914779
conda-4.8.4 228202733
glibc-all-langpacks-2.29 217752640
docker-ce-cli-19.03.12 168609825
clang-libs-8.0.0 117688777
wireshark-cli-3.2.3 108810552
llvm-libs-8.0.0 108310728
docker-ce-19.03.12 106517368
ansible-2.9.9 102477070
```

But what if you want to format the numbers in the output? Or to be able to display the results with scrolling? The `rpm` command has many options, but what if you need to integrate RPM output in other applications?
And once you've written it, what about unit testing your code or distributing it to other machines?

This is where other languages like Python shine. In this tutorial, I demonstrate how to:

* Interact with the RPM database using Python
* Create an interface to parse the command line using Argparse
* Unit test your new code with unittest 
* Package and test your code with the help of setuptools

That's a lot to cover, so basic knowledge of Python is required. Also you should know what RPM is. But even if you don't know much, the code is simple to follow and the boilerplate code is small.

Python is a great default language for system administrators, and the RPM database [comes with bindings](http://ftp.rpm.org/api/4.4.2.2/group__python.html) that make it easy to query with Python.

There are [several chapters](https://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-rpm-programming-python.html) dedicated to this in the Fedora documentation, but in this article you'll write a simple program that prints a list of RPM packages sorted by size.

## Setup

First clone the code for this tutorial:

```shell=
git clone git@github.com:josevnz/tutorials.git
cd rpm_query
```

For this tutorial to work, you must have the `python3-rpm` package installed.
RPM has deep ties with the system, that's maybe one of the reasons it's not offered through the `pip` command and the PyPi module repository.
You can install it instead with the `dnf` command:

```shell=
sudo dnf install -y python3-rpm
```

## Virtual environment

Your Python virtual environment must include site packages.
A [virtual environment](https://opensource.com/article/20/10/venv-python) is a sandboxed location where you can install Python code and dependencies without disturbing your main distribution.

You can install the dependencies for this tutorial in a virtual environment. I strongly recomend ***AGAINST*** installing thes modules system-wide, as they **can destroy your system**. 
Also, for this virtual environment to work, you need to 'leak' the system packages inside your virtual environments, as the system package you need is python3-rpm and it's not available through `pip`.
You can provide access to site packages using the `--system-site-packages` option:

```shell=
python3 -m venv --system-site-packages ~/virtualenv/rpm_query
. ~/virtualenv/rpm_query/bin/activate
```

## Query RPM with sorting

In this example application, I wrap the RPM instance in a '[context manager](https://docs.python.org/3/library/contextlib.html)'.
This makes it easier to use, and also saves you from worrying about closing the RPM database. Also, I'll take a few shortcuts to return the result of the database query.

A few things to notice:

* [The code](https://github.com/josevnz/rpm_query/blob/main/reporter/rpm_query.py) that imports the RPM is in a try/except clause because it is possible that the RPM is not installed. So if it fails, it does so gracefully, explaining that it needs to be installed.
* Depending on whether the user wants the results sorted by size or not, a reference to the code in the ``__get__`` function is passed.
* The customization magic happens in the constructor, with named parameters. After that, the code returns database transactions in the ``` __enter__``` method.

```python=
"""
Wrapper around RPM database
"""
import sys
try:
    import rpm
except ModuleNotFoundError:
    print((
        "You must install the following package:\n"
        "sudo dnf install -y python3-rpm\n"
        "'rpm' doesn't come as a pip but as a system dependency.\n"
    ), file=sys.stderr)
    raise


def __get__(is_sorted: bool, dbMatch):
    if is_sorted:
        return sorted(
            dbMatch,
            key=lambda item: item['size'], reverse=True)
    return dbMatch


class QueryHelper:

    UNLIMITED = -1

    def __init__(self, *, limit: int = UNLIMITED, name: str = None, sorted_val: bool = True):
        """
        :param limit: How many results to return
        :param name: Filter by package name, if any
        :param sorted_val: Sort results
        """
        self.ts = rpm.TransactionSet()
        self.name = name
        self.limit = limit
        self.sorted = sorted_val

    def __enter__(self):
        """
        Returns list of items on the RPM database
        :return:
        """
        if self.name:
            db = self.db = self.ts.dbMatch("name", self.name)
        else:
            db = self.db = self.ts.dbMatch()
        count = 0
        for package in __get__(self.sorted, db):
            if self.limit != self.UNLIMITED:
                if count < self.limit:
                    count += 1
                else:
                    break
            yield package

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ts.closeDB()

    def count(self):
        """
        How many results were found
        :return:
        """
        return self.db.count()
```

# Unit testing with unittest

*How good is this code without testing*? 

You definitely want to automate the testing of your code. Unit testing is different than other types of testing. Overall, it makes your application more robust because it ensures the smallest components of your application behave correctly.

In this case, unit test is nothing more than a class that exercises functionality of the RPM wrapper class, running several small methods that test for very specific conditions. In the case of `unittest`, they follow certain conventions so the framework can call each test case one by one.

I wrote a [unit test](https://github.com/josevnz/rpm_query/blob/main/tests/test_rpm_query.py) for the `reporter.rpm_query.QueryHelper` class. The code has several assertions that must be true in order to pass the each test case.

```python=
"""
Unit tests for the QueryHelper class
Please read how to write unit tests: 
https://docs.python.org/3/library/unittest.html
"""
import os
import unittest
from reporter.rpm_query import QueryHelper

DEBUG = True if os.getenv("DEBUG_RPM_QUERY") else False

class QueryHelperTestCase(unittest.TestCase):
    def test_get_unsorted_counted_packages(self):
        """
        Test retrival or unsorted counted packages
        :return:
        """
        LIMIT = 10
        with QueryHelper(limit=LIMIT, sorted_val=False) as rpmquery:
            count = 0
            for package in rpmquery:
                count += 1
                self.assertIn('name', package, "Could not get 'name' in package?")
            self.assertEqual(LIMIT, count, f"Limit ({count}) did not worked!")

    def test_get_all_packages(self):
        """
        Default query is all packages, sorted by size
        :return:
        """
        with QueryHelper() as rpmquery:
            previous_size = 0
            previous_package = None
            for package in rpmquery:
                size = package['size']
                if DEBUG:
                    print(f"name={package['name']} ({size}) bytes")
                self.assertIn('name', package, "Could not get 'name' in package?")
                if previous_size > 0:
                    self.assertGreaterEqual(
                        previous_size,
                        size,
                        f"Returned entries not sorted by size in bytes ({previous_package}, {package['name']})!")
                    previous_size = size
                    previous_package = package['name']

    def test_get_named_package(self):
        """
        Test named queries
        :return:
        """
        package_name = "glibc-common"
        with QueryHelper(name=package_name, limit=1) as rpmquery:
            found = 0
            for package in rpmquery:
                self.assertIn('name', package, "Could not get 'name' in package?")
                if DEBUG:
                    print(f"name={package['name']}, version={package['version']}")
                found += 1
        self.assertGreater(found, 0, f"Could not find a single package with name {package_name}")


if __name__ == '__main__':
    unittest.main()
```

I strongly recommend you read [official unittest documentation](https://docs.python.org/3/library/unittest.html) for more details, as there's so much more unit testing than this simple code, like [mock testing](https://docs.python.org/3/library/unittest.mock.html), which is particularly useful for complex dependency scenarios.


# QueryHelper and Argparse

You can use the `QueryHelper` wrapper class and parse command-line arguments with Argparse. Using this class to query the RPM database becomes very easy. A few things to note with the code below:

* With [argparse](https://docs.python.org/3/library/argparse.html), we can have complete control of command-line options, complete with a help message and default values.

```python=
#!/usr/bin/env python
"""
# rpmq_simple.py - A simple CLI to query the sizes of RPM on your system
Author: Jose Vicente Nunez
"""
import argparse
import textwrap

from reporter import __is_valid_limit__
from reporter.rpm_query import QueryHelper

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=textwrap.dedent(__doc__))
    parser.add_argument(
        "--limit",
        type=__is_valid_limit__,  # Custom limit validator
        action="store",
        default=QueryHelper.MAX_NUMBER_OF_RESULTS,
        help="By default results are unlimited but you can cap the results"
    )
    parser.add_argument(
        "--name",
        type=str,
        action="store",
        help="You can filter by a package name."
    )
    parser.add_argument(
        "--sort",
        action="store_false",
        help="Sorted results are enabled bu default, but you fan turn it off"
    )
    args = parser.parse_args()

    with QueryHelper(
        name=args.name,
        limit=args.limit,
        sorted_val=args.sort
    ) as rpm_query:
        current = 0
        for package in rpm_query:
            if current >= args.limit:
                break
            print(f"{package['name']}-{package['version']}: {package['size']:,.0f}")
            current += 1
```

You can install your new application in something called 'development mode'. What that means is that a symbolic link is created to your sandbox, which allow you to make changes and still test the application:

```shell
(rpm_query)$ python setup.py develop
```

So how does the output look now? Try asking for all the RPMs you have installed, sorted, and limited to the first 20 entries:

```shell=
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

By the way, once you are done testing you can remove development mode:

```shell
python setup.py develop --uninstall
```

# Packaging and installing the distribution

Now that you're ready to deploy your application, you can package it, copy its wheel file, and then install it in a new virtual environment. But first, you need to define a very important file: `setup.py`, which is used by [setuptools](https://opensource.com/article/21/11/packaging-python-setuptools).

The most important sections in the file below are:

* *_requires sections: build and installation dependencies
* packages: the location of your Python classes
* scripts: these are the scripts that the end user calls to interact with your libraries (if any)

```python=
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

The official documentation recommends migrating from a `setup.py` configuration to `setup.cfg`, but I decided to use `setup.py` because it's what I'm familiar with.


```shell
(rpm_query)$ python setup.py bdist_wheel
running bdist_wheel
...
```

Then you can install it on the the same machine or a new machine, in a virtual environment:

```shell
(rpm_query)$ python setup.py install \
dist/rpm_query-1.0.0-py3-none-any.whl
```

## Uploading your application to a repository

The most common way to share Python code is to upload it to an artifact manager like Sonatype Nexus. For that, you can use a tool like [twine](https://twine.readthedocs.io/en/latest/).

```shell=
(rpm_query)$ pip install twine
# Configure twine to upload to a repository without prompting a password, etc, by editing ~/.pypirc
...
(rpm_query)$ python upload --repository myprivaterepo \
dist/rpm_query-1.0.0-py3-none-any.whl
```

Setting this up is a lengthy topic by itself, which is out of scope for this article.

# What you've learned

This has been a lot of information, and here's a reminder of what I covered:

* Write unit tests.
* Package your application with [setuptools](https://setuptools.pypa.io/en/latest/index.html) or a framework of your choice. Make installations and testing repeatable.
* Learn how to use [Argparse](https://opensource.com/article/21/7/argument-parsing-python-argparse). Your users and your future self will thank you if you provide an easy to use CLI!

Finally, get more famliar with the RPM API. [This article barely scratches the surface](https://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-rpm-programming-python.html) of all the things you can do with it!
