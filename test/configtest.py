#!/usr/bin/env python -B

import unittest
import sys
import os
import errno

sys.path.append(os.path.abspath("pkg"))
sys.path.append(os.path.abspath("."))

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
import bingDashboardParser as bdp
import bingAuth
from config import Config
from config import BingRewardsReportItem
from eventsProcessor import EventsProcessor
from bingRewards import BingRewards
from socket import error as SocketError

sys.path.append(os.path.abspath("pkg/queryGenerators"))
import googleTrends
import wikipedia
import HTMLParser

XMLString = """
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
FBXML = """
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
                <invalidretry if="%p lt 16" interval="5" salt="3.5" count="1" />
                <retry interval="5" salt="3.5" count="1" />
                <notify cmd="echo error %a %p %r %l %i" />
            </onError>
            <onComplete>
                <invalidretry if="%p lt 16" interval="5" salt="3.5" count="1" />

                <account ref="Facebook_john.smith@gmail.com">
                    <retry if="%p lt 31" interval="5" salt="3.5" count="1" />
                    <notify if="%l gt 10000" cmd="echo complete %a %p %r %P %l %i" />
                    <notify if="%p ne 31" cmd="echo complete %a %p %r %P %l %i" />
                    <notify if="%P gt 475" cmd="echo complete %a %p %r %P %l %i" />
                </account>
            </onComplete>
            <onScriptComplete>
                <invalidretry if="%p lt 16" interval="5" salt="3.5" count="1" />
                <notify cmd="./mail.sh" />
            </onScriptComplete>
            <onScriptFailure>
                <invalidretry if="%p lt 16" interval="5" salt="3.5" count="1" />
                <notify cmd="./onScriptFailure.sh" />
            </onScriptFailure>
        </events>
        <queries generator="wikipedia" />
    </configuration>
            """

NONREF = """
    <configuration>
        <general />
        <accounts>
            <account type="Facebook" disabled="false">
                <login>john.smith@gmail.com</login>
                <password>xxx</password>
            </account>
        </accounts>

        <events>
            <onComplete>
                <account>
                    <retry if="%p lt 31" interval="5" salt="3.5" count="1" />
                    <notify if="%l gt 10000" cmd="echo complete %a %p %r %P %l %i" />
                    <notify if="%p ne 31" cmd="echo complete %a %p %r %P %l %i" />
                    <notify if="%P gt 475" cmd="echo complete %a %p %r %P %l %i" />
                </account>
            </onComplete>
        </events>
        <queries generator="wikipedia" />
    </configuration>
            """

NONACCREF = """
    <configuration>
        <general />
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
                <account>
                </account>
            </onComplete>
            <onScriptComplete>
                <invalidretry if="%p lt 16" interval="5" salt="3.5" count="1" />
                <notify cmd="./mail.sh" />
            </onScriptComplete>
            <onScriptFailure>
                <invalidretry if="%p lt 16" interval="5" salt="3.5" count="1" />
                <notify cmd="./onScriptFailure.sh" />
            </onScriptFailure>
        </events>
        <queries generator="wikipedia" />
    </configuration>
            """

NONEV = """
    <configuration>
        <general />
        <accounts>
            <account type="Facebook" disabled="false">
                <login>john.smith@gmail.com</login>
                <password>xxx</password>
            </account>
        </accounts>

        <events>
            <onErrorRetry>
                <retry interval="5" salt="3.5" count="1" />
                <notify cmd="echo error %a %p %r %l %i" />
            </onErrorRetry>
        </events>
        <queries generator="wikipedia" />
    </configuration>
            """

RETRY = """
    <configuration>
        <general />
        <accounts>
            <account type="Facebook" disabled="false">
                <login>john.smith@gmail.com</login>
                <password>xxx</password>
            </account>
        </accounts>

        <events>
            <onError>
                <retry salt="3.5" count="1" />
                <notify cmd="echo error %a %p %r %l %i" />
            </onError>
        </events>
        <queries generator="wikipedia" />
    </configuration>
            """

INVRETRY = """
    <configuration>
        <general />
        <accounts>
            <account type="Facebook" disabled="false">
                <login>john.smith@gmail.com</login>
                <password>xxx</password>
            </account>
        </accounts>

        <events>
            <onError>
                <retry interval="asdfsf" salt="3.5" count="1" />
                <notify cmd="echo error %a %p %r %l %i" />
            </onError>
        </events>
        <queries generator="wikipedia" />
    </configuration>
            """

NEGRETRY = """
    <configuration>
        <general />
        <accounts>
            <account type="Facebook" disabled="false">
                <login>john.smith@gmail.com</login>
                <password>xxx</password>
            </account>
        </accounts>

        <events>
            <onError>
                <retry interval="-1" salt="3.5" count="1" />
                <notify cmd="echo error %a %p %r %l %i" />
            </onError>
        </events>
        <queries generator="wikipedia" />
    </configuration>
            """

RETRYCNT = """
    <configuration>
        <general />
        <accounts>
            <account type="Facebook" disabled="false">
                <login>john.smith@gmail.com</login>
                <password>xxx</password>
            </account>
        </accounts>

        <events>
            <onError>
                <retry interval="0" salt="3.5" />

                <notify cmd="echo error %a %p %r %l %i" />
            </onError>
        </events>
        <queries generator="wikipedia" />
    </configuration>
            """

INVRETRYCNT = """
    <configuration>
        <general />
        <accounts>
            <account type="Facebook" disabled="false">
                <login>john.smith@gmail.com</login>
                <password>xxx</password>
            </account>
        </accounts>

        <events>
            <onError>
                <retry interval="0" count="asdfsf" salt="3.5" />
                <notify cmd="echo error %a %p %r %l %i" />
            </onError>
        </events>
        <queries generator="wikipedia" />
    </configuration>
            """

NEGRETRYCNT = """
    <configuration>
        <general />
        <accounts>
            <account type="Facebook" disabled="false">
                <login>john.smith@gmail.com</login>
                <password>xxx</password>
            </account>
        </accounts>

        <events>
            <onError>
                <retry interval="0" count="-1" salt="3.5" />
                <notify cmd="echo error %a %p %r %l %i" />
            </onError>
        </events>
        <queries generator="wikipedia" />
    </configuration>
            """

INT = """
    <configuration>
        <general
            openLinkChance="-1"
            betweenAccountsSalt="40.52" />
    </configuration>
            """

FLOAT = """
    <configuration>
        <general
            addSearchesMobile="-1" />
    </configuration>
            """
NONINT = """
    <configuration>
        <general
            openTopLinkRange="asdfd" />
    </configuration>
            """

NONFLOAT = """
    <configuration>
        <general
            addSearchesMobile="asdfdf" />
    </configuration>
            """

EVENT = """
    <configuration>
        <general
            betweenQueriesInterval="12.271"
            betweenQueriesSalt="5.7"
            betweenAccountsInterval="404.1"
            betweenAccountsSalt="40.52" />
        <queries/>
    </configuration>
            """

EVENTLESS = """
    <configuration>
        <general
            betweenQueriesInterval="12.271"
            betweenQueriesSalt="5.7"
            betweenAccountsInterval="404.1"
            betweenAccountsSalt="40.52" />

        <accounts>
            <account type="Live" disabled="false">
                <login>john.smith@gmail.com</login>
                <password>xxx</password>
            </account>
        </accounts>
        <queries generator="wikipedia" />
    </configuration>
            """

InvalidXML = """
    <configuration>
        <abc> invalid </abc>
    </configuration>
            """

LOGINXML = """
    <configuration>
        <general
            betweenQueriesInterval="12.271"
            betweenQueriesSalt="5.7"
            betweenAccountsInterval="404.1"
            betweenAccountsSalt="40.52" />
        <accounts>
            <account type="Live" disabled="false">
                <password>xxx</password>
            </account>
        </accounts>
    </configuration>
            """

PWDXML = """
    <configuration>
        <general
            betweenQueriesInterval="12.271"
            betweenQueriesSalt="5.7"
            betweenAccountsInterval="404.1"
            betweenAccountsSalt="40.52" />

        <accounts>
            <account type="Live" disabled="false">
                <login>john.smith@gmail.com</login>
            </account>
        </accounts>
    </configuration>
            """

PROTXML = """
    <configuration>
        <general
            betweenQueriesInterval="12.271"
            betweenQueriesSalt="5.7"
            betweenAccountsInterval="404.1"
            betweenAccountsSalt="40.52" />
        <proxy
               url="www.bing.com"
               login="xxx"
               password="yyy" />
    </configuration>
            """

URLXML = """
    <configuration>
        <general
            betweenQueriesInterval="12.271"
            betweenQueriesSalt="5.7"
            betweenAccountsInterval="404.1"
            betweenAccountsSalt="40.52" />
        <proxy protocols="http"

               login="xxx"
               password="yyy" />
    </configuration>
            """

PROXYLOGINXML = """
    <configuration>
        <general
            betweenQueriesInterval="12.271"
            betweenQueriesSalt="5.7"
            betweenAccountsInterval="404.1"
            betweenAccountsSalt="40.52" />
        <proxy protocols="http"
               url="www.bing.com"
               password="yyy" />
    </configuration>
            """

NONIF2 = """
    <configuration>
        <general />
        <accounts>
            <account type="Live" disabled="false">
                <login>ms@ps.com</login>
                <password>zzz</password>
            </account>
        </accounts>

        <events>
            <onComplete>
                <retry if="%p lt" interval="5" salt="3.5" count="1" />
                <account ref="Live_ms@ps.com">
                    <retry if="%p lt 31" interval="5" salt="3.5" count="1" />
                </account>

            </onComplete>
        </events>
        <queries generator="googleTrends" />
    </configuration>
            """

NONIFRHS = """
    <configuration>
        <general />
        <accounts>
            <account type="Live" disabled="false">
                <login>ms@ps.com</login>
                <password>zzz</password>
            </account>
        </accounts>
        <events>
            <onComplete>
                <notify if="%l gt adfsdf" cmd="echo complete %a %p %r %P %l %i" />
                <account ref="Live_ms@ps.com">
                    <retry if="%p lt 31" interval="5" salt="3.5" count="1" />
                </account>
            </onComplete>
        </events>
        <queries generator="googleTrends" />
    </configuration>
            """

NONIFOP = """
    <configuration>
        <general />
        <accounts>
            <account type="Live" disabled="false">
                <login>ms@ps.com</login>
                <password>zzz</password>
            </account>
        </accounts>
        <events>
            <onComplete>
                <notify if="%l gt adfsdf" cmd="echo complete %a %p %r %P %l %i" />
                <account ref="Live_ms@ps.com">
                    <retry if="%p zt 0.001" interval="5" salt="3.5" count="1" />
                </account>
            </onComplete>
        </events>
        <queries generator="googleTrends" />
    </configuration>
            """

DASHPG = ""

def validateSpecifier(specifier, specifierType=None):
    spec = Config.Event.Specifier()
    return spec._Specifier__validateSpecifier(specifier, specifierType=None)


def run(config):
    return main.__run(config)


def stringify(report_item, len):
    return main.__stringifyAccount(report_item, len)


def processAccount(config):
    bp = BingRewardsReportItem()
    return main.__processAccount(config, None, None, bp, "")


class TestConfig(unittest.TestCase):
    fsock = None
    mockdate = "2017-09-06 00:44:47.7"

    def _redirectOut(self):  # pragma: no cover
        self.fsock = open('out.log', 'a+')
        sys.stdout = self.fsock

    def tearDown(self):  # pragma: no cover
        if self.fsock is not None:
            self.fsock.close()
            self.fsock = None
            sys.stdout = sys.__stdout__

    def setUp(self):
        self.config = Config()
        self.configXMLString = XMLString

        self.config.parseFromString(self.configXMLString)
        self.configFBXML = FBXML

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

    @patch('os.path.dirname', new=Mock(side_effect=OSError("fail to mock a write", errno.EACCES)))
    def test_createdir_raise(self):
        """
         test dir raise error
         :return:
         """
        self.assertRaisesRegexp(OSError, "fail to mock", helpers.createResultsDir, "none")

    @patch('os.path.dirname', new=Mock(side_effect=OSError("fail to mock a write", errno.EEXIST)))
    def test_createdir_fail(self):
        """
         test dir with failing oserror
         :return:
         """
        self.assertRaisesRegexp(OSError, "fail to mock", helpers.createResultsDir, "none")

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
        sys.version_info = [2, 1]

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

    @patch('helpers.getResponseBody', return_value='"WindowsLiveId":""     "WindowsLiveId":""')
    @patch('time.sleep', return_value='')
    def test_auth_url(self, timemock, helpmock):  # pragma: no cover
        """
        test authentication decoding error
        :return:
        """
        self.assertRaisesRegexp(ValueError, "unknown url type", run, self.config)

    @patch('bingAuth.BingAuth.authenticate',
           new=Mock(side_effect=SocketError(errno.ECONNREFUSED, "errno.ECONNREFUSED")))
    def test_auth_exceptionSock(self):
        self.assertRaisesRegexp(SocketError, "", run, self.config)

    @patch('bingAuth.BingAuth.authenticate', new=Mock(side_effect=SocketError(errno.ECONNRESET, "errno.ECONNRESET")))
    def test_auth_exceptionSockReset(self):
        self.assertIsNone(run(self.config), "should not return anything")

    @patch('bingAuth.BingAuth.authenticate', new=Mock(side_effect=helpers.BingAccountError(None)))
    def test_auth_exceptionBing(self):
        self.assertIsNone(run(self.config), "should not return anything")

    @patch('bingAuth.BingAuth.authenticate', new=Mock(side_effect=urllib2.URLError("")))
    def test_auth_exceptionURL(self):
        self.assertIsNone(run(self.config), "should not return anything")

    @patch('bingAuth.BingAuth.authenticate', new=Mock(side_effect=HTMLParser.HTMLParseError("error")))
    def test_auth_exceptionParser(self):
        self.assertIsNone(run(self.config), "should not return anything")

    @patch('bingAuth.BingAuth.authenticate', new=Mock(side_effect=urllib2.HTTPError("", "", "", "", open("tmp", "a+"))))
    def test_auth_exceptionHTTP(self):
        self.assertIsNone(run(self.config), "should not return anything")

    def test_stringify(self):
        self.assertRaisesRegexp(ValueError, "too small", stringify, None, -1)

    @patch('urllib2.Request', return_value="")
    @patch('helpers.getResponseBody', return_value="")
    @patch('urllib2.Request.add_header', return_value=urllib2.Request(bingCommon.BING_URL, bingCommon.HEADERS))
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

    def test_config(self):
        """
        test config module
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
        ifs.lhs = lambda x: x
        ifs.rhs = "b"
        self.assertIsNotNone(str(ifs), "should return class")
        self.assertRaisesRegexp(ValueError, "None", ifs.evaluate, None)
        self.assertRaisesRegexp(TypeError, "is not of", ifs.evaluate, [])
        self.assertIsNotNone(ifs.evaluate(BingRewardsReportItem()))

        spec = Config.Event.Specifier()
        self.assertIsNotNone(spec, "should return class")
        self.assertRaisesRegexp(ValueError, "is None", spec.evaluate, None, BingRewardsReportItem())
        self.assertRaisesRegexp(TypeError, "list", spec.evaluate, [], BingRewardsReportItem())
        self.assertRaisesRegexp(ValueError, "is None", spec.evaluate, [], None)
        self.assertRaisesRegexp(TypeError, "not of BingRewardsReportItem type", spec.evaluate, [], self.config)
        self.assertIsNotNone(spec.evaluate("%a", BingRewardsReportItem()), "should return string")

        dist = os.path.join(os.path.dirname(__file__), "..", "config.xml")
        self.assertIsNone(configobj.parseFromFile(dist), "should be none")
        self.assertRaisesRegexp(ValueError, "_configFile_ is None", configobj.parseFromFile, None)
        self.assertRaisesRegexp(ValueError, "is None", self.config.parseFromString, None)
        self.assertRaisesRegexp(ConfigError, "Invalid subnode", configobj.parseFromString, InvalidXML)
        self.assertRaisesRegexp(ConfigError, "is not found", configobj.parseFromString, LOGINXML)
        self.assertRaisesRegexp(ConfigError, "is not found", configobj.parseFromString, PWDXML)
        self.assertRaisesRegexp(ConfigError, "should be either set", self.config.parseFromString, PROXYLOGINXML)
        self.assertRaisesRegexp(KeyError, "_specifier_ is not", validateSpecifier, "%not")
        self.assertRaisesRegexp(ConfigError, "Invalid subnode", self.config.parseFromString, FBXML)

    def test_config_attr(self):
        self.assertRaisesRegexp(ConfigError, "MUST", self.config.parseFromString, FLOAT)
        self.assertRaisesRegexp(ConfigError, "MUST", self.config.parseFromString, INT)
        self.assertRaisesRegexp(ConfigError, "must", self.config.parseFromString, NONFLOAT)
        self.assertRaisesRegexp(ConfigError, "must", self.config.parseFromString, NONINT)

    def test_config_notify(self):
        self.assertRaisesRegexp(ConfigError, "is not found", self.config.parseFromString, NONREF)
        self.assertRaisesRegexp(ConfigError, "is not found", self.config.parseFromString, NONACCREF)
        self.assertRaisesRegexp(ConfigError, "not supported", self.config.parseFromString, NONEV)

    def test_config_retry(self):
        self.assertRaisesRegexp(ConfigError, "is not found", self.config.parseFromString, RETRY)
        self.assertRaisesRegexp(ConfigError, "must be", self.config.parseFromString, INVRETRY)
        self.assertRaisesRegexp(ConfigError, "MUST BE", self.config.parseFromString, NEGRETRY)
        self.assertRaisesRegexp(ConfigError, "is not found", self.config.parseFromString, RETRYCNT)
        self.assertRaisesRegexp(ConfigError, "must be", self.config.parseFromString, INVRETRYCNT)
        self.assertRaisesRegexp(ConfigError, "MUST BE", self.config.parseFromString, NEGRETRYCNT)

    def test_config_if(self):
        self.assertRaisesRegexp(ConfigError, "is invalid", self.config.parseFromString, NONIF2)
        self.assertRaisesRegexp(ConfigError, "is invalid", self.config.parseFromString, NONIFRHS)
        self.assertRaisesRegexp(ConfigError, "is invalid", self.config.parseFromString, NONIFOP)

    def test_event(self):
        """
        test event
        :return:
        """
        self.assertIsNone(EventsProcessor.onScriptFailure(self.config, Exception()), "should be none")
        self.assertIsNone(EventsProcessor.onScriptComplete(self.config), "should be none")
        self.assertRaisesRegexp(ConfigError, "not found", self.config.parseFromString, EVENT)
        self.config.parseFromString(EVENTLESS)
        self.assertRaisesRegexp(Exception, ".*", EventsProcessor.onScriptFailure, self.config, Exception())
        self.assertIsNone(EventsProcessor.onScriptComplete(self.config), "should be none")
        ep = EventsProcessor(self.config, BingRewardsReportItem())
        self.assertIsNotNone(ep.processReportItem(), "should not be none and be done")

    @patch('main.earnRewards', return_value=None)
    @patch('eventsProcessor.EventsProcessor.processReportItem', return_value=(-1, None))
    def test_event_dontcare(self, mockep, mockmain):
        # not retry nor ok with -1
        self.assertIsNone(processAccount(self.config), "should return nothing")

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

    def test_reward_bfp_hit(self):
        self._rewards_hit(bfp.RewardV1())
        self._rewards_hit(bdp.Reward())

    @patch('helpers.getResponseBody')
    def _rewards_hit(self, classobj, helpmock):
        """
        test rewards object
        :return:
        """
        self.config.proxy = False
        reward = BingRewards(bingCommon.HEADERS, "", self.config)

        page = '"WindowsLiveId":""     "WindowsLiveId":"" '
        page += 'action="0" value="0" '
        page += 'value= "0" NAP value="0" '
        page += 'ANON value="0" '
        page += 'id="t" value="0" '
        page += '<div> 999 livetime points</div> '

        helpmock.return_value = page

        # if not login should have not found error for url
        self.assertIsNotNone(reward.getLifetimeCredits, "Should return int")

        page = "t.innerHTML='100'"
        helpmock.return_value = page
        self.assertIsNotNone(reward.getRewardsPoints(), "should not be None")
        self.assertRaisesRegexp(TypeError, "not an instance", reward.process, None, True)

        # NONE case
        newbfp = classobj
        newbfp.tp = None
        rewards = [newbfp]
        self.assertIsNotNone(reward.process(rewards, True), "handle not none")

        # HIT case
        newbfp.tp = mock.Mock()
        newbfp.tp = [0, 1, 2, 3, bfp.RewardV1.Type.Action.HIT]

        # SEARCH case
        newbfp.tp = mock.Mock()
        newbfp.tp = [0, 1, 2, 3, bfp.RewardV1.Type.Action.SEARCH]
        newbfp.progressCurrent = 100
        rewards = [newbfp]
        self.assertIsNotNone(reward.process(rewards, True), "should return res")

        self.assertRaisesRegexp(TypeError, "not an instance", reward.printResults, None, True)

        result = mock.Mock()
        result.action = bfp.RewardV1.Type.Action.SEARCH
        result.isError = True
        result.o = newbfp
        result.message = "done"
        newbfp.progressCurrent = 1
        newbfp.progressMax = 100
        newbfp.url = "http:0.0.0.0"
        self.assertIsNone(reward.printResults([result], True), "should return None")
        self.assertRaisesRegexp(TypeError, "rewards is not", reward.printRewards, None)
        rewards[0].isDone = True
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

        proxy.login = False
        self.config.proxy = proxy
        self.assertIsNotNone(BingRewards(bingCommon.HEADERS, "", self.config), "should return class")

        self.assertRaisesRegexp(ConfigError, "not found", self.config.parseFromString, PROTXML)
        self.assertRaisesRegexp(ConfigError, "not found", self.config.parseFromString, URLXML)


