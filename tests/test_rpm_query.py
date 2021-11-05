"""
Unit tests for the QueryHelper class
How to write unit tests: https://docs.python.org/3/library/unittest.html
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
