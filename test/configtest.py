#!/usr/bin/python2.7 -B

import unittest
import subprocess

"""
  Testing bing reward with configuration files below
"""
class TestBing(unittest.TestCase):
  def test_assert(self):
      cmd = "ls config.xml"
      cmds = cmd.split()
      status = subprocess.check_call(cmds)
      self.assertEqual(status, 0, "no config.xml file")
  def test_configfile(self):
      cmd = "./main.py -f config.xml"
      cmds = cmd.split()
      status = subprocess.check_call(cmds)
      self.assertEqual(status, 0, "fail to run config.xml")

if __name__ == '__main__':
  unittest.main(verbosity=2)