class TestLong(unittest.TestCase):
    """
    Test that takes near 30s
    """

    def setUp(self):
        self.config = Config()
        self.configXMLString = XMLString

        self.config.parseFromString(self.configXMLString)

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

        # test with proxy
        b = BingRewards(bingCommon.HEADERS, useragents, self.config)
        self.config.login = None

        # test without proxy
        b = BingRewards(bingCommon.HEADERS, useragents, self.config)
        q = wikipedia.queryGenerator(b)
        q.br = None
        q.unusedQueries = set()
        self.assertIsNotNone(q.generateQueries(10, set()))

    def test_bingparser(self):
        self._bp(bfp.RewardV1())
        self._bp(bdp.Reward())

    def _bp(self, classobj):
        """
        test reward parser
        :return:
        """
        self.assertIsNotNone(classobj.isAchieved(), "should not be None")
        classobj.progressCurrent = 1
        classobj.progressMax = 100
        self.assertIsNotNone(classobj.progressPercentage(), "should not be None")
        page = '<div id="messageContainer"></div>'
        page += '<div id="bottomContainer"></div>'
        if isinstance(classobj, bdp.Reward):
            with open("test/dashhtml", "r") as fd:
                DASHPG = fd.readlines()
                DASHPG = "".join(DASHPG)
                self.assertIsNotNone(bdp.parseDashboardPage(DASHPG, bingCommon.ACCOUNT_URL), "should see rewards")
        if isinstance(classobj, bfp.RewardV1):
            self.assertIsNotNone(bfp.parseFlyoutPage(page, "http://bing"), "should not be None")
        self.assertIsNotNone(classobj.Type.Action.toStr(classobj.Type.Action.PASS), "should not be None")

        classobj.progressCurrent = 1
        classobj.progressMax = 0
        self.assertIsNotNone(classobj.progressPercentage(), "should not be None")

    @patch('bingFlyoutParser.RewardV1.progressPercentage', return_value="100")
    @patch('helpers.getResponseBody')
    def test_rewards_search(self, helpmock, permock):
        """
        Search rewards string
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
        newbfp = bfp.RewardV1()
        reward.RewardResult(newbfp)

        newbfp.progressCurrent = 1
        newbfp.progressMax = 100
        newbfp.description = "Up to 10 points today, 10 points per search"

        newbfp.isDone = False

        # SEARCH case, PC, Mobile, Earn
        for data in [
            newbfp.Type.SEARCH_MOBILE,
            newbfp.Type.SEARCH_PC,
            newbfp.Type.YOUR_GOAL,
            newbfp.Type.MAINTAIN_GOLD,
            newbfp.Type.REFER_A_FRIEND,
            newbfp.Type.SEND_A_TWEET,
            newbfp.Type.RE_EARNED_CREDITS,
            newbfp.Type.COMPLETED,
            newbfp.Type.SILVER_STATUS,
            newbfp.Type.INVITE_FRIENDS,
            newbfp.Type.EARN_MORE_POINTS,
            newbfp.Type.SEARCH_AND_EARN,
            newbfp.Type.THURSDAY_BONUS,
            newbfp.Type.RE_QUIZ]:
            newbfp.tp = data
            newbfp.url = "www.espn.com"

            newbfp.Type = bfp.RewardV1.Type.Action.SEARCH
            rewards = [newbfp]
            newbfp.isAchieved = lambda: data is False
            self.assertIsNotNone(reward.process(rewards, True), "should return res")

        newbfp.isDone = True
        self.assertIsNotNone(reward.process(rewards, True), "should return res")

        self.config.proxy = None
        BingRewards(bingCommon.HEADERS, useragents, self.config)


class TestBDP(unittest.TestCase):
    """
    Test that takes near 30s
    """

    def setUp(self):
        self.config = Config()
        self.configXMLString = XMLString

        self.config.parseFromString(self.configXMLString)

    @patch('bingDashboardParser.Reward.progressPercentage', return_value="100")
    @patch('helpers.getResponseBody')
    def test_bdp_search(self, helpmock, permock):
        """
        Search rewards string
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
        newbdp = bdp.Reward()
        reward.RewardResult(newbdp)

        newbdp.progressCurrent = 1
        newbdp.progressMax = 100
        newbdp.description = "Up to 10 points today, 10 points per search"

        newbdp.isDone = False

        # SEARCH case, PC, Mobile, Earn
        for data in [
            newbdp.Type.SEARCH_MOBILE,
            newbdp.Type.SEARCH_PC,
            newbdp.Type.YOUR_GOAL,
            newbdp.Type.MAINTAIN_GOLD,
            newbdp.Type.REFER_A_FRIEND,
            newbdp.Type.SEND_A_TWEET,
            newbdp.Type.RE_EARNED_CREDITS,
            newbdp.Type.COMPLETED,
            newbdp.Type.SILVER_STATUS,
            newbdp.Type.INVITE_FRIENDS,
            newbdp.Type.EARN_MORE_POINTS,
            newbdp.Type.SEARCH_AND_EARN,
            newbdp.Type.THURSDAY_BONUS,
            newbdp.Type.RE_QUIZ]:
            newbdp.tp = data
            newbdp.url = "www.espn.com"

            newbdp.Type = bfp.RewardV1.Type.Action.SEARCH
            rewards = [newbdp]
            newbdp.isAchieved = lambda: data is False
            self.assertIsNotNone(reward.process(rewards, True), "should return res")

        newbdp.isDone = True
        self.assertIsNotNone(reward.process(rewards, True), "should return res")

        self.config.proxy = None
        BingRewards(bingCommon.HEADERS, useragents, self.config)


if __name__ == '__main__':  # pragma: no cover
    unittest.main(verbosity=3)
