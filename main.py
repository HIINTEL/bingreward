#!/usr/bin/env python

#
# developed by Sergey Markelov (2013)
#

from __future__ import absolute_import

import HTMLParser
import getopt
import os
import random
import sys
import time
import urllib2

from socket import error as SocketError
import errno

sys.path.append(os.path.join(os.path.dirname(__file__), "pkg"))
sys.path.append(os.path.join(os.path.dirname(__file__), "pkg", "queryGenerators"))

from bingAuth import BingAuth, AuthenticationError
from bingRewards import BingRewards
from config import BingRewardsReportItem, Config, ConfigError
from eventsProcessor import EventsProcessor
import bingCommon
import bingFlyoutParser as bfp
import helpers
from helpers import BingAccountError

verbose = False
totalPoints = 0

SCRIPT_VERSION = "3.14.9"
SCRIPT_DATE = "September 7, 2016"

def earnRewards(config, httpHeaders, userAgents, reportItem, password):
    """Earns Bing! reward points and populates reportItem"""
    noException = False
    try:
        if reportItem is None: raise ValueError("reportItem is None")
        if reportItem.accountType is None: raise ValueError("reportItem.accountType is None")
        if reportItem.accountLogin is None: raise ValueError("reportItem.accountLogin is None")
        if password is None: raise ValueError("password is None")

        del reportItem.error
        reportItem.error = None
        reportItem.pointsEarned = 0

        bingRewards = BingRewards(httpHeaders, userAgents, config)
        bingAuth    = BingAuth(httpHeaders, bingRewards.opener)
        bingAuth.authenticate(reportItem.accountType, reportItem.accountLogin, password)
        reportItem.oldPoints = bingRewards.getRewardsPoints()
        rewards = bfp.parseFlyoutPage(bingRewards.requestFlyoutPage(), bingCommon.BING_URL)

        if verbose:
            bingRewards.printRewards(rewards)
        print ("%s - %s" % (reportItem.accountType, reportItem.accountLogin))
        results = bingRewards.process(rewards, verbose)

        if verbose:
            print
            print "-" * 80
            print

        bingRewards.printResults(results, verbose)

        reportItem.newPoints = bingRewards.getRewardsPoints()
        reportItem.lifetimeCredits = bingRewards.getLifetimeCredits()
        reportItem.pointsEarned = reportItem.newPoints - reportItem.oldPoints
        reportItem.pointsEarnedRetrying += reportItem.pointsEarned
        print
        print "%s - %s" % (reportItem.accountType, reportItem.accountLogin)
        print
        print "Points before:    %6d" % reportItem.oldPoints
        print "Points after:     %6d" % reportItem.newPoints
        print "Points earned:    %6d" % reportItem.pointsEarned
        print "Lifetime Credits: %6d" % reportItem.lifetimeCredits

        print
        print "-" * 80

        noException = True

    except AuthenticationError, e:
        reportItem.error = e
        print "AuthenticationError:\n%s" % e

    except HTMLParser.HTMLParseError, e:
        reportItem.error = e
        print "HTMLParserError: %s" % e

    except urllib2.HTTPError, e:
        reportItem.error = e
        print "The server couldn't fulfill the request."
        print "Error code: ", e.code

    except urllib2.URLError, e:
        reportItem.error = e
        print "Failed to reach the server."
        print "Reason: ", e.reason

    except SocketError as e:
        if e.errno != errno.ECONNRESET:
            raise

        # see http://stackoverflow.com/a/20568874/2147244
        # for explanation of the problem

        reportItem.error = e
        print "Connection reset by peer."

    except BingAccountError as e:
        reportItem.error = e
        print "BingAccountError: %s" % e

    finally:
        if not noException:
            print
            print "For: %s - %s" % (reportItem.accountType, reportItem.accountLogin)
            print
            print "-" * 80


def usage():
    print "Usage:"
    print "    -h, --help               show this help"
    print
    print "    -f, --configFile=file    use specific config file. Default is config.xml"
    print
    print "    -r, --full-report        force printing complete report at the end. Note: complete report will be"
    print "                             printed anyway if more than one account was processed and cumulative"
    print "                             points earned is more than zero"
    print
    print "    -v, --verbose            print verbose output"
    print
    print "        --version            print version info"

