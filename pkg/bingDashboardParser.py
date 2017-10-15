#!/usr/bin/env python2

#
# developed by Sergey Markelov (2013)
#

"""
Bing! dashboard page parser

Usage:
    from bingDashboardParser import Reward, parseDashboardPage
    ...
    bingRewards = BingRewards(FACEBOOK_EMAIL, FACEBOOK_PASSWORD)
    bingRewards.authenticate()
    parseDashboardPage(bingRewards.requestDashboardPage(), BING_URL)
"""

import re
from bs4 import BeautifulSoup
from bingFlyoutParser import RewardV1


class Reward(RewardV1):
    "A class to represent a Bing! reward"

    class Type:
        class Action:
            PASS = 0
            INFORM = 1
            HIT = 2
            SEARCH = 3
            WARN = 4

            @staticmethod
            def toStr(action):
                actions = ("pass", "inform", "hit", "search", "warn")
                return (actions[action])

        class Col:
            INDEX = 0
            NAME = 1
            DESCRIPTION = 2  # optional field, can be set to None
            ISRE = 3
            ACTION = 4

        SEARCH_AND_EARN_DESCR_RE = re.compile(r"[Uu]p to (\d+) points? (?:per day|today), (\d+) points? per search")
        # need to change this to work for hits
        EARN_CREDITS_RE = re.compile("Earn (\d+) credits?")

        #       Alias                   Index Reward.name
        #                           optional(Reward.description)                         isRe?  Action

        RE_EARN_CREDITS_PASS = (1, EARN_CREDITS_RE,
                                "Get the best of Bing by signing in with Facebook.", True, Action.PASS)
        RE_EARN_CREDITS = (2, EARN_CREDITS_RE, None, True, Action.HIT)
        SEARCH_MOBILE = (3, "Mobile search", None, False, Action.SEARCH)
        SEARCH_PC = (4, "PC search", None, False, Action.SEARCH)
        YOUR_GOAL = (5, "Your goal", None, False, Action.INFORM)
        MAINTAIN_GOLD = (6, "Maintain Gold", None, False, Action.INFORM)
        REFER_A_FRIEND = (7, "Refer-A-Friend", None, False, Action.PASS)
        SEND_A_TWEET = (8, "Send a Tweet", None, False, Action.PASS)
        RE_EARNED_CREDITS = (9, re.compile("Earned \d+ credits?"), None, True, Action.PASS)
        COMPLETED = (10, "Completed", None, False, Action.PASS)
        SILVER_STATUS = (11, "Silver Status", None, False, Action.PASS)
        INVITE_FRIENDS = (12, "Invite friends", None, False, Action.PASS)
        EARN_MORE_POINTS = (13, "Earn more points", None, False, Action.INFORM)
        SEARCH_AND_EARN = (14, "Search and earn", None, False, Action.SEARCH)
        THURSDAY_BONUS = (15, "Thursday bonus", None, False, Action.PASS)
        RE_QUIZ = (16, re.compile(r"\b[Qq]uiz\b"), None, True, Action.PASS)

        ALL = (RE_EARN_CREDITS_PASS, RE_EARN_CREDITS, SEARCH_MOBILE, SEARCH_PC, YOUR_GOAL, MAINTAIN_GOLD,
               REFER_A_FRIEND, SEND_A_TWEET, RE_EARNED_CREDITS, COMPLETED, SILVER_STATUS, INVITE_FRIENDS,
               EARN_MORE_POINTS, SEARCH_AND_EARN, THURSDAY_BONUS, RE_QUIZ)

    def __init__(self):
        self.url = ""  # optional
        self.name = ""
        self.progressCurrent = 0  # optional
        self.progressMax = 0  # optional
        self.isDone = False  # optional - is set if progress is "Done"
        self.description = ""
        self.tp = None  # is one of self.Type if set

    def isAchieved(self):
        """
        Returns True if the reward is achieved.
        Applicable only if self.progressMax is not 0
        """
        return (self.isDone or self.progressMax != 0 and self.progressCurrent == self.progressMax)

    def progressPercentage(self):
        if self.progressMax == 0:
            return 0
        else:
            return (float(self.progressCurrent) / self.progressMax * 100)


