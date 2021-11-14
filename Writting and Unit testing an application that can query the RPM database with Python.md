# Writting and unit testing an application to query the RPM database with Python

When you install software on a Linux system, your package manager keeps track of what's installed, what it's dependent upon, what it provides, and much more.
The usual way to look at that metadata is through your package manager. In the case of Fedora or RedHat it is the [RPM database.](https://rpm.org/)
The RPM database, for example, can be queried from the command line with the `rpm` command, which supports some very nice formatting options. For example, to get a list of all packages sorted by size, you can do the following, with a little bit of Bash glue:

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
And once you've written it, what about unit testing your code script? Bash is not exactly good at that.

Instead this is where other languages like Python shine. In this tutorial, I demonstrate how to:

* Interact with the RPM database using Python RPM bindings.
* Will write my own [Python class](https://docs.python.org/3/tutorial/classes.html) to create a wrapper around the provided RPM bindings, but even if you don't know much about object oriented programming it should be easy to grasp (will keep advanced features out like virtual classes, data classes and other features).
* Make the script easier to use and customize by calling Argparse methods to parse the command line interface.
* Unit test your new code with unittest

That's a lot to cover, so basic knowledge of Python is required (for example [OO programming](https://www.datacamp.com/community/tutorials/python-oop-tutorial)). Also you should know what [RPM database.](https://rpm.org/) is. But even if you don't know much, the code is simple to follow and the boilerplate code is small.

There are [several chapters](https://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-rpm-programming-python.html) dedicated on how to interact with RPM the Fedora documentation, but in this article you'll write a simple program that prints a list of RPM packages sorted by size.

# The RPM database and Python

Python is a great default language for system administrators, and the RPM database [comes with bindings](http://ftp.rpm.org/api/4.4.2.2/group__python.html) that make it easy to query with Python.

# Setup

For this tutorial to work, you must have the `python3-rpm` package installed.
RPM has deep ties with the system, that's maybe one of the reasons it's not offered through the `pip` command and the PyPi module repository.
You can install it instead with the `dnf` command:

```shell=
sudo dnf install -y python3-rpm
```

Then you should clone the code for this tutorial:

```shell=
git clone git@github.com:josevnz/tutorials.git
cd rpm_query
```

## Virtual environment

Python has a feature called '[virtual environments](https://opensource.com/article/20/10/venv-python)'. A virtual environment provides you a sandboxed location where:

* Can install different versions of libraries than the rest of the system
* Get isolation from bad or unstable libraries. An issue with a library doesn't compromise your whole python installation.
* Because is isolated it allows you to test your software more easily before you [merge your feature branch it into your main branch](https://www.git-tower.com/blog/understanding-branches-in-git/) (A [continous integration pipeline](https://www.digitalocean.com/community/tutorials/an-introduction-to-continuous-integration-delivery-and-deployment) can take care of deploying your new code on a test virtual environment).

On this tutorial we will use a virtual environment wht the following features:
* Will be called 'rpm_query'
* We will 'leak' the system packages inside the environment, as the system package you need is python3-rpm and it's not available through `pip` (You can provide access to site packages using the `--system-site-packages` option).

In a nutshell will create and activate it like this:

```shell=
python3 -m venv --system-site-packages ~/virtualenv/rpm_query
. ~/virtualenv/rpm_query/bin/activate
```

# Coding the Query RPM class (optionally limiting number of results and sorting)

In this example application, I'll wrap the RPM instance in a '[context manager](https://docs.python.org/3/library/contextlib.html)'.
This makes it easier to use, and also saves you from worrying about manually closing the RPM database. Also, I'll take a few shortcuts to return the result of the database query.

Putting all this functionality into a class (a collection of data and methods) together is what makes object orientation so useful; in our case the RPM functionality is on a class called ```QueryHelper``` and its sole purpouse is:
* Define filtering parameters like number of items and sorting results at creation time (we use a class constructor for that)
* To provide a way to iterate through every package of the system

Let me show you first how QueryHelper class can used to get a list of a max 5 packages, sorted by size:

```python
with QueryHelper(limit=5, sorted_val=True)) as rpm_query:
    for package in rpm_query:
        print(f"{package['name']}-{package['version']}: {package['size']:,.0f}")
```

I used a Python feature called ['named arguments'](https://trstringer.com/python-named-arguments/), which makes using the class much easier.

What if you are happy with the default arguments? Not a problem:

```python
with QueryHelper() as rpm_query:
    for package in rpm_query:
        print(f"{package['name']}-{package['version']}: {package['size']:,.0f}")
```

Now we can see how it was implemented:

* [The code](https://github.com/josevnz/rpm_query/blob/main/reporter/rpm_query.py) that imports the RPM is in a try/except clause because it is possible that the RPM is not installed. So if it fails, it does so gracefully, explaining that rpm needs to be installed.
* The `__get__` function takes care of return the results sorted or 'as-is'. We pass a reference to this function to the code that queries the database
* The customization magic happens in the constructor of the QueryHelper class, with [named parameters](https://www.python.org/dev/peps/pep-3102/).
* After that, the code returns database transactions in the ```QueryHelper.__enter__``` method.

```python
"""
Wrapper around RPM database
"""
import sys
from typing import Any

try:
    import rpm
except ModuleNotFoundError:
    print((
        "You must install the following package:\n"
        "sudo dnf install -y python3-rpm\n"
        "'rpm' doesn't come as a pip but as a system dependency.\n"
    ), file=sys.stderr)
    raise


def __get__(is_sorted: bool, dbMatch: Any) -> Any:
    """
    If is_sorted is true then sort the results by item size in bytes, otherwise
    return 'as-is'
    :param is_sorted:
    :param dbMatch:
    :return:
    """
    if is_sorted:
        return sorted(
            dbMatch,
            key=lambda item: item['size'], reverse=True)
    return dbMatch


class QueryHelper:
    MAX_NUMBER_OF_RESULTS = 10_000

    def __init__(self, *, limit: int = MAX_NUMBER_OF_RESULTS, name: str = None, sorted_val: bool = True):
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
            if count >= self.limit:
                break
            yield package
            count += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ts.closeDB()
```

A few things to notice:

* We can reuse this search logic not just on our CLI application but also on future GUI, REST services because functionality lives on a well defined unit (data + actions)
* Did you saw how I 'hinted' the interpreter about the types of the arguments in the constructor (like limit: int is an integer)? This helps IDE like Pycharm a lot, so they can provide auto-completion for you and your users. Python doesn't require it but ***it is as good practice***.
* Some times is good to provide default values to your parameters. That can make your class easier to use if the developer decides not to override the defaults (makes your argument 'optional').
* It is also a good practice to document your methods, even briefly. IDE can show you this detail when you are using the methods,

Will cover unit testing next.

# Unit testing with unittest

*How good is this code without testing*? 

You definitely want to automate the testing of your code. Unit testing is different than other types of testing. Overall, it makes your application more robust because it ensures the smallest components of your application behave correctly (and it works better if you [do it after every change](https://martinfowler.com/articles/continuousIntegration.html) in your code)

In this case, python [unittest](https://docs.python.org/3/library/unittest.html) is nothing more than a class automates proving if a function behaves correctly.

## What is a [good unit test](https://www.artofunittesting.com/)?
* It is small (if a method is testing more than one feature it means it should be split into more tests)
* It is self contained. Ideally should not have external dependencies like databases or application servers. Sometimes you can replace those dependencies with [Mock objects](https://docs.python.org/3/library/unittest.mock.html) that can mimic a part of the system and even allow you to simulate failures.
* It is repeatable. The result of running your test should be the same. For that you maye need to clean before and after running a test ([setUp(), tearDown()](https://docs.python.org/3/library/unittest.html#unittest.TestCase.setUp))

I wrote a [unit test](https://github.com/josevnz/rpm_query/blob/main/tests/test_rpm_query.py) for the `reporter.rpm_query.QueryHelper` class:
* The code has several assertions that must be true in order to pass the each test case.
* I do not use Mock objects because the RPM framework is so ingrained into Fedora/ RedHat it is guaranteed the real database will be there. Also the tests are non-destructive.

```python
"""
Unit tests for the QueryHelper class
How to write unit tests: https://docs.python.org/3/library/unittest.html
"""
import os
import unittest
from reporter.rpm_query import QueryHelper

DEBUG = True if os.getenv("DEBUG_RPM_QUERY") else False


class QueryHelperTestCase(unittest.TestCase):

    def test_default(self):
        with QueryHelper() as rpmquery:
            for package in rpmquery:
                self.assertIn('name', package, "Could not get 'name' in package?")

    def test_get_unsorted_counted_packages(self):
        """
        Test retrieval or unsorted counted packages
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

I strongly recommend you read [official unittest documentation](https://docs.python.org/3/library/unittest.html) for more details, as there's so much more unit testing than this simple code, like [mock testing](https://docs.python.org/3/library/unittest.mock.html), which is particularly useful for complex system dependency scenarios.


# Making the script more usable with Argparse

We can write a small CLI using the `QueryHelper` class created earlier and to make it easier to customize we use [argparse](https://docs.python.org/3/library/argparse.html).

Argparse allows you to do the following:
* Validate user input and restrict number of options. For example to check if the number of results is a non negative number I wrote a type 'validator' on the repoter/__init__.py module (__I could have done it into the class constructor__ but I wanted to show you this feature. You can use it to add extra logic not present in the original code):
```python
def __is_valid_limit__(limit: str) -> int:
    try:
        int_limit = int(limit)
        if int_limit <= 0:
            raise ValueError(f"Invalid limit!: {limit}")
        return int_limit
    except ValueError:
        raise
```
* Combine multiple options to make your program easier to use. You can even mark some required if needed.
* Provide contextualized help on the program usage (help=, --help flag)

Using this class to query the RPM database becomes very easy by parsing the options and then calling ```QueryHelper```:

```python
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

So how does the output look now? Let's ask for all the RPMs you have installed, sorted, and limited to the first 20 entries:

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

# What you've learned

This has been a lot of information, and here's a reminder of what I covered:

* Write modules and clases to interact with the RPM database. This article barely scratches the surface of [all the things](https://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-rpm-programming-python.html) you can do with the API.
* Automatically test small pieces of your application with unittest.
* Learn how to use [Argparse](https://opensource.com/article/21/7/argument-parsing-python-argparse) to make your application easier to use.

