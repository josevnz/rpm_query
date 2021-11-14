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

I explained how to install this code on a [previous tutorial](https://github.com/josevnz/rpm_query/blob/main/Writting%20and%20Unit%20testing%20an%20application%20that%20can%20query%20the%20RPM%20database%20with%20Python.md) and the usage of [virtual environment](https://opensource.com/article/20/10/venv-python), but you can take a shortcut and just do this:

```shell
sudo dnf install -y python3-rpm
git clone git@github.com:josevnz/tutorials.git
cd rpm_query
python3 -m venv --system-site-packages ~/virtualenv/rpm_query
. ~/virtualenv/rpm_query/bin/activate
(rpm_query)$ 
```

# Packaging and installing the distribution

## Why you don't want to use an RPM to package your Python application

Well, there is no short answer for that.

RPM is *great* [if you want to share](https://www.redhat.com/sysadmin/package-linux-applications-rpm) your application with __all__ the users of your system, specially because RPM can install related dependencies for you automatically.

For example, the RPM Python bindings (rpm-python3) is distributed that way, make sense as it is thinly tied to RPM.

In some causes is also a disadvantage:
* You will need root elevated access to install an RPM. If the code is malicious it will take control of your server very easily (that's why [you always check the RPM signatures](https://www.redhat.com/sysadmin/rpm-gpg-verify-packages) and download code from well know sources right?)
* You decide to upgrade an RPM that may be incompatible with older dependent applications. That will prevent an upgrade.
* RPM is not well suited to share 'test' code created during continuous integration, at least in bare-metal deployments. If you create a Docker container that is probably a different story...
* If your Python code has dependencies it is very likely you will also have to package them as RPMS.

## Enter virtual environments and pip + setuptools

How these 3 tools solve the RPM limitations mentioned earlier?:
* [Virtual environment](https://docs.python.org/3/library/venv.html) will allow you to install applications without having elevated permissions
* The application is self-contained to the virtual environment, you can install different versions of the libraries without affecting the whole system
* It is very easy to integrate a virtual environment with continuous integration and unit testing. After the tests pass, the environment can be recycled
* [setuptools](https://packaging.python.org/tutorials/installing-packages/) solves the problem of packaging your application in a nice directory structure, and making your scripts and libraries vailable to users.
* setuptools also deals with the issue of keeping track of your dependencies with proper version check, to make the build process repeatable.
* setuptools works with [pip](https://pip.pypa.io/en/stable/), the Python package manager
* Best part is that both virtual environments and setuptools have excellent support in IDE like Pycharm or VSCode.

# Working with setuptools
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

Things to note:
* I stored the version on the reporter/__init__.py package module in order to share
with other parts of the application, not just setuptools. Also used a [semantic version schema](https://packaging.python.org/guides/distributing-packages-using-setuptools/#semantic-versioning-preferred) naming convention.
* Readme of the module is also stored on an external file. This makes it editing the file much easier without worrying about size or breaking the python syntax.
* [Classifiers](https://pypi.org/pypi?%3Aaction=list_classifiers) make it easier to see the intent of your application
* You can define packaging dependencies (setup_requires) and runtime dependencies (install_requires)
* I need the wheel package as I want to create a '[pre-compiled](https://packaging.python.org/glossary/#term-Wheel)' distribution that is faster to install than other modes.

## How to deploy while you are testing

You don't need to package and deploy your application in full mode. setuptools has a very convenient mode that will install dependencies and will let you keep editing your code while testing, called the 'develop' mode:

```shell
(rpm_query)$ python setup.py develop
```

This will create special symbolic links that will put your scripts (remember that section in setup.py?) into your path.

By the way, once you are done testing you can remove development mode:

```shell
(rpm_query)$ python setup.py develop --uninstall
```

The official documentation recommends migrating from a `setup.py` configuration to `setup.cfg`, but I decided to use `setup.py` because it's what I'm familiar with.

## Creating a pre-compiled distribution

It is easy as typing this:

```shell
(rpm_query)$ python setup.py bdist_wheel
running bdist_wheel
...  # Omitted output
(rpm_query)$ ls dist/
rpm_query-0.0.1-py3-none-any.whl
```

Then you can install it on the same machine or a new machine, in a virtual environment:

```shell
(rpm_query)$ python setup.py install \
dist/rpm_query-1.0.0-py3-none-any.whl
```

What if you want to share your PIP with other users? You could copy the wheel file on the other machines and have your users install it, but there is a better way

# Uploading your application to a repository with twine

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

