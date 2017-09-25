#!/usr/bin/python2.7 -B


#
# developed by Sergey Markelov (2013)
#

from __future__ import with_statement

import cookielib
import random
import time
import urllib
import urllib2
import importlib
import re

import bingCommon
import bingFlyoutParser as bfp
import bingHistory
import helpers

# extend urllib.addinfourl like it defines @contextmanager (to use with "with" keyword)
urllib.addinfourl.__enter__ = lambda self: self
urllib.addinfourl.__exit__  = lambda self, type, value, traceback: self.close()
RE_DASHBD_POINTS = re.compile(r"(\d+) of? (\d+) points?")


class HTTPRefererHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        if not "Referer" in req.headers:
#             if req.get_host() == "www.bing.com":
#                 req.headers["Referer"] = "http://www.bing.com/"
#             else:
                req.headers["Referer"] = req.get_full_url()
        return urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)

    http_error_301 = http_error_303 = http_error_307 = http_error_302

class BingRewards:
    class RewardResult:
        def __init__(self, reward):
            if reward is None or not isinstance(reward, bfp.Reward):
                raise TypeError("reward is not of Reward type")

            self.o = reward
            self.isError = False
            self.message = ""
# action applied to the reward
            self.action  = bfp.Reward.Type.Action.WARN

    BING_FLYOUT_PAGE = "http://www.bing.com/rewardsapp/flyoutpage?style=v2"

    def __init__(self, httpHeaders, userAgents, config):
        """
        From _config_ these parameters are used:
            config.general.betweenQueriesInterval - (double) - how many seconds the script should wait between queries
            config.general.betweenQueriesSalt     - (double) - up to how many seconds to wait on top of _betweenQueriesInterval_ (rand(0, salt))
            config.proxy - proxy settings (can be None)
        """

        self.betweenQueriesInterval = float(config.general.betweenQueriesInterval)
        self.betweenQueriesSalt     = float(config.general.betweenQueriesSalt)
        self.addSearchesDesktop     = int(config.general.addSearchesDesktop)
        self.addSearchesDesktopSalt = int(config.general.addSearchesDesktopSalt)
        self.addSearchesMobile      = int(config.general.addSearchesMobile)
        self.addSearchesMobileSalt  = int(config.general.addSearchesMobileSalt)
        self.openTopLinkRange       = int(config.general.openTopLinkRange)
        self.openLinkChance         = float(config.general.openLinkChance)
        self.httpHeaders = httpHeaders
        self.userAgents  = userAgents
        self.queryGenerator = config.queryGenerator

        cookies = cookielib.CookieJar()

        if config.proxy:
            if config.proxy.login:
                proxyString = "%s:%s@%s" % ( config.proxy.login, config.proxy.password, config.proxy.url )
            else:
                proxyString = config.proxy.url

            print "Protocols: '%s', Proxy: '%s'" % ( ", ".join(config.proxy.protocols), proxyString )

            self.opener = urllib2.build_opener(
                                            urllib2.ProxyHandler( { p : proxyString for p in config.proxy.protocols } ),
                                            #urllib2.HTTPSHandler(debuglevel = 1),     # be verbose on HTTPS
                                            #urllib2.HTTPHandler(debuglevel = 1),      # be verbose on HTTP
                                            urllib2.HTTPSHandler(),
                                            HTTPRefererHandler,                       # add Referer header on redirect
                                            urllib2.HTTPCookieProcessor(cookies))     # keep cookies

        else:
            self.opener = urllib2.build_opener(
                                            #urllib2.HTTPSHandler(debuglevel = 1),     # be verbose on HTTPS
                                            #urllib2.HTTPHandler(debuglevel = 1),      # be verbose on HTTP
                                            urllib2.HTTPSHandler(),
                                            HTTPRefererHandler,                       # add Referer header on redirect
                                            urllib2.HTTPCookieProcessor(cookies))     # keep cookies

    def requestFlyoutPage(self):
        """
        Returns bing.com flyout page
        This page shows what rewarding activity can be performed in
        order to earn Bing points
        """
        url = self.BING_FLYOUT_PAGE
        request = urllib2.Request(url = url, headers = self.httpHeaders)