def parseDashboardPage(page, bing_url):
    """
    Parses a bing dashboard page
    returns a list of Reward objects

    page - bing dashboard page - see the class __doc__ for further information
    bing_url - url of bing main page - generally http://www.bing.com which will be
                added to Reward.url as a prefix if appropriate
    """
    if page is None: raise TypeError("page is None")
    if page.strip() == "": raise ValueError("page is empty")

    # overwrite the bing_url passed in (don't want to change it in the source file because it could be used elsewhere)


    # filter out the characters that crash BS (can probably fix this with encoding if someone wants to look into it
    soup = BeautifulSoup(
        page.replace("&#8212;", "").replace("&#10005;", "").replace("&#169;", "").replace("\u2022", "").replace(
            "\u2013", "").replace("\u2019", ""), 'html.parser')
    rewardsDashboard = soup.find('div', id="dashboard")

    allRewards = []

    # Get the rewards on the sidebar (mostly search + earn)
    for ddiv in rewardsDashboard.find_all('div', class_='spacer-32-top display-table'):
        currentReward = Reward()
        rewardURL = ''
        rewardName = ''
        rewardProgressCurrent = 0
        rewardProgressMax = 0
        rewardDescription = ''
        lnk = ddiv.find('a')
        if lnk is not None:
            # this url already starts with the bing URL, others need it to be appended
            rewardURL = lnk.get('href')
            rewardName = lnk.get_text()
        progressDiv = ddiv.find('div', class_='text-caption spacer-16-top')
        if progressDiv is not None:
            if progressDiv.get_text().find('of') != -1:
                progressStuff = progressDiv.get_text().split(' ')
                rewardProgressCurrent, rewardProgressMax = int(progressStuff[0]), int(progressStuff[2])
        descriptionDiv = ddiv.find('div', class_='spacer-12-top')
        if descriptionDiv is not None:
            rewardDescription = descriptionDiv.get_text()
        createReward(currentReward, rewardURL, rewardName, rewardProgressCurrent, rewardProgressMax, rewardDescription)
        allRewards.append(currentReward)

    # Get the rewards on the main dashboard page
    dashboardOnly = rewardsDashboard.find('div', class_='card-row spacer-32-bottom clearfix')
    links = dashboardOnly.find_all('a')
    i = 0
    while i < len(links):
        currentReward = Reward()
        rewardURL = ''
        rewardName = ''
        rewardProgressCurrent = 0
        rewardProgressMax = 0
        rewardDescription = ''
        # need to append the bing url here
        rewardURL = bing_url + links[i].get('href')
        rewardName = links[i].find('div', class_='offer-title-height')
        # if this reward has not been started
        rewardDescription = links[i].find('div', class_='offer-description-height spacer-20-top ')
        # 'HIT' rewards will have their point total in this field
        currAction = links[i].find('span', class_='pull-left card-button-line-height margin-right-15')
        # if the reward is a quiz and partially complete
        if rewardDescription is None:
            rewardDescription = links[i].find('div', class_='text-caption progress-text-height clearfix')
            if rewardDescription.get_text().find('of') != -1:
                progressStuff = rewardDescription.get_text().split(' ')
                rewardProgressCurrent, rewardProgressMax = int(progressStuff[0]), int(progressStuff[2])
                # also need to find the new description here
                rewardDescription = links[i].find('div',
                                                  class_='offer-description-height spacer-20-top offer-description-margin-bottom')
                # if the reward is a quiz and fully complete
        if rewardDescription.get_text().find('You did it!') != -1:
            rDscSplit = rewardDescription.get_text().split(' ')
            rewardProgressCurrent = rewardProgressMax = int(rDscSplit[rDscSplit.index('points.') - 1])
            # Grab the point totals for 'HIT' rewards - we're using these as a marker to set the 'HIT' type
        hits = checkForHit(currAction, rewardProgressCurrent, rewardProgressMax, links[i])
        if hits is not None:
            rewardProgressCurrent, rewardProgressMax = hits[0], hits[1]
        createReward(currentReward, rewardURL, rewardName.get_text(), rewardProgressCurrent, rewardProgressMax,
                     rewardDescription.get_text())
        allRewards.append(currentReward)
        i += 1

    # Get the top feature reward (top spot on the dashboard) - doing this separately since it's hard to parse as part of the dashboard
    # first link on the dashboard will be the top spot
    currentReward = Reward()
    rewardURL = ''
    rewardName = ''
    rewardProgressCurrent = 0
    rewardProgressMax = 0
    rewardDescription = ''
    topLink = rewardsDashboard.find('a')
    # need to append the bing url here
    rewardURL = bing_url + topLink.get('href')
    rewardName = topLink.find('div', class_='offer-title-height')
    rewardDescription = topLink.find('div', class_='offer-description-height spacer-20-top ')
    # if the reward is a quiz and partially complete
    if rewardDescription is None:
        rewardDescription = topLink.find('div', class_='text-caption progress-text-height clearfix')
        if rewardDescription.get_text().find('of') != -1:
            progressStuff = rewardDescription.get_text().split(' ')
            rewardProgressCurrent, rewardProgressMax = int(progressStuff[0]), int(progressStuff[2])

            # also need to find the new description here
            rewardDescription = topLink.find('div',
                                             class_='offer-description-height spacer-20-top offer-description-margin-bottom')
    # if the reward is a quiz and fully complete
    if rewardDescription.get_text().find('You did it!') != -1:
        rDscSplit = rewardDescription.get_text().split(' ')
        rewardProgressCurrent = rewardProgressMax = int(rDscSplit[rDscSplit.index('points.') - 1])
    currAction = topLink.find('span', class_='pull-left card-button-line-height margin-right-15')
    # Grab the point totals for 'HIT' rewards - we're using these as a marker to set the 'HIT' type
    hits = checkForHit(currAction, rewardProgressCurrent, rewardProgressMax, topLink)
    if hits is not None:
        rewardProgressCurrent, rewardProgressMax = hits[0], hits[1]
    createReward(currentReward, rewardURL, rewardName.get_text(), rewardProgressCurrent, rewardProgressMax,
                 rewardDescription.get_text())
    allRewards.append(currentReward)

    return allRewards


