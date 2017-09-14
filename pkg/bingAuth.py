#
# developed by Sergey Markelov (2013)
#

import random
import urllib
import urllib2
import re
import time
import json

import bingCommon
import helpers

class AuthenticationError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class BingAuth:
    inputNameValue = re.compile(r"<input.+?name=\"(.+?)\".+?value=\"(.+?)\"")
    formAction = re.compile(r"<form.+action=\"(.+?)\"")
    ppftValue = re.compile(r"sFTTag:'.+value=\"(.+?)\"")
    ppsxValue = re.compile(r":'(Pa?s?s?p?o?r?t?R?N?)'")
    winLiveId = re.compile(r"\"WindowsLiveId\":\"(.+?)\"")
    urlPostValue = re.compile(r"urlPost:'(.+?)'")

    def __init__(self, httpHeaders, opener):
        """
        @param opener is an instance of urllib2.OpenerDirector
        """
        if opener is None or not isinstance(opener, urllib2.OpenerDirector):
            raise TypeError("opener is not an instance of urllib2.OpenerDirector")

        self.opener = opener
        self.httpHeaders = httpHeaders

    def authenticate(self, authType, login, password):
        """
        throws ValueError if login or password is None
        throws AuthenticationError
        """
        if login is None: raise ValueError("login is None")
        if password is None: raise ValueError("password is None")

        """
        Authenticates a user on bing.com with his/her Live account.

        throws AuthenticationError if authentication can not be passed
        throws urllib2.HTTPError if the server couldn't fulfill the request
        throws urllib2.URLError if failed to reach the server
        """
        # request http://www.bing.com
        request = urllib2.Request(url = bingCommon.BING_URL, headers = self.httpHeaders)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)

        # get connection URL for provider Live
        urlSearch = self.winLiveId.search(page)
        if urlSearch == None:
            raise AuthenticationError("Could not find variable 'WindowsLiveId' on Live login page")
        url = urlSearch.group(1).decode("unicode_escape")

        request = urllib2.Request(url = url, headers = self.httpHeaders)
        request.add_header("Referer", bingCommon.BING_URL)
        with self.opener.open(request) as response:
            referer = response.geturl()
            page = helpers.getResponseBody(response)

        # get PPFT parameter
        PPFTSearch = self.ppftValue.search(page)
        if PPFTSearch == None:
            raise AuthenticationError("Could not find variable 'PPFT' on Live login page")
        PPFT = PPFTSearch.group(1)

        # get PPSX parameter
        ppsxSearch = self.ppsxValue.search(page)
        if ppsxSearch == None:
            raise AuthenticationError("Could not find PassportRN variable on Live login page")
        PPSX = ppsxSearch.group(1)

        # generate ClientLoginTime
        clt = 20000 + int(random.uniform(0, 1000))

        # get url to post data to
        urlSearch = self.urlPostValue.search(page)
        if urlSearch == None:
            raise AuthenticationError("Could not find variable 'urlPost' on Live login page")
        url = urlSearch.group(1)

        timestamp = int(round(time.time() * 1000))
        # TODO: randomize times a bit?
        i16 = json.dumps({
            "navigationStart": timestamp,
            "unloadEventStart": timestamp + 209,
            "unloadEventEnd": timestamp + 210,
            "redirectStart": 0,
            "redirectEnd": 0,
            "fetchStart": timestamp + 73,
            "domainLookupStart": timestamp + 73,
            "domainLookupEnd": timestamp + 130,
            "connectStart": timestamp + 130,
            "connectEnd": timestamp + 130,
            "secureConnectionStart": timestamp + 210,
            "requestStart": timestamp + 183,
            "responseStart": timestamp + 205,
            "responseEnd": timestamp + 205,
            "domLoading": timestamp + 208,
            "domInteractive": timestamp + 406,
            "domContentLoadedEventStart": timestamp + 420,
            "domContentLoadedEventEnd": timestamp + 420,
            "domComplete": timestamp + 422,
            "loadEventStart": timestamp + 422,
            "loadEventEnd": 0
        })

        postFields = urllib.urlencode({
            "loginfmt"      : login,
            "login"         : login,
            "passwd"        : password,
            "type"          : "11",
            "PPFT"          : PPFT,
            "PPSX"          : str(PPSX),
            "LoginOptions"  : "3",
            "FoundMSAs"     : "",
            "fspost"        : "0",
            "NewUser"       : "1",
            "i2"            : "1",                  # ClientMode
            "i13"           : "0",                  # ClientUsedKMSI
            "i16"           : i16,
            "i19"           : str(clt),             # ClientLoginTime
            "i21"           : "0",
            "i22"           : "0",
            "i17"           : "0",                  # SRSFailed
            "i18"           : "__DefaultLogin_Strings|1,__DefaultLogin_Core|1," # SRSSuccess
        })

        # get Passport page
        request = urllib2.Request(url, postFields, self.httpHeaders)
        request.add_header("Referer", referer)
        with self.opener.open(request) as response:
            referer = response.geturl()
            page = helpers.getResponseBody(response)

        # Checking for bad usernames and password
        helpers.errorOnText(page, "That password is incorrect.", "Authentication has not been passed: Invalid password")
        helpers.errorOnText(page, "That Microsoft account doesn't exist", "Authentication has not been passed: Invalid username")
        # check if there is a new terms of use
        helpers.errorOnText(page, "//account.live.com/tou/accrue", "Please log in (log out first if necessary) through a browser and accept the Terms Of Use")

        contSubmitUrl = self.formAction.search(page)
        if contSubmitUrl == None:
            raise AuthenticationError("Could not find form action for continue page")
        url = contSubmitUrl.group(1)

        # get all form inputs
        formFields = self.inputNameValue.findall(page)
        postFields = {}
        for field in formFields:
            postFields[field[0]] = field[1]
        postFields = urllib.urlencode(postFields)

        # submit continue page
        request = urllib2.Request(url, postFields, self.httpHeaders)
        request.add_header("Referer", referer)
        with self.opener.open(request) as response:
            referer = response.geturl()
            page = helpers.getResponseBody(response)

        request = urllib2.Request(url = bingCommon.BING_URL, headers = self.httpHeaders)
        request.add_header("Referer", referer)
        with self.opener.open(request) as response:
            referer = response.geturl()

            # if that's not bingCommon.BING_URL => authentication wasn't pass => write the page to the file and report
            if referer.find(bingCommon.BING_URL) == -1:
                try:
                    filename = helpers.dumpErrorPage(helpers.getResponseBody(response))
                    s = "check {} file for more information".format(filename)
                except IOError:
                    s = "no further information could be provided - failed to write a file into {} subfolder".format(helpers.RESULTS_DIR)
                raise AuthenticationError("Authentication has not been passed:\n{}".format(s))