# commenting the line below, because on 10/25/2013 Bing! started to return an empty flyout page if referer is other than http://www.bing.com
        #request.add_header("Referer", "http://www.bing.com/rewards/dashboard")

        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)
        return page

    def decodeDashBoard(self):
        url = "https://account.microsoft.com/rewards"
        request = urllib2.Request(url = url, headers = self.httpHeaders)
        request.add_header("Referer", bingCommon.BING_URL)
        page = ""
        with self.opener.open(request) as response:
            referer = response.geturl()
            page = helpers.getResponseBody(response)
        try:
            # get form data
            s = page.index('action="')
            s += len('action="')
            e = page.index('"', s)
            action = page[s:e]

            # could raise error for non-encrypted
            s = page.index("NAP")
            s = page.index('value="', s)
            s += len('value="')
            e = page.index('"', s)
            nap = page[s:e]

            s = page.index("ANON")
            s = page.index('value="', s)
            s += len('value="')
            e = page.index('"', s)
            anon = page[s:e]

            s = page.index('id="t"')
            s = page.index('value="', s)
            s += len('value="')
            e = page.index('"', s)
            t = page[s:e]

            postFields = urllib.urlencode({
                "NAP"    : nap,
                "ANON"   : anon,
                "t"      : t
            })

            request = urllib2.Request(action, postFields, self.httpHeaders)
            request.add_header("Referer", referer)
            with self.opener.open(request) as response:
                page = helpers.getResponseBody(response)
        except ValueError:
            # Ignore valueerror
            pass

        status = [[tag] for tag in ["Browse", "Mobile", "PC"] if tag in page]
        for n, tup in enumerate(RE_DASHBD_POINTS.findall(page)):
            # print tuple of completion
            if len(status[0]) == 1:
                status[0].append(tup)
                continue
            if tup[1] == '150' and len(status[2]) == 1:
                status[2].append(tup)
                continue
            if tup[1] == '100':
                status[1].append(tup)
                continue
        return page, status

    def getLifetimeCredits(self):
        """
        Returns https://account.microsoft.com/rewards Lifetime Credits
        The number of credits earned since day one of the account
        """
        (page, status) = self.decodeDashBoard()

# find lifetime points
        s = page.find(' lifetime points</div>') - 20
        s = page.find('>', s) + 1
        e = page.find(' ', s)
        points = page[s:e]

        return int(points.replace(",", "")) # remove commas so we can cast as int

    def getRewardsPoints(self):
        """
        Returns rewards points as int
        """
# report activity
        postFields = urllib.urlencode( { "url" : bingCommon.BING_URL, "V" : "web" } )
        url = "http://www.bing.com/rewardsapp/reportActivity"
        request = urllib2.Request(url, postFields, self.httpHeaders)
        request.add_header("Referer", bingCommon.BING_URL)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)

        if len(page) == 0:
            raise Exception("Rewards points page is empty. That could mean you are not signed up for rewards with this account")

         # There are instances where the account appears to be signed in, but really is not
        helpers.errorOnText(page, "You are not signed", "Temporary account ban: User was not successfully signed in.\n")

# parse activity page
        s = page.index("t.innerHTML='")
        s += len("t.innerHTML='")
        e = page.index("'", s)
        rewardsText = page[s:e]
        if rewardsText == 'Rewards': # The account is banned
            raise helpers.BingAccountError("Banned from BingRewards: Could not get the number of rewards.")
        else:
            return int(rewardsText)

    def __processHit(self, reward):
        """Processes bfp.Reward.Type.Action.HIT and returns self.RewardResult"""
        res = self.RewardResult(reward)
        pointsEarned = self.getRewardsPoints()
        request = urllib2.Request(url = reward.url, headers = self.httpHeaders)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)
        pointsEarned = self.getRewardsPoints() - pointsEarned
# if HIT is against bfp.Reward.Type.RE_EARN_CREDITS - check if pointsEarned is the same to
# pointsExpected
        indCol = bfp.Reward.Type.Col.INDEX
        if reward.tp[indCol] == bfp.Reward.Type.RE_EARN_CREDITS[indCol]:
            matches = bfp.Reward.Type.RE_EARN_CREDITS[bfp.Reward.Type.Col.NAME].search(reward.name)
            pointsExpected = int(matches.group(1))
            if pointsExpected != pointsEarned:
                filename = helpers.dumpErrorPage(page)
                res.isError = True
                res.message = "Expected to earn " + str(pointsExpected) + " points, but earned " + \
                              str(pointsEarned) + " points. Check " + filename + " for further information"
        return res

    def __processWarn(self, reward):
        """Processes bfp.Reward.Type.Action.WARN and returns self.RewardResult"""
        res = self.RewardResult(reward)

        if reward.isAchieved():
            res.message = "This reward has been already achieved"
            return res

        pointsEarned = self.getRewardsPoints()
        request = urllib2.Request(url = reward.url, headers = self.httpHeaders)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)
        pointsEarned = self.getRewardsPoints() - pointsEarned
