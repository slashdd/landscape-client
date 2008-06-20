import unittest

from landscape.tests.helpers import LandscapeTest

from landscape.lib.process import get_uptime, calculate_pcpu


class UptimeTest(LandscapeTest):
    """Test for parsing /proc/uptime data."""

    def test_valid_uptime_file(self):
        """Test ensures that we can read a valid /proc/uptime file."""
        proc_file = self.make_path("17608.24 16179.25")
        self.assertEquals("%0.2f" % get_uptime(proc_file),
                          "17608.24")

class CalculatePCPUTest(unittest.TestCase):

    def test_calculate_pcpu(self):
        self.assertEquals(calculate_pcpu(40000, 10000, 1000, 50000, 100), 10.0)
