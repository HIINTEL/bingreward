#!/usr/bin/env python2

#
# Wikipedia queries generator
# developed by Alex Mayer (2014)
#

import re
import helpers
import urllib2
from random import randint
from datetime import date
from bingRewards import BingRewards

month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
QUERY_URL = "http://en.wikipedia.com/wiki/{0}_{1}".format(month_names[date.today().month - 1], date.today().strftime("%d"))

class queryGenerator:
    def __init__(self, br):
        """
        param br is a pointer to the calling class bingRewards (used for variables)
        """
        if br is None or not isinstance(br, BingRewards):
            raise ValueError("br is not set or is not an instance of BingRewards")
        self.bingRewards = br

    def generateQueries(self, queriesToGenerate, history, maxQueryLen = None):
        """
        Parses the current days wikipedia.com page and generates queries
        from the links on the page.

        param queriesToGenerate the number of queries to return
        param history a set of previous searches
        param maxQueryLen the maximum query length

        returns a set of queries - self.queries
        """
        if queriesToGenerate <= 0:
            raise ValueError("numberOfQueries should be more than 0, but it is %d" % queriesToGenerate)
        if history is None or not isinstance(history, set):
            raise ValueError("history is not set or not an instance of set")

        request = urllib2.Request(url = QUERY_URL, headers = self.bingRewards.httpHeaders)
        with self.bingRewards.opener.open(request) as response:
            page = helpers.getResponseBody(response)

        if page.strip() == "": raise ValueError("wikipedia page is empty")

        # get rid of new lines
        page = page.replace("\n", "")
        # seperate out the guts of the article
        page = re.search('id="Events"(.+?)id="External_links"', page, re.I)
        if page == None:
            raise ValueError("wiki page has no contents")
        # seperate out each result
        searchTerms = re.findall(r'<li.+?<a href="/wiki/.+?".*?>([a-zA-Z\s]+?)</a>.*?</li>', page.group(1))

        queries = set()
        queriesNeeded = queriesToGenerate
        while queriesNeeded > 0 and len(searchTerms) > 0:
            ri = randint(0, len(searchTerms) - 1)
            # ignore things in your history
            if searchTerms[ri] in history:
                del searchTerms[ri]
                continue
            queries.add(searchTerms[ri])
            del searchTerms[ri]
            queriesNeeded -= 1

        return queries
