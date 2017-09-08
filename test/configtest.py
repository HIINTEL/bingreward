#!/usr/bin/env python -B

import unittest
import subprocess
import sys
import os
import main

"""
Add pkg and parent directory for mock testing of authentication errors
"""
from mock import patch, Mock
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "pkg"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from config import AccountKey, BingRewardsReportItem, Config, ConfigError
import mock

import helpers
import bingCommon
import bingHistory
import bingFlyoutParser as bfp


"""
  Test xml is correctly stored
"""


class TestConfig(unittest.TestCase):
    fsock = None
    mockdate = "2017-09-06 00:44:47.7"


    def _redirectOut(self):
        self.fsock = open('out.log', 'a+')
        sys.stdout = self.fsock

    def tearDown(self):
        if self.fsock is not None:
            self.fsock.close()
            self.fsock = None
            sys.stdout = sys.__stdout__
    def setUp(self):
        self.config = Config()
        self.configXMLString = """
    <configuration>
        <general
            betweenQueriesInterval="12.271"
            betweenQueriesSalt="5.7"
            betweenAccountsInterval="404.1"
            betweenAccountsSalt="40.52" />

        <accounts>
            <account type="Live" disabled="false">
                <login>ms@ps.com</login>
                <password>zzz</password>
                <ua_desktop>Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10136</ua_desktop>
                <ua_mobile>mozilla/5.0 (iphone; cpu iphone os 7_0_2 like mac os x) applewebkit/537.51.1 (khtml, like gecko) version/7.0 mobile/11a501 safari/9537.53</ua_mobile>
            </account>
        </accounts>

        <events>
            <onError>
                <retry interval="5" salt="3.5" count="1" />
                <notify cmd="echo error %a %p %r %l %i" />
            </onError>
            <onComplete>
                <retry if="%p lt 16" interval="5" salt="3.5" count="1" />
                <notify if="%l gt 3000" cmd="echo complete %a %p %r %P %l %i" />
                <notify if="%p ne 16" cmd="echo complete %a %p %r %P %l %i" />
                <notify if="%P gt 475" cmd="echo complete %a %p %r %P %l %i" />

                <account ref="Live_ms@ps.com">
                    <retry if="%p lt 31" interval="5" salt="3.5" count="1" />
                    <notify if="%l gt 10000" cmd="echo complete %a %p %r %P %l %i" />
                    <notify if="%p ne 31" cmd="echo complete %a %p %r %P %l %i" />
                    <notify if="%P gt 475" cmd="echo complete %a %p %r %P %l %i" />
                </account>

            </onComplete>
            <onScriptComplete>
                <notify cmd="echo" />
            </onScriptComplete>
            <onScriptFailure>
                <notify cmd="echo" />
            </onScriptFailure>
        </events>
        <queries generator="googleTrends" />
    </configuration>
            """
        self.config.parseFromString(self.configXMLString)
        self.configFBXML = """
    <configuration>
        <general
            betweenQueriesInterval="12.271"
            betweenQueriesSalt="5.7"
            betweenAccountsInterval="404.1"
            betweenAccountsSalt="40.52" />

        <accounts>
            <account type="Facebook" disabled="false">
                <login>john.smith@gmail.com</login>
                <password>xxx</password>
            </account>
        </accounts>

        <events>
            <onError>
                <retry interval="5" salt="3.5" count="1" />
                <notify cmd="echo error %a %p %r %l %i" />
            </onError>
            <onComplete>
                <retry if="%p lt 16" interval="5" salt="3.5" count="1" />
                <notify if="%l gt 3000" cmd="echo complete %a %p %r %P %l %i" />
                <notify if="%p ne 16" cmd="echo complete %a %p %r %P %l %i" />
                <notify if="%P gt 475" cmd="echo complete %a %p %r %P %l %i" />

                <account ref="Facebook_john.smith@gmail.com">
                    <retry if="%p lt 31" interval="5" salt="3.5" count="1" />
                    <notify if="%l gt 10000" cmd="echo complete %a %p %r %P %l %i" />
                    <notify if="%p ne 31" cmd="echo complete %a %p %r %P %l %i" />
                    <notify if="%P gt 475" cmd="echo complete %a %p %r %P %l %i" />
                </account>

            </onComplete>
            <onScriptComplete>
                <notify cmd="./mail.sh" />
            </onScriptComplete>
            <onScriptFailure>
                <notify cmd="./onScriptFailure.sh" />
            </onScriptFailure>
        </events>
        <queries generator="wikipedia" />
    </configuration>
            """

    @patch('helpers.getResponseBody')
    @patch('time.sleep')
    def test_auth(self, timemock, helpmock):
        """
        test authentication decoding error
        :return:
        """
        helpmock.return_value = '"WindowsLiveId":""     "WindowsLiveId":""'
        timemock.return_value = ''

        self._redirectOut()
        main.run(self.config)
        output = ""
        for line in self.fsock.readlines():
            print line
            output += line
        self.assertRegexpMatches(output, "", "should have not error,\n" + output)

    @patch('helpers.getResponseBody')
    @patch('time.sleep')
    def test_fail_auth(self, timemock, helpmock):
        """
        test authentication decoding error
        :return:
        """
        helpmock.return_value = ''
        timemock.return_value = ''
        self.assertRaisesRegexp(ValueError, "substring not found", main.run, self.config)

    def test_timestamp(self):
        """
         test getlogtime
         :return:
         """
        stamp = helpers.getLoggingTime()
        self.assertRegexpMatches(stamp, "\d{4}-\d{2}-\d{2}", "should have time stamp,\n" + stamp)

    def test_createdir(self):
        """
         test dir with file
         :return:
         """
        helpers.createResultsDir("none")
        self.assertEqual(os.path.isdir(helpers.RESULTS_DIR), True, "missing directory " + helpers.RESULTS_DIR)

    def test_dump_none(self):
        """
         test none page to a file
         :return:
         """
        self.assertRaisesRegexp(TypeError, "None", helpers.dumpErrorPage, None)

    def test_dump(self):
        """
         test dump page to a file
         :return:
         """
        filename = helpers.dumpErrorPage(self.mockdate)
        output = ""
        with open("result/" + filename, "r") as fd:
            output += fd.readline()
        self.assertRegexpMatches(output, "\d{4}-\d{2}-\d{2}", "should have time stamp,\n" + output)

    def test_errorontext(self):
        """
        test exception from helper's errorOnText
        :return:
        """
        err = 'Authentication has not been passed: Invalid password'

        # not found so no assertion
        output = helpers.errorOnText("", 'That password is incorrect.', err)

        # should raise if it sees an assertion
        self.assertRaisesRegexp(helpers.BingAccountError, "Invalid", helpers.errorOnText, 'That password is incorrect.',
                                'That password is incorrect.', err)

    def test_node(self):
        """
        test node's children
        :return:
        """
        import xml.etree.ElementTree as ET
        root = ET.fromstring(self.configXMLString)

        node = helpers.getXmlChildNodes(root)
        self.assertIsNotNone(node, "should not be null " + str(node))

    @patch('sys.version_info')
    def test_node_fail(self, mockver):
        sys.version_info = [ 2, 1 ]

        import xml.etree.ElementTree as ET
        root = ET.fromstring(self.configXMLString)

        node = helpers.getXmlChildNodes(root)
        self.assertIsNotNone(node, "should not be null " + str(node))

    def test_accounts(self):
        self.assertIsNotNone(self.config.accounts)
        self.assertEqual(len(self.config.accounts), 1)
        accounts = dict()

        acc = Config.Account()
        acc.accountLogin = "ms@ps.com"
        acc.password = "zzz"
        acc.accountType = "Live"
        acc.disabled = False
        acc.ua_desktop = "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10136"
        acc.ua_mobile = "mozilla/5.0 (iphone; cpu iphone os 7_0_2 like mac os x) applewebkit/537.51.1 (khtml, like gecko) version/7.0 mobile/11a501 safari/9537.53"
        accounts[acc.getRef()] = acc

        self.assertEqual(accounts, self.config.accounts)

    def test_facebook(self):
        """
        Should throw Not supported value for facebook parameters
        """
        self.config.parseFromString(self.configFBXML)
        self.assertRaisesRegexp(ValueError, "Not supported", main.run, self.config)

    def test_history_parse(self):
        """
        test history parsing
        :return:
        """
        self.assertRaisesRegexp(TypeError, "None", bingHistory.parse, None)

        output = bingHistory.parse("")
        self.assertIsNotNone(output, "missing output " + str(output))

        page = '<div id="results_area"></div id="results_area"><div id="sidebar">'
        output = bingHistory.parse(page)
        self.assertIsNotNone(output, "missing output " + str(output))

        page += '<ul class="sh_dayul"></ul class="sh_dayul">'
        output = bingHistory.parse(page)
        self.assertIsNotNone(output, "missing output " + str(output))

    def test_history_today(self):
        """
        test history parsing
        :return:
        """
        output = bingHistory.getBingHistoryTodayURL()

        self.assertRegexpMatches(output, "https", "missing url " + str(output))

    def test_bfp(self):
        """
        test bfp
        :return:
        """
        newbfp = bfp.Reward()
        self.assertIsNotNone(newbfp.isAchieved(), "should not be None")
        self.assertIsNotNone(newbfp.progressPercentage(), "should not be None")
        page = '<div id="messageContainer"></div id="messageContainer">'
        page += '<div id="bottomContainer">'
        self.assertIsNotNone(bfp.parseFlyoutPage(page, "http://bing"), "should not be None")
        self.assertIsNotNone(newbfp.Type.Action.toStr(newbfp.Type.Action.PASS) , "should not be None")

    def test_rewards(self):
        """
        test rewards object
        :return:
        """
        from bingRewards import BingRewards
        reward = BingRewards(bingCommon.HEADERS, "", self.config)
        self.assertIsNotNone(reward.requestFlyoutPage(), "should not be None")

        # if not login should have not found error
        self.assertRaisesRegexp(ValueError, "not found", reward.getLifetimeCredits)
        self.assertIsNotNone(reward.getRewardsPoints(), "should not be None")

        newbfp = bfp.Reward()

        self.assertRaisesRegexp(TypeError, "not an instance", reward.process, None, True)

        # NONE case
        newbfp.tp = None
        rewards = [ newbfp ]
        self.assertRaisesRegexp(ValueError, "unknown", reward.process, rewards, True)

        # HIT case
        newbfp.tp = mock.Mock()
        newbfp.tp = [ 0, 1, 2, 3, bfp.Reward.Type.Action.HIT ]
        rewards = [ newbfp ]
        self.assertRaisesRegexp(ValueError, "unknown", reward.process, rewards, True)

        # SEARCH case
        newbfp.tp = mock.Mock()
        newbfp.tp = [ 0, 1, 2, 3, bfp.Reward.Type.Action.SEARCH ]
        rewards = [ newbfp ]
        self.assertIsNotNone(reward.process(rewards, True), "should return res")

        self.assertRaisesRegexp(TypeError, "not an instance", reward.printResults, None, True)
        self.assertIsNone(reward.printResults(list(), True), "should return None")
        self.assertRaisesRegexp(TypeError, "reward is not", reward.RewardResult, None)

        self.assertIsNotNone(reward.RewardResult(newbfp), "should return class")

        proxy = mock.Mock()
        proxy.login = True
        proxy.password = "xxx"
        proxy.url = "http://127.0.0.1"
        proxy.protocols = "http"
        self.config.proxy = proxy
        self.assertIsNotNone(BingRewards(bingCommon.HEADERS, "", self.config), "should return class")


"""
  Testing mock library used
"""
mockdir="/usr/local/lib/python2.7/site-packages/mock/tests"
mockdir1="/home/ubuntu/virtualenvs/venv-2.7/lib/python2.7/site-packages"


@unittest.skip("buggy unittest2 and needed some loving")
class TestMock(unittest.TestCase):
    def test_all(self):
        """
        test all mock code using their unittest
        """
        sys.path.append(os.path.join(os.path.dirname(mockdir)))
        sys.path.append(os.path.join(os.path.dirname(mockdir1)))
        try:
            os.chdir(mockdir)
        except:
            os.chdir(mockdir1)

        cmd = "nosetests"
        cmds = cmd.split()
        status = subprocess.check_call(cmds, stderr=subprocess.STDOUT)
        self.assertEqual(status, 0, "failed to execute " + str(status))

if __name__ == '__main__':
    unittest.main(verbosity=3)
