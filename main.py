#!/usr/bin/env python

#
# developed by Sergey Markelov (2013)
#

import HTMLParser
import getopt
import sys
import urllib2
import xml.etree.ElementTree as et

from bingAuth import BingAuth, AuthenticationError
from bingRewards import BingRewards
import bingCommon
import bingFlyoutParser as bfp
import helpers

verbose = False

class RewardsReport:
    def __init__(self):
        self.accountType     = ""
        self.accountLogin    = ""
        self.oldPoints       = 0
        self.newPoints       = 0
        self.pointsEarned    = 0
        self.lifetimeCredits = 0

def earnRewards(reportItem, password):
    """Earns Bing! reward points and populates reportItem"""
    noException = False
    try:
        if reportItem is None: raise ValueError("reportItem is None")
        if reportItem.accountType is None: raise ValueError("reportItem.accountType is None")
        if reportItem.accountLogin is None: raise ValueError("reportItem.accountLogin is None")
        if password is None: raise ValueError("password is None")

        bingRewards = BingRewards()
        bingAuth    = BingAuth(bingRewards.opener)
        bingAuth.authenticate(reportItem.accountType, reportItem.accountLogin, password)
        reportItem.oldPoints = bingRewards.getRewardsPoints()
        rewards = bfp.parseFlyoutPage(bingRewards.requestFlyoutPage(), bingCommon.BING_URL)

        if verbose:
            bingRewards.printRewards(rewards)
        results = bingRewards.process(rewards)

        if verbose:
            print
            print "-" * 80
            print

        bingRewards.printResults(results, verbose)

        reportItem.newPoints = bingRewards.getRewardsPoints()
        reportItem.lifetimeCredits = bingRewards.getLifetimeCredits()
        reportItem.pointsEarned = reportItem.newPoints - reportItem.oldPoints
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
        print "AuthenticationError:\n%s" % e

    except HTMLParser.HTMLParseError, e:
        print "HTMLParserError: %s" % e

    except urllib2.HTTPError, e:
        print "The server couldn't fulfill the request."
        print "Error code: ", e.code

    except urllib2.URLError, e:
        print "Failed to reach the server."
        print "Reason: ", e.reason

    finally:
        if not noException:
            print
            print "For: %s - %s" % (reportItem.accountType, reportItem.accountLogin)
            print
            print "-" * 80

def usage():
    print "Usage:"
    print "    -h, --help               show this help"
    print "    -f, --configFile=file    use specific config file. Default is config.xml"
    print "    -r, --full-report        force printing complete report at the end. Note: complete report will be"
    print "                             printed anyway if more than one account was processed and cumulative"
    print "                             points earned is more than zero"
    print "    -v, --verbose            print verbose output"

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

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:rv", ["help", "configFile=", "full-report", "verbose"])
    except getopt.GetoptError, e:
        print "getopt.GetoptError: %s" % e
        usage()
        sys.exit(1)

    configFile = "config.xml"
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
        else:
            raise NotImplementedError("option '" + o + "' is not implemented")

    print "%s - script started" % helpers.getLoggingTime()
    print "-" * 80
    print

    helpers.createResultsDir(__file__)

    try:
        tree = et.parse(configFile)
    except IOError, e:
        print "IOError: %s" % e
        sys.exit(2)

    totalPoints = 0
    report = list()
    root = tree.getroot()
    for accounts in root.findall("accounts"):
        for account in accounts.findall("account"):
            isDisabled = True if account.get("disabled", "false").lower() == "true" else False
            if isDisabled:
                continue

            reportItem = RewardsReport()
            reportItem.accountType = account.get("type")
            reportItem.accountLogin = account.find("login").text
            password = account.find("password").text
            earnRewards(reportItem, password)
            totalPoints += reportItem.pointsEarned
            report.append(reportItem)

    #
    # trigger full report if needed
    #

    if showFullReport or totalPoints > 0 and len(report) > 1:
        print
        print " -=-=-=-=-=-=-=-=-=-=--=-=- FULL REPORT -=-=-=-=-=-=-=-=--=-=-=-=-=-=-=-"
        print
        print "          Account          | Before | After  | Earned | Lifetime Credits"
        print "---------------------------+--------+--------+--------+------------------"

        for r in report:
            print " %25s | %6d | %6d | %6d | %16d" % (__stringifyAccount(r, 25), r.oldPoints, r.newPoints, r.pointsEarned, r.lifetimeCredits)

        print

    #
    # print footer
    #

    print "Total points earned: %d" % totalPoints
    print
    print "%s - script ended" % helpers.getLoggingTime()
