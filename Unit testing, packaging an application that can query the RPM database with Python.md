# Unit testing, packaging an application that can query the RPM database with Python

The RPM database can be queried from the command line and the 'rpm' command line tool support nice formatting. For example, to get the list of all the packages sorted by size you could do the following:

```shell=
rpm -qa --queryformat "%{NAME}-%{VERSION} %{SIZE}\n"|sort -r -k 2 -n
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

But what if you want to format the numbers in the output? Or to be able to display the results with scrolling? rpm cli has many options but it may be complicated to add more Bash code to make tailor results to our needs.

What about unit testing your code or distributing it to other machines?

This is where other languages like Python shine. On this tutorial you will learn about the following:

* How to interact with the RPM database using Python
* Using a context manager, to auto-close resources and prevent 'leaking'
* Create nice CLI to parse the command line using Argparse
* How to unit test your ne code with unittest 
* Package and test locally your code with the help of setuptools

It is quite a bit to cover and basic knowledge of python is required. Also you should know what RPM is. But even if you don't know much, the code is simple to follow and the boilerplate code is small.

## Accessing RPM database from Python

Python is the default language for system administrators, and the RPM database [comes with bindings](http://ftp.rpm.org/api/4.4.2.2/group__python.html) that make it easy to query from the scripting language.

There a [several chapters](https://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-rpm-programming-python.html) dedicated to this on the Fedora documentation, I will show you how to use this feature with a simple program that prints the list of RPM packages, sorted by size.

### Pre-requisites

#### python3-rpm must be present

First clone the code that we will use for this tutorial:

```shell=
git clone git@github.com:josevnz/tutorials.git
cd rpm_query
```

RPM has deep ties with the system, that's maybe one of the reasons is not offered as a PIP. So you need an RPM with the bindings:

```shell=
sudo dnf install -y python3-rpm
```

#### Virtual environment MUST include site packages

A [virtual environment](https://docs.python.org/3/tutorial/venv.html) is nothing more like a sandboxed location where you can install your python code and dependencies without disturbing the main distribution.

You can install the dependencies for this tutorial on a virtual environment. I strongly recomend ***AGAINST*** installing pip modules system wide as they **can destroy your system**. 
Also, for this virtual environment to work you need to 'leak' the system packages inside your virtual environments, as the system package we need is python3-rpm and it doesn't come as a pip:

```shell=
python3 -m venv --system-site-packages ~/virtualenv/rpm_query
. ~/virtualenv/rpm_query/bin/activate
```

### Our first CLI to query RPM, with sorting

I wrapped the rpm instance in a '[context manager](https://docs.python.org/3/library/contextlib.html)', to make it easier to use and also to avoid worring about closing the RPM database. Also I'll take a few shortcuts to return the result of the database query.

A few things to notice:
* [The code](https://github.com/josevnz/rpm_query/blob/main/reporter/rpm_query.py) that imports the rpm is on a try - except because it is possible than the RPM is not installed. So if we fail, we do it gracefully explaining that it needs to be installed
* Depending if we want the results sorted by size or not, a reference to the right code in ```__get__``` is passed.
* The customization magic happens on the constructor, with named parameters. After that the code returns the database transaction on the ``` __enter__``` method when you use it with an 'with' (will show that in a how a [context manage works](https://docs.python.org/3/library/contextlib.html))

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
**How good is this code without testing**? 

You [definitely want to automate the testing of your code](https://www.freecodecamp.org/news/an-introduction-to-testing-in-python/). [Unit testing is different](https://stackabuse.com/unit-testing-in-python-with-unittest/) than other types of testing. Overall, it will make your application more robust because by making sure the smallest components of your application behave correctly.

In this case unit test is nothing more than a class that exercises functionality of our rpm wrapper class, running several small methods that test for very specific contions. In the case of unittest they follow certain conventions so the framework can call our test cases one by one.

I wrote a [unit test](https://github.com/josevnz/rpm_query/blob/main/tests/test_rpm_query.py) for the `reporter.rpm_query.QueryHelper` class. The code has several assertions that must be true in order to pass the each test case.

```python=
"""
Unit tests for the QueryHelper class
Please read how to write unit tests: https://docs.python.org/3/library/unittest.html
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

I strongly recommend you read [official unittest documentation](https://docs.python.org/3/library/unittest.html) for more details, as there is so much more unit testing than this simple code, like [mock testing](https://docs.python.org/3/library/unittest.mock.html) (useful for more complex dependency scenarios)


# Using QueryHelper wrapper class, parse command line arguments with Argparse

And then using this class to query the RPM database becomes very easy. A few things to note with the code below:

* With [argparse](https://docs.python.org/3/library/argparse.html) we can have complete control of command line options, with help and default values. Doing this from Bash requires more glue code and is still not as complete as the python code (take a look how the limit is validated with ```__is_valid_limit__``` function imported from the file [reporter/__init__.py](https://github.com/josevnz/rpm_query/blob/main/reporter/__init__.py)

```python=
#!/usr/bin/env python
"""
# rpmqa_simple.py - A simple CLI to query the sizes of RPM on your system
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
        default=QueryHelper.UNLIMITED,
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
        for package in rpm_query:
            print(f"{package['name']}-{package['version']}: {package['size']:,.0f}")
