#!/usr/bin/env python
"""
# rpmq_tkinter.py - A simple CLI to query the sizes of RPM on your system
This example is more complex because:
 * Uses callbacks (commands) to update the GUI and also deals
 * Deals with placement of components using a frame with Grid and a flow layout
Author: Jose Vicente Nunez
"""
import argparse
import textwrap
from tkinter import *
from tkinter.ttk import *
from reporter import __is_valid_limit__
from reporter.rpm_query import QueryHelper


def __initial__search__(*, window: Tk, name: str, limit: int, sort: bool, table: Treeview) -> NONE:
    """
    Populate the table with an initial search using CLI args
    :param window:
    :param name:
    :param limit:
    :param sort:
    :param table:
    :return:
    """
    with QueryHelper(name=name, limit=limit, sorted_val=sort) as rpm_query:
        row_id = 0
        for package in rpm_query:
            package_name = f"{package['name']}-{package['version']}"
            package_size = f"{package['size']:,.0f}"
            table.insert(
                parent='',
                index='end',
                iid=row_id,
                text='',
                values=(package_name, package_size)
            )
            window.update()  # Update the UI as soon we get results
            row_id += 1


def __create_table__(main_w: Tk) -> Treeview:
    """
    * Create a table using a tree component, with scrolls on both sides (vertical, horizontal)
    * Let the UI 'pack' or arrange the components, not using a grid here
    * The table will react to the components actions and values defined on the filtering components.
    :param main_w
    """
    scroll_y = Scrollbar(main_w)
    scroll_y.pack(side=RIGHT, fill=Y)
    scroll_x = Scrollbar(main_w, orient='horizontal')
    scroll_x.pack(side=BOTTOM, fill=X)
    tree = Treeview(main_w, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    tree.pack()
    scroll_y.config(command=tree.yview)
    scroll_x.config(command=tree.xview)
    tree['columns'] = ('package_name', 'package_size')
    tree.column("#0", width=0, stretch=NO)
    tree.column("package_name", anchor=CENTER, width=500)
    tree.column("package_size", anchor=CENTER, width=100)
    tree.heading("#0", text="", anchor=CENTER)
    tree.heading("package_name", text="Name", anchor=CENTER)
    tree.heading("package_size", text="Size (bytes)", anchor=CENTER)
    return tree


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


def __reset_command__() -> None:
    """
    Callback to reset the UI form filters
    Doesn't trigger a new search. This is on purpose!
    :return:
    """
    query_v.set(args.name)
    limit_v.set(args.limit)
    sort_v.set(args.sort)


def __ui_search__() -> None:
    """
    Re-do a search using UI filter settings
    :return:
    """
    for i in results_tbl.get_children():
        results_tbl.delete(i)
        win.update()
    __initial__search__(
        window=win, name=query_v.get(), limit=limit_v.get(), sort=sort_v.get(), table=results_tbl)


def test(arg):
    print(arg)


if __name__ == "__main__":
    args = __cli_args__()
    win = Tk()
    win.title("RPM Search results")
    # Search frame with filtering options. Force placement using a grid
    search_f = LabelFrame(text='Search options:', labelanchor=N, relief=FLAT, padding=1)
    query_v = StringVar(value=args.name)
    query_e = Entry(search_f, textvariable=query_v, width=25)
    limit_v = IntVar(value=args.limit)
    limit_l = Label(search_f, text="Limit results: ")
    query_l = Spinbox(
        search_f,
        from_=1,  # from_ is not a typo and is annoying!
        to=QueryHelper.MAX_NUMBER_OF_RESULTS,
        textvariable=limit_v
    )
    sort_v = BooleanVar(value=args.sort)
    sort_c = Checkbutton(search_f, text="Sort by size", variable=sort_v)
    search_btn = Button(search_f, text="Search RPM", command=__ui_search__)
    clear_btn = Button(search_f, text="Reset filters", command=__reset_command__)
    package_l = Label(search_f, text="Package name: ").grid(row=0, column=0, sticky=W)
    search_f.grid(column=0, row=0, columnspan=3, rowspan=4)
    limit_l.grid(row=1, column=0, sticky=W)
    query_e.grid(row=0, column=1, columnspan=2, sticky=W)
    query_l.grid(row=1, column=1, columnspan=1, sticky=W)
    sort_c.grid(row=2, column=0, columnspan=1, sticky=W)
    search_btn.grid(row=3, column=0, columnspan=2, sticky=W)
    clear_btn.grid(row=3, column=1, columnspan=1, sticky=W)
    search_f.pack(side=TOP, fill=BOTH, expand=1)
    results_tbl = __create_table__(win)
    results_tbl.pack(side=BOTTOM, fill=BOTH, expand=1)
    __initial__search__(
        window=win, name=query_v.get(), limit=limit_v.get(), sort=sort_v.get(), table=results_tbl)
    win.mainloop()