# check if we earned any points
        if pointsEarned < 1:
            res.isError = True
            res.message = "Didn't earn any points for click"
        return res

    def __processSearch(self, reward, verbose):
        """Processes bfp.Reward.Type.Action.SEARCH and returns self.RewardResult"""

        BING_QUERY_URL = 'http://www.bing.com/search?q='
        BING_QUERY_SUCCESSFULL_RESULT_MARKER_PC = '<div id="b_content">'
        BING_QUERY_SUCCESSFULL_RESULT_MARKER_MOBILE = '<div id="content">'
        IG_PING_LINK = "http://www.bing.com/fd/ls/GLinkPing.aspx"
        IG_NUMBER_PATTERN = re.compile(r'IG:"([^"]+)"')
        IG_SEARCHES_PATTERN = re.compile(r'<li\s[^>]*class="b_algo"[^>]*><h2><a\s[^>]*href="(http[^"]+)"\s[^>]*h="([^"]+)"')
        status = None
        res = self.RewardResult(reward)

        indCol = bfp.Reward.Type.Col.INDEX

# get a set of queries from today's Bing! history
        url = bingHistory.getBingHistoryTodayURL()
        request = urllib2.Request(url = url, headers = self.httpHeaders)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)
        history = bingHistory.parse(page)
        try:
            (page, status) = self.decodeDashBoard()
            reward.progressCurrent, reward.progressMax = 150, 150
            if status[1][1][0] == '0':
                reward.progressCurrent, reward.progressMax = status[1][1]
                reward.tp = bfp.Reward.Type.SEARCH_MOBILE
            else:
                reward.progressCurrent, reward.progressMax = status[2][1]
                reward.tp = bfp.Reward.Type.SEARCH_PC
            reward.progressCurrent, reward.progressMax = int(reward.progressCurrent), int(reward.progressMax)
        except IndexError:
            print status
            # let BFP handle it when dashboard is bad
        except ValueError:
            # let BFP handle it when dashboard is bad
            print status

        # above replace the BFP isAchieved() because the scoreboard has higher accuracy
        if reward.isAchieved():
            res.message = "This reward has been already achieved"
            return res

        if re.search("earning.*free.*credits", reward.description):
            maxRewardsCount = 12
            rewardsCount    = 30
            rewardCost      = 1 # Looks like it's now always X points per one search
            searchesCount = maxRewardsCount * rewardCost / rewardsCount

        else:
# find out how many searches need to be performed
            matches = bfp.Reward.Type.SEARCH_AND_EARN_DESCR_RE.search(reward.description)
            if matches is None:
                print "No RegEx matches found for this search and earn"
                res.isError = True
                res.message = "No RegEx matches found for this search and earn"
                return res
            maxRewardsCount = int(matches.group(1))
            rewardsCount    = int(matches.group(2))
            rewardCost      = 1 # Looks like it's now always X points per one search
            searchesCount = maxRewardsCount * rewardCost / rewardsCount

# adjust to the current progress
# reward.progressCurrent is now returning current points, not current searches
# so divide it by points per search (rewardsCount) to get correct search count needed
        searchesCount -= (reward.progressCurrent * rewardCost) / rewardsCount
        if searchesCount < 0:
            res.isError = True
            res.message = "Not searchable"
            return res

        headers = self.httpHeaders

        if reward.tp == bfp.Reward.Type.SEARCH_PC or reward.tp == bfp.Reward.Type.SEARCH_AND_EARN:
            headers["User-Agent"] = self.userAgents.pc
            searchesCount += self.addSearchesDesktop + random.randint(0, self.addSearchesDesktopSalt)
            print
            print "Running PC searches"
            print
        elif reward.tp == bfp.Reward.Type.SEARCH_MOBILE:
            headers["User-Agent"] = self.userAgents.mobile
            searchesCount += self.addSearchesMobile + random.randint(0, self.addSearchesMobileSalt)
            print
            print "Running mobile searches"
            print
        else:
            res.isError = True
            res.message = "Don't know how to process this search"
            return res

        if verbose:
            print("User-Agent: {0}".format(bingCommon.HEADERS["User-Agent"]))
            print

        # Import the query generator
        try:
            qg = importlib.import_module(self.queryGenerator, package=None)
            queryGenerator = qg.queryGenerator(self)
        except ImportError:
            raise TypeError("{0} is not a module".format(self.queryGenerator))

        # generate a set of queries to run
        queries = queryGenerator.generateQueries(searchesCount, history)

        if len(queries) < searchesCount:
            print "Warning: not enough queries to run were generated!"
            print "Requested:", searchesCount
            print "Generated:", len(queries)

        successfullQueries = 0
        i = 1
        totalQueries = len(queries)

        for query in queries:
            if i > 1:
# sleep some time between queries (don't worry Bing! ;) )
                t = self.betweenQueriesInterval + random.uniform(0, self.betweenQueriesSalt)
                time.sleep(t)

            url = BING_QUERY_URL + urllib.quote_plus(query.encode('utf-8'))

            print "%s - %2d/%2d - Search: %s" % (helpers.getLoggingTime(), i, totalQueries, query)

            request = urllib2.Request(url = url, headers = bingCommon.HEADERS)
            with self.opener.open(request) as response:
                page = helpers.getResponseBody(response)

