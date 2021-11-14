# rpm_query

This is a simple project that aims:

* How to write a class that can query the contents of the RPM database
* How to package and distribute a python application using setuptools
* How to write nice command line arguments with argparse and rich, tkinter, DearPyGUI

# Local installation

## Pre-requisites
### Install python3-rpm
```shell
sudo dnf install -y python3-rpm
```
### Create a virtual environment with system site packages
```shell
python3 -m venv --system-site-packages ~/virtualenv/rpm_query
. ~/virtualenv/rpm_query/bin/activate
```

All the commands will assume you successfully activated your virtual environment

## Create the editable package

```shell
(rpm_query) [josevnz@dmaf5 rpm_query]$ python setup.py develop
```
Remember when you are done you can remove the development mode:
```shell
python setup.py develop --uninstall
```

## Compiling the package

### Bumping the version

Just change the value of the '__version__' variable in the rpm_query package.

### Wheel package

```shell
(rpm_query) [josevnz@dmaf5 rpm_query]$ python setup.py bdist_wheel
running bdist_wheel
...
```
## Installation

```shell
(rpm_query) [josevnz@dmaf5 rpm_query]$ python setup.py install dist/rpm_query-0.0.1-py3-none-any.whl
```

# Tutorial

There is a 3 part tutorial that explains how and why this code was written. In order:

* [Writing and unit testing an application to query the RPM database with Python](https://github.com/josevnz/rpm_query/blob/main/Writting%20and%20Unit%20testing%20an%20application%20that%20can%20query%20the%20RPM%20database%20with%20Python.md#writting-and-unit-testing-an-application-to-query-the-rpm-database-with-python)
* [Packaging an application to query an RPM database with Python](https://github.com/josevnz/rpm_query/blob/main/Packaging%20an%20application%20that%20can%20query%20the%20RPM%20database%20with%20Python.md)
* [Writing UI applications that can query the RPM database with Python](https://github.com/josevnz/rpm_query/blob/main/Writting%20UI%20applications%20that%20can%20query%20the%20RPM%20database%20with%20Python.md)