def checkForHit(currAction, rewardProgressCurrent, rewardProgressMax, searchLink):
    if currAction is not None:
        if rewardProgressCurrent == 0 and rewardProgressMax == 0:
            if currAction.get_text().lower().find('points') != -1:
                rewardProgressMax = int(currAction.get_text().split(' ')[0])
                # Use the button div to determine whether the offer has been completed
                btn = searchLink.find('div',
                                      class_='card-button-height text-caption text-align-center offer-complete-card-button-background border-width-2 offer-card-button-background')
                if btn is not None:
                    rewardProgressCurrent = rewardProgressMax
                return [rewardProgressCurrent, rewardProgressMax]


def createReward(reward, rUrl, rName, rPC, rPM, rDesc):
    reward.url = rUrl.strip()
    reward.name = rName.strip()
    reward.progressCurrent = rPC
    reward.progressMax = rPM
    reward.description = rDesc.strip()
    if rPC == rPM:
        reward.isDone = True

    for t in Reward.Type.ALL:
        if t[Reward.Type.Col.ISRE]:  # regex
            if t[Reward.Type.Col.NAME].search(reward.name) \
                    and (t[Reward.Type.Col.DESCRIPTION] is None \
                                 or t[Reward.Type.Col.DESCRIPTION] == reward.description):
                reward.tp = t

        elif t[Reward.Type.Col.NAME].lower() == reward.name.lower() \
                and (t[Reward.Type.Col.DESCRIPTION] is None \
                             or t[Reward.Type.Col.DESCRIPTION] == reward.description):
            reward.tp = t

        # for 'HIT' rewards (10 points) we assume 10 points, higher values won't be triggered
        # To determine whether a hit is already complete, there is logic above to check which div the button uses + the comparison below
        if reward.progressMax == 10 and reward.progressCurrent != 10:
            reward.tp = Reward.Type.RE_EARN_CREDITS
