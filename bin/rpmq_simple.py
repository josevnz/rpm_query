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
        for package in rpm_query:
            print(f"{package['name']}-{package['version']}: {package['size']:,.0f}")