```

You can install our new application in something called  'development mode'. What that means is that a symbolic link is created to our sandbox, which will allow us to make changes and still test the application:

```shell
(rpm_query) [josevnz@dmaf5 rpm_query]$ python setup.py develop
```

So how does the output look now? Let's ask for all the RPMS, sorted and with a limit of the first 20 entries:

```shell=
(rpm_query) [josevnz@dmaf5 rpm_query]$ rpmqa_simple.py --limit 20 
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

By the way, once you are done testing you can remove the development mode:

```shell
python setup.py develop --uninstall
```

# Packaging and installing the distribution

Now that you are ready to deploy your application, you can package it, copy its wheel file and then install it on a new virtual environment. But first you need to define a very important file: setup.py, which [is used by setuptools](https://setuptools.pypa.io/en/latest/userguide/quickstart.html).

The most important sections in the file below:

* *_requires sections: build and installation dependencies
* packages: Where are your Python classes
* scripts: Which scripts the end user will call to interact with your libraries (if any).

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

The official documentation recommends migrating from the setup.py configuration to setup.cfg. I decided to use the well known setup.py as I'm not very familiar with the new way of doing things.


```shell
(rpm_query) [josevnz@dmaf5 rpm_query]$ python setup.py bdist_wheel
running bdist_wheel
...
```

Then you can install it on the the same machine or a new machine, on a virtual environment:

```shell
(rpm_query) [josevnz@dmaf5 rpm_query]$ python setup.py install dist/rpm_query-1.0.0-py3-none-any.whl
```

## What about uploading your application to a artifact repository?

The right way to share your code is to upload your distribution to an artifact manager like Sonatype Nexus. For that you can use a tool like [twine](https://twine.readthedocs.io/en/latest/).

```shell=
(rpm_query) [josevnz@dmaf5 rpm_query]$ pip install twine
# Configure twine to upload to a repository without prompting a password, etc, by editing ~/.pypirc
...
(rpm_query) [josevnz@dmaf5 rpm_query]$ python upload --repository myprivaterepo dist/rpm_query-1.0.0-py3-none-any.whl
```

Setting this up is a whole lenghty topic by itself, which we will not cover on this tutorial.

# So what did you learn so far
* Write unit tests. There are [best practices](https://dzone.com/articles/unit-testing-best-practices-how-to-get-the-most-ou) you should follow.
* Package your application with [setuptools](https://setuptools.pypa.io/en/latest/index.html) (or the framework of your choice). Make installations and testing repeatable.
* Learn how to use [Argparse](https://docs.python.org/3/library/argparse.html). Your users and your future self will thank you if you provide an easy to use CLI.
* Simplify your resource management [with a context manager](https://stackabuse.com/python-context-managers/).
* Finally get more famliar with the RPM API. [We barely scratched the surface](https://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-rpm-programming-python.html) of the things you can do with it.