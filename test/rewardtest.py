#!/usr/bin/env python -B

import unittest
import sys
import subprocess
import os

"""
Add pkg and parent directory for mock testing of authentication errors
"""
sys.path.append(os.path.abspath("pkg"))
sys.path.append(os.path.abspath("."))


"""
  Testing bing reward in root dir with configuration files below
"""


class TestBing(unittest.TestCase):

    def setUp(self):
        newpath = os.path.join(os.path.dirname(__file__), "..")
        sys.path.append(newpath)
        os.chdir(newpath)
        
    def test_assert(self):
        cmd = "ls config.xml"
        cmds = cmd.split()
        status = subprocess.check_call(cmds)
        self.assertEqual(status, 0, "no config.xml file")

    def test_configdist(self):
        cmd = "python main.pyc -v -r -f config.xml"
        cmds = cmd.split()
        output = subprocess.check_output(cmds, stderr=subprocess.STDOUT)
        self.assertRegexpMatches(output, "AuthenticationError", "should have seen invalid account auth\n" + output)

    def test_confighelp(self):
        cmd = "python main.pyc -h"
        cmds = cmd.split()
        status = subprocess.check_call(cmds, stderr=subprocess.STDOUT)
        self.assertEqual(status, 0, "failed to execute " + str(status))

    def test_configversion(self):
        cmd = "python main.pyc --version"
        cmds = cmd.split()
        status = subprocess.check_call(cmds, stderr=subprocess.STDOUT)
        self.assertEqual(status, 0, "failed to execute " + str(status))

    def test_configinvalid(self):
        cmd = "coverage run -p main.py --donotexist"
        cmds = cmd.split()
        self.assertRaisesRegexp(subprocess.CalledProcessError, "status 1", subprocess.check_call, cmds, stderr=subprocess.STDOUT)

if __name__ == '__main__': # pragma: no cover
        unittest.main(verbosity=3)