# check for the successfull marker
            found = page.find(BING_QUERY_SUCCESSFULL_RESULT_MARKER_PC) != -1 \
                 or page.find(BING_QUERY_SUCCESSFULL_RESULT_MARKER_MOBILE) != -1

            if not found:
                filename = helpers.dumpErrorPage(page)
                print "Warning! Query:"
                print "\t" + query
                print "returned no results, check " + filename + " file for more information"

            else:
                successfullQueries += 1

                # randomly open a link
                if self.openLinkChance > random.random():
                    # get IG number
                    ig_number = IG_NUMBER_PATTERN.search(page)
                    if ig_number is not None:
                        ig_number = ig_number.group(1)
                        ig_searches = IG_SEARCHES_PATTERN.findall(page)
                        # make sure we have at least 1 search
                        if len(ig_searches) > 0:
                            # get a random link to open
                            ig_max_rand = min(self.openTopLinkRange, len(ig_searches) - 1)
                            # number of the link we will use
                            ig_link_num = random.randint(0, ig_max_rand)
                            ig_link = "{0}?IG={1}&{2}".format(
                                IG_PING_LINK,
                                urllib.quote_plus(ig_number),
                                urllib.quote_plus(ig_searches[ig_link_num][1])
                            )

                            # sleep a reasonable amount of time before clicking the link
                            # use defaults to save space in config
                            t = random.uniform(0.75, 3.0)
                            time.sleep(t)

                            # open the random link
                            request = urllib2.Request(url = ig_link, headers = bingCommon.HEADERS)
                            request.headers["Referer"] = response.url
                            self.opener.open(request)

                            if verbose:
                                print("Followed Link {}".format(ig_link_num + 1))
                        else:
                            filename = helpers.dumpErrorPage(page)
                            print "Warning! No searches were found on search results page"
                            print "Check {0} file for more information".format(filename)
                    else:
                        filename = helpers.dumpErrorPage(page)
                        print "Warning! Could not find search result IG number"
                        print "Check {0} file for more information".format(filename)

            i += 1

        if successfullQueries < searchesCount:
            res.message = str(successfullQueries) + " out of " + str(searchesCount) + " requests were successfully processed"
        else:
            res.message = "All " + str(successfullQueries) + " requests were successfully processed"

        # reset header to pc so pc pages return in getting life time points
        headers["User-Agent"] = self.userAgents.pc

        return res

    def process(self, rewards, verbose):
        """
        Runs an action for each of rewards as described in self.RewardType
        returns results list of self.RewardResult objects
        """
        if rewards is None or not isinstance(rewards, list):
            raise TypeError("rewards is not an instance of list")

        results = []

        for r in rewards:
            if r.tp is None:
                action = bfp.Reward.Type.Action.WARN
            else:
                action = r.tp[bfp.Reward.Type.Col.ACTION]

            if action == bfp.Reward.Type.Action.HIT:
                res = self.__processHit(r)
            elif action == bfp.Reward.Type.Action.WARN:
                res = self.__processWarn(r)
            elif action == bfp.Reward.Type.Action.SEARCH:
                res = self.__processSearch(r, verbose)
            else:
                res = self.RewardResult(r)

            res.action = action
            results.append(res)

        return results

    def __printReward(self, reward):
        """Prints a reward"""
        print "name        : %s" % reward.name
        if reward.url != "":
            print "url         : %s" % reward.url
        if reward.progressMax != 0:
            print "progressCur : %d" % reward.progressCurrent
            print "progressMax : %d" % reward.progressMax
            print "progress %%  : %0.2f%%" % reward.progressPercentage()
        if reward.isDone:
            print "is done     : true"
        print "description : %s" % reward.description

    def printRewards(self, rewards):
        """
        Prints out rewards list
        throws TypeError if rewards is None or not instance of list
        """
        if rewards is None or not isinstance(rewards, list):
            raise TypeError("rewards is not an instance of list")

        i = 0
        total = len(rewards)
        for r in rewards:
            i += 1
            print "Reward %d/%d:" % (i, total)
            print "-----------"
            self.__printReward(r)
            print

    def __printResult(self, result):
        """Prints a result"""
        self.__printReward(result.o)
        if result.isError:
            print "   Error    :   true"
        print "   Message  : " + result.message
        print "   Action   : " + bfp.Reward.Type.Action.toStr(result.action)


    def printResults(self, results, verbose):
        """
        Prints out results list
        if verbose - prints all results, otherwise prints errors only
        throws TypeError if results is None or not instance of list
        """
        if results is None or not isinstance(results, list):
            raise TypeError("results is not an instance of list")

        i = 0
        total = len(results)
        for r in results:
            if verbose or r.isError:
                i += 1
                print "Result %d/%d:" % (i, total)
                print "-----------"
                self.__printResult(r)
                print
