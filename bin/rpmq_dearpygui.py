#!/usr/bin/env python
"""
# rpmq_dearpygui.py - A simple CLI to query the sizes of RPM on your system
Author: Jose Vicente Nunez
"""
import argparse
import textwrap

from reporter import __is_valid_limit__
from reporter.rpm_query import QueryHelper
import dearpygui.dearpygui as dpg

TABLE_TAG = "query_table"
MAIN_WINDOW_TAG = "main_window"


def __cli_args__() -> argparse.Namespace:
    """
    Command line argument parsing
    :return:
    """
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
        default="",
        help="You can filter by a package name."
    )
    parser.add_argument(
        "--sort",
        action="store_false",
        help="Sorted results are enabled bu default, but you fan turn it off"
    )
    return parser.parse_args()


def __reset_form__():
    dpg.set_value("package_name", args.name)
    dpg.set_value("limit_text", args.limit)
    dpg.set_value("sort_by_size", args.sort)


def __run_initial_query__(
        *,
        package: str,
        limit: int,
        sorted_elem: bool
) -> None:
    """
    Need to ensure the table gets removed.
    See issue: https://github.com/hoffstadt/DearPyGui/issues/1350
    :return:
    """
    if dpg.does_alias_exist(TABLE_TAG):
        dpg.delete_item(TABLE_TAG, children_only=False)
    if dpg.does_alias_exist(TABLE_TAG):
        dpg.remove_alias(TABLE_TAG)
    with dpg.table(header_row=True, resizable=True, tag=TABLE_TAG, parent=MAIN_WINDOW_TAG):
        dpg.add_table_column(label="Name", parent=TABLE_TAG)
        dpg.add_table_column(label="Size (bytes)", default_sort=True, parent=TABLE_TAG)
        with QueryHelper(
                name=package,
                limit=limit,
                sorted_val=sorted_elem
        ) as rpm_query:
            for package in rpm_query:
                with dpg.table_row(parent=TABLE_TAG):
                    dpg.add_text(f"{package['name']}-{package['version']}")
                    dpg.add_text(f"{package['size']:,.0f}")


def __run__query__() -> None:
    __run_initial_query__(
        package=dpg.get_value("package_name"),
        limit=dpg.get_value("limit_text"),
        sorted_elem=dpg.get_value("sort_by_size")
    )


if __name__ == "__main__":

    args = __cli_args__()

    dpg.create_context()
    with dpg.window(label="RPM Search results", tag=MAIN_WINDOW_TAG):
        dpg.add_text("Run a new search")
        dpg.add_input_text(label="Package name", tag="package_name", default_value=args.name)
        with dpg.tooltip("package_name"):
            dpg.add_text("Leave empty to search all packages")
        dpg.add_checkbox(label="Sort by size", tag="sort_by_size", default_value=args.sort)
        dpg.add_slider_int(
            label="Limit",
            default_value=args.limit,
            tag="limit_text",
            max_value=QueryHelper.MAX_NUMBER_OF_RESULTS
        )
        with dpg.tooltip("limit_text"):
            dpg.add_text(f"Limit to {QueryHelper.MAX_NUMBER_OF_RESULTS} number of results")
        with dpg.group(horizontal=True):
            dpg.add_button(label="Search", tag="search", callback=__run__query__)
            with dpg.tooltip("search"):
                dpg.add_text("Click here to search RPM")
            dpg.add_button(label="Reset", tag="reset", callback=__reset_form__)
            with dpg.tooltip("reset"):
                dpg.add_text("Reset search filters")
        __run_initial_query__(
            package=args.name,
            limit=args.limit,
            sorted_elem=args.sort
        )

    dpg.create_viewport(title='RPM Quick query tool')
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
