#!/usr/bin/env python -B

import unittest
import sys
import subprocess
import os

"""
Add pkg and parent directory for mock testing of authentication errors
"""
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "pkg"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

"""
  Testing bing reward in root dir with configuration files below
"""
class TestBing(unittest.TestCase):
    def test_assert(self):
      cmd = "ls config.xml"
      cmds = cmd.split()
      status = subprocess.check_call(cmds)
      self.assertEqual(status, 0, "no config.xml file")

    def test_configdist(self):
      cmd = "./main.py -f config.xml.dist"
      cmds = cmd.split()
      output = subprocess.check_output(cmds, stderr=subprocess.STDOUT)
      self.assertRegexpMatches(output, "AuthenticationError", "should have seen invalid account auth\n" + output)

    def test_configxml(self):
      cmd = "./main.py -f config.xml"
      cmds = cmd.split()
      status = subprocess.check_call(cmds, stderr=subprocess.STDOUT)
      self.assertEqual(status, 0, "failed to execute " + str(status))

if __name__ == '__main__':
  unittest.main(verbosity=3)
