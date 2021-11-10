#!/usr/bin/env python
"""
# rpmq_rich.py - A simple CLI to query the sizes of RPM on your system
Author: Jose Vicente Nunez
"""
import argparse
import textwrap
from reporter import __is_valid_limit__
from reporter.rpm_query import QueryHelper
from rich.table import Table
from rich.progress import Progress

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
        rpm_table = Table(title="RPM package name and sizes")
        rpm_table.add_column("Name", justify="right", style="cyan", no_wrap=True)
        rpm_table.add_column("Size (bytes)", justify="right", style="green")
        with Progress(transient=True) as progress:
            querying_task = progress.add_task("[red]RPM query...", start=False)
            current = 0
            for package in rpm_query:
                if current >= args.limit:
                    break
                rpm_table.add_row(f"{package['name']}-{package['version']}", f"{package['size']:,.0f}")
                progress.console.print(f"[yellow]Processed package: [green]{package['name']}-{package['version']}")
                current += 1
            progress.update(querying_task, advance=100.0)
            progress.console.print(rpm_table)
