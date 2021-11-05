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
    Get the package results and the total number of results found
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
        limit = max(self.limit, self.MAX_NUMBER_OF_RESULTS)
        for package in __get__(self.sorted, db):
            if count < limit:
                count += 1
            else:
                break
            yield package

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ts.closeDB()
