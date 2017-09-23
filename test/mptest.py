import unittest
import sys
import os
import mpmain
from pathos.multiprocessing import ProcessingPool
import re
sys.path.append(os.path.abspath("pkg"))
sys.path.append(os.path.abspath("."))

from config import Config

PATTERN_SEL = re.compile(r'<login.*?>(.+?)</login>', re.MULTILINE)
PATTERN_ACCS = re.compile(r'<accounts>(.+?)</accounts>', re.MULTILINE)
PATTERN_ACC = re.compile(r'<account.*?>(.+?)</account>', re.MULTILINE)
PATTERN_REFS = re.compile(r'<account ref.*Live_.*</account>', re.MULTILINE)
PATTERN_REF = re.compile(r'<account ref.*Live_.*</account> |.*', re.MULTILINE)

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

                <account ref="Live_abc@ps.com">
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


def run_v1(config): # pragma: no cover
    return main.__run(config)


def run(nodes=1, filename="config.xml"):
    file_xml = ""
    with open(filename, "r") as fd:
        lines = fd.readlines()
        for line in lines:
            file_xml += line
    xml = " ".join(file_xml.rsplit())

    pool = ProcessingPool(nodes)
    runlist = [[xml, value] for value in PATTERN_SEL.findall(xml)]
    return pool.map(mpmain.helper, runlist)


def replace(xml, selector):
    """
    replace xml accounts with only selector inside
    :param xml:
    :param selector:
    :return:
    """
    newXML = " ".join(xml.rsplit())
    accounts = PATTERN_ACCS.findall(newXML)[0]
    type = accounts.split(">")[0] + ">"
    for account in PATTERN_ACC.findall(accounts):
        if selector in account:
            break
    newXML = PATTERN_ACCS.sub('<accounts> ' + type + account + "</account> </accounts>", newXML)

    accounts = PATTERN_REFS.findall(newXML)[0]
    for account in PATTERN_REF.findall(accounts):
        if selector in account:
            break
    newXML = PATTERN_REFS.sub(account, newXML)
    return newXML


class TestMP(unittest.TestCase):
    """
    Test under multiprocessing environment
    """

    def setUp(self):
        self.config = Config()
        self.configXMLString = XMLString

    def test_selector(self):
        """
        test replacement functions and replace account ref/type if they are not account
        :return:
        """
        newXML = replace(XMLString, "ms@ps.com")
        self.assertIsNone(self.config.parseFromString(newXML), "should be none")

    def test_pool_file(self):
        """
        test process pool of two from a file
        :return:
        """
        run(2, "config.xml.dist")

if __name__ == "__main__": # pragma: no cover
    unittest.main(verbosity=0)
