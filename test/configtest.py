#!/usr/bin/env python -B

import unittest
import subprocess
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "pkg"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import main
import urllib2

"""
Add pkg and parent directory for mock testing of authentication errors
"""
from mock import patch, Mock

from config import AccountKey, BingRewardsReportItem, Config, ConfigError
import mock

import helpers
import bingCommon
import bingHistory
import bingFlyoutParser as bfp
import bingAuth
from config import Config
from config import BingRewardsReportItem
from eventsProcessor import EventsProcessor
from bingRewards import BingRewards

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "pkg", "queryGenerators"))
import googleTrends
import wikipedia

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
        <proxy protocols="http"
               url="www.bing.com"
               login="xxx"
               password="yyy" />
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

    def test_history(self):
        """
        test history parsing
        :return:
        """
        self.assertRaisesRegexp(TypeError, "None", bingHistory.parse, None)

        output = bingHistory.parse("")
        self.assertIsNotNone(output, "missing output " + str(output))

        page = '<span class="query_t">'
        page += '<div id="results_area"></div><div id="sidebar"></div>'
        output = bingHistory.parse(page)
        self.assertIsNotNone(output, "missing output " + str(output))

        page = '<span class="sh_item_qu_query">'
        page += '<ul class="sh_dayul"></ul>'
        page += ' value == 0'
        page += '</span>'
        output = bingHistory.parse(page)
        self.assertIsNotNone(output, "missing output " + str(output))

        page = '<ul class="sh_dayul"> </ul>'
        output = bingHistory.parse(page)
        self.assertIsNotNone(output, "missing output " + str(output))

        output = bingHistory.getBingHistoryTodayURL()
        self.assertRegexpMatches(output, "https", "missing url " + str(output))

    @patch('helpers.getResponseBody', return_value = '"WindowsLiveId":""     "WindowsLiveId":""')
    @patch('time.sleep', return_value = '')
    def test_auth(self, timemock, helpmock):
        """
        test authentication decoding error
        :return:
        """
        self._redirectOut()
        main.run(self.config)
        output = ""
        output.join(self.fsock.readlines())
        self.assertRegexpMatches(output, "", "should have not error,\n" + output)

        form = bingAuth.HTMLFormInputsParser()
        self.assertIsNone(form.handle_starttag("input", "name"), "should not be None")
        self.assertIsNone(form.handle_starttag("input", [["name", "1"] , ["value", "2"]]), "should not be None")

    @patch('urllib2.Request', return_value = "")
    @patch('helpers.getResponseBody', return_value = "")
    @patch('urllib2.Request.add_header', return_value = urllib2.Request(bingCommon.BING_URL, bingCommon.HEADERS))
    def test_auth_url(self, headermock, helpmock, urlmock):
        """
        test auth class
        :param headermock:
        :param helpmock:
        :param urlmock:
        :return:
        """
        self.assertRaisesRegexp(TypeError, "opener is not", bingAuth.BingAuth, bingCommon.HEADERS, None)

        auth = bingAuth.BingAuth(bingCommon.HEADERS, urllib2.OpenerDirector())
        self.assertIsNotNone(auth, "should return class")
        self.assertRaisesRegexp(bingAuth.AuthenticationError, "Error", auth.authenticate, "does_not_exist", "xxx", "yyy")

    @patch('helpers.getResponseBody', return_value = '')
    @patch('time.sleep', return_value = '')
    def test_auth_fail(self, timemock, helpmock):
        """
        test authentication decoding error
        :return:
        """
        self.assertRaisesRegexp(ValueError, "substring not found", main.run, self.config)

    def test_bfp(self):
        """
        test bfp
        :return:
        """
        newbfp = bfp.Reward()
        self.assertIsNotNone(newbfp.isAchieved(), "should not be None")
        newbfp.progressCurrent = 1
        newbfp.progressMax = 100
        self.assertIsNotNone(newbfp.progressPercentage(), "should not be None")
        page = '<div id="messageContainer"></div>'
        page += '<div id="bottomContainer"></div>'
        self.assertIsNotNone(bfp.parseFlyoutPage(page, "http://bing"), "should not be None")
        self.assertIsNotNone(newbfp.Type.Action.toStr(newbfp.Type.Action.PASS) , "should not be None")

    def test_config(self):
        """
        test config.py
        :return:
        """
        configobj = Config()
        self.assertIsNotNone(configobj, "should return class")
        self.assertIsNotNone(Config.General(), "should return class")
        self.assertIsNotNone(ConfigError("ok"), "should return exception")
        self.assertIsNotNone(Config.Proxy(), "should return class")

        self.assertIsNotNone(Config.EventAccount(), "should return class")
        self.assertIsNotNone(Config.Event.Notify(), "should return class")
        ifs = Config.Event.IfStatement()
        ifs.op = lambda x, y: x
        ifs.lhs = lambda x : x
        ifs.rhs = "b"
        self.assertIsNotNone(str(ifs), "should return class")
        self.assertRaisesRegexp(ValueError, "None", ifs.evaluate, None)
        self.assertRaisesRegexp(TypeError, "is not of", ifs.evaluate, [])
        self.assertIsNotNone(ifs.evaluate(BingRewardsReportItem()))

        spec = Config.Event.Specifier()
        self.assertIsNotNone(spec, "should return class")
        self.assertRaisesRegexp(ValueError, "is None", spec.evaluate, None, BingRewardsReportItem())
        self.assertRaisesRegexp(TypeError, "list", spec.evaluate, [], BingRewardsReportItem())
        self.assertIsNotNone(spec.evaluate("%a", BingRewardsReportItem()), "should return string")

        dist = os.path.join(os.path.dirname(__file__), "..", "config.xml.dist")
        self.assertIsNone(configobj.parseFromFile(dist), "should be none")

    def test_event(self):
        """
        test event
        :return:
        """
        self.assertIsNone(EventsProcessor.onScriptFailure(self.config, Exception()), "should be none")
        self.assertIsNone(EventsProcessor.onScriptComplete(self.config), "should be none")

    def test_event_getEvent_returnsEvent(self):
        """
        test onScriptFailure using echo from xml config string
        :return:
        """
        event = self.config.getEvent(Config.Event.onScriptFailure)
        self.assertIsNotNone(event)
        self.assertTrue(len(event.notifies) == 1)
        self.assertEqual(event.notifies[0].cmd, "echo")

    def test_event_getEvent_returnsNoneIfEventDoesntExist(self):
        """
        test no event call does not exist
        :return:
        """
        self.assertIsNone(self.config.getEvent("does_not_exist"))
        self.assertRaisesRegexp(ValueError, "None", self.config.getEvent, None)

    def test_query(self):
        """
        test google queryGenerator
        :return:
        """
        q = googleTrends.queryGenerator(1)
        q.br = None
        q.unusedQueries = set()
        self.assertIsNotNone(q.generateQueries(10, set()))

        self.assertRaisesRegexp(ValueError, "is not", wikipedia.queryGenerator, None)
        useragents = bingCommon.UserAgents().generate(self.config.accounts)
        b = BingRewards(bingCommon.HEADERS, useragents, self.config)
        q = wikipedia.queryGenerator(b)
        q.br = None
        q.unusedQueries = set()
        self.assertIsNotNone(q.generateQueries(10, set()))

    @patch('bingFlyoutParser.Reward.progressPercentage', return_value = "100")
    @patch('helpers.getResponseBody')
    def test_rewards_search(self, helpmock, permock):
        """
        Search string
        :param helpmock:
        :param permock:
        :return:
        """
        page = '"WindowsLiveId":""     "WindowsLiveId":"" '
        page += 'action="0" value="0" '
        page += 'value= "0" NAP value="0" '
        page += 'ANON value="0" '
        page += 'id="t" value="0" '
        page += '<div> 999 livetime points</div> '
        page += "t.innerHTML='100'"
        page += '<div id="b_content">'
        page += '<div id="content">'
        page += 'IG:"100"'
        page += "http://www.bing.com/fd/ls/GLinkPing.aspx"

        helpmock.return_value = page

        useragents = bingCommon.UserAgents().generate(self.config.accounts)
        reward = BingRewards(bingCommon.HEADERS, useragents, self.config)
        newbfp = bfp.Reward()
        reward.RewardResult(newbfp)

        newbfp.progressCurrent = 1
        newbfp.progressMax = 100
        newbfp.description = "Up to 10 points today, 10 points per search"

        newbfp.isDone = False

        # SEARCH case, PC, Mobile, Earn
        for data in [
            newbfp.Type.SEARCH_MOBILE        ,
            newbfp.Type.SEARCH_PC            ,
            newbfp.Type.YOUR_GOAL            ,
            newbfp.Type.MAINTAIN_GOLD        ,
            newbfp.Type.REFER_A_FRIEND       ,
            newbfp.Type.SEND_A_TWEET         ,
            newbfp.Type.RE_EARNED_CREDITS    ,
            newbfp.Type.COMPLETED            ,
            newbfp.Type.SILVER_STATUS        ,
            newbfp.Type.INVITE_FRIENDS       ,
            newbfp.Type.EARN_MORE_CREDITS    ,
            newbfp.Type.SEARCH_AND_EARN      ,
            newbfp.Type.THURSDAY_BONUS       ,
            newbfp.Type.RE_QUIZ ]:
            newbfp.tp = data
            newbfp.url = "www.espn.com"

            newbfp.Type = bfp.Reward.Type.Action.SEARCH
            rewards = [ newbfp ]
            newbfp.isAchieved = lambda : data is 0
            self.assertIsNotNone(reward.process(rewards, True), "should return res")

        newbfp.isDone = True
        self.assertIsNotNone(reward.process(rewards, True), "should return res")

        self.config.proxy = None
        BingRewards(bingCommon.HEADERS, useragents, self.config)

    @patch('helpers.getResponseBody')
    def test_rewards_hit(self, helpmock):
        """
        test rewards object
        :return:
        """
        self.config.proxy = False
        reward = BingRewards(bingCommon.HEADERS, "", self.config)
        self.assertIsNotNone(reward.requestFlyoutPage(), "should not be None")

        page = '"WindowsLiveId":""     "WindowsLiveId":"" '
        page += 'action="0" value="0" '
        page += 'value= "0" NAP value="0" '
        page += 'ANON value="0" '
        page += 'id="t" value="0" '
        page += '<div> 999 livetime points</div> '

        helpmock.return_value = page

        # if not login should have not found error for url
        self.assertRaisesRegexp(ValueError, "unknown", reward.getLifetimeCredits)

        page = "t.innerHTML='100'"
        helpmock.return_value = page
        self.assertIsNotNone(reward.getRewardsPoints(), "should not be None")
        self.assertRaisesRegexp(TypeError, "not an instance", reward.process, None, True)

        # NONE case
        newbfp = bfp.Reward()
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
        newbfp.progressCurrent = 100
        rewards = [ newbfp ]
        self.assertIsNotNone(reward.process(rewards, True), "should return res")

        self.assertRaisesRegexp(TypeError, "not an instance", reward.printResults, None, True)

        result = mock.Mock()
        result.action = bfp.Reward.Type.Action.SEARCH
        result.isError = True
        result.o = newbfp
        result.message = "done"
        newbfp.progressCurrent = 1
        newbfp.progressMax = 100
        newbfp.url = "http:0.0.0.0"
        self.assertIsNone(reward.printResults([result], True), "should return None")
        self.assertRaisesRegexp(TypeError, "rewards is not", reward.printRewards, None)

        self.assertIsNone(reward.printRewards(rewards), "should return None")

        self.assertRaisesRegexp(TypeError, "reward is not", reward.RewardResult, None)
        self.assertIsNotNone(reward.RewardResult(newbfp), "should return class")

        proxy = mock.Mock()
        proxy.login = True
        proxy.password = "xxx"
        proxy.url = "http://127.0.0.1"
        proxy.protocols = "http"
        self.config.proxy = proxy
        self.assertIsNotNone(BingRewards(bingCommon.HEADERS, "", self.config), "should return class")

if __name__ == '__main__': # pragma: no cover
    unittest.main(verbosity=3)
