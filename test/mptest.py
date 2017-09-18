import unittest
import sys
import os
import main

import dill as pickle
from pathos.multiprocessing import ProcessingPool

sys.path.append(os.path.abspath("pkg"))
sys.path.append(os.path.abspath("."))

from config import Config


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


def run(config):
    return main.__run(config)


class TestMP(unittest.TestCase):
    """
    Test under multiprocessing environment
    """

    def setUp(self):
        self.config = Config()
        self.configXMLString = XMLString

    def test_accounts(self):
        self.config.parseFromString(self.configXMLString)
        import copy
        saved = copy.copy(self.config.accounts)
        for key, account in saved.iteritems():
            self.config.accounts.clear()
            self.config.accounts[key] = account
            self.assertIsNotNone(self.config.accounts[key], "should be one account")

    @unittest.skip("need love with pickle")
    def test_pool(self):
        pool = ProcessingPool(nodes=1)
        result = pool.map(run, [self.config])


if __name__ == "__main__":
    unittest.main(verbosity=3)