def printVersion():
    print "Bing! Rewards Automation script: <http://sealemar.blogspot.com/2012/12/bing-rewards-automation.html>"
    print "Version: " + SCRIPT_VERSION + " from " + SCRIPT_DATE
    print "See 'version.txt' for the list of changes"
    print "This code is published under LGPL v3 <http://www.gnu.org/licenses/lgpl-3.0.html>"
    print "There is NO WARRANTY, to the extent permitted by law."
    print
    print "Developed by: Sergey Markelov"

def __stringifyAccount(reportItem, strLen):
    if strLen < 15:
        raise ValueError("strLen too small. Must be > " + 15)

    s = ""
    if reportItem.accountType == "Facebook":
        s += " fb "
    elif reportItem.accountType == "Live":
        s += "live"
    else:
        raise ValueError("Account type (" + reportItem.accountType + ") is not supported")

    s += " - "

    l = strLen - len(s)

    if len(reportItem.accountLogin) < l:
        s += reportItem.accountLogin
    else:
        s += reportItem.accountLogin[:(l - 3)]
        s += "..."

    return s


def __processAccount(config, httpHeaders, userAgents, reportItem, accountPassword):
    global totalPoints
    eventsProcessor = EventsProcessor(config, reportItem)
    while True:
        reportItem.retries += 1

        if reportItem.retries > 1:
            print "retry #" + str(reportItem.retries)

        earnRewards(config, httpHeaders, userAgents, reportItem, accountPassword)
        totalPoints += reportItem.pointsEarned

        result, extra = eventsProcessor.processReportItem()
        if result == EventsProcessor.OK:
            break
        elif result == EventsProcessor.RETRY:
            time.sleep(extra)
        else:
            # TODO: implement as Utils.warn() or something
            print "Unexpected result from eventsProcessor.processReportItem() = ( %s, %s )" % (result, extra)
            break

def __processAccountUserAgent(config, account, userAgents, doSleep):
# sleep between two accounts logins
    if doSleep:
        extra = config.general.betweenAccountsInterval + random.uniform(0, config.general.betweenAccountsSalt)
        if verbose:
            print
            print("Pausing between accounts for {0} seconds".format(int(extra)))
        time.sleep(extra)

    reportItem = BingRewardsReportItem()
    reportItem.accountType  = account.accountType
    reportItem.accountLogin = account.accountLogin

    agents = bingCommon.UserAgents.generate(account)

    httpHeaders = bingCommon.HEADERS
    httpHeaders["User-Agent"] = agents.pc

    __processAccount(config, httpHeaders, agents, reportItem, account.password)

    return reportItem

def __run(config):
    report = list()

    doSleep = False

    for key, account in config.accounts.iteritems():
        if account.disabled:
            continue

        reportItem = __processAccountUserAgent(config, account, bingCommon.USER_AGENTS_PC, doSleep)
        report.append(reportItem)
        doSleep = True


    #
    # trigger full report if needed
    #

    if showFullReport or totalPoints > 0 and len(report) > 1:
        print
        print "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= FINAL REPORT =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
        print
        print "            Account           | Before | After  | Earned |  Lifetime  | Retries "
        print "------------------------------+--------+--------+--------+------------+---------"

        for r in report:
            print " %-28s | %6d | %6d | %6d | %10d | %7d" % (__stringifyAccount(r, 28), r.oldPoints, r.newPoints, r.pointsEarnedRetrying, r.lifetimeCredits, r.retries)

        print

    #
    # print footer
    #

    print "Total points earned: %d" % totalPoints
    print
    print "%s - script ended" % helpers.getLoggingTime()

    EventsProcessor.onScriptComplete(config)

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:rv", ["help", "configFile=", "full-report", "verbose", "version"])
    except getopt.GetoptError, e:
        print "getopt.GetoptError: %s" % e
        usage()
        sys.exit(1)

    configFile = os.path.join(os.path.dirname(__file__), "config.xml")
    showFullReport = False
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-f", "--configFile"):
            configFile = a
        elif o in ("-r", "--full-report"):
            showFullReport = True
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o == "--version":
            printVersion()
            sys.exit()
        else:
            raise NotImplementedError("option '" + o + "' is not implemented")

    print "%s - script started" % helpers.getLoggingTime()
    print "-" * 80
    print

    helpers.createResultsDir(__file__)

    config = Config()

    try:
        config.parseFromFile(configFile)
    except IOError, e:
        print "IOError: %s" % e
        sys.exit(2)
    except ConfigError, e:
        print "ConfigError: %s" % e
        sys.exit(2)

    try:
        __run(config)
    except BaseException, e:
        EventsProcessor.onScriptFailure(config, e)
