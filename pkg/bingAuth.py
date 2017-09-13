#
# developed by Sergey Markelov (2013)
#

import HTMLParser
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

class HTMLFormInputsParser(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.inputs = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            name = value = ''
            for attr in attrs:
                if attr[0] == 'name':
                    name = attr[1]
                elif attr[0] == 'value':
                    value = attr[1]
            if name != '' and value != '':
                self.inputs[name] = value.encode("utf-8")

class BingAuth:

    inputNameValue = re.compile(r"<input.+?name=\"(.+?)\".+?value=\"(.+?)\"")
    formAction = re.compile(r"<form.+action=\"(.+?)\"")
    ppsxValue = re.compile(r",r:'(.+?)',")


    def __init__(self, httpHeaders, opener):
        """
        @param opener is an instance of urllib2.OpenerDirector
        """
        if opener is None or not isinstance(opener, urllib2.OpenerDirector):
            raise TypeError("opener is not an instance of urllib2.OpenerDirector")

        self.opener = opener
        self.httpHeaders = httpHeaders

    @staticmethod
    def _escapeString(s):
        t = (
            # encoding          marker
            ( 'unicode_escape', re.compile("\\\\u[0-9a-fA-F]{4}") ),
            ( 'string-escape',  re.compile("\\\\x[0-9a-fA-F]{2}") )
        )

        for encoding, marker in t:
            if marker.search(s):
                return s.decode(encoding)

        raise AuthenticationError( "s = '%s' can not be decoded with these encodings: [ %s ]" % ( s, ", ".join( ( e for e, m in t ) ) ) )

    def __authenticateFacebook(self, login, password):
        """
        Authenticates a user on bing.com with his/her Facebook account.

        throws AuthenticationError if authentication can not be passed
        throws HTMLParser.HTMLParseError
        throws urllib2.HTTPError if the server couldn't fulfill the request
        throws urllib2.URLError if failed to reach the server
        """
        raise ValueError("Not supported")

    def __authenticateLive(self, login, password):
        """
        Authenticates a user on bing.com with his/her Live account.

        throws AuthenticationError if authentication can not be passed
        throws urllib2.HTTPError if the server couldn't fulfill the request
        throws urllib2.URLError if failed to reach the server
        """
#        print "Requesting bing.com"

# request http://www.bing.com
        request = urllib2.Request(url = bingCommon.BING_URL, headers = self.httpHeaders)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)

# get connection URL for provider Live
        s = page.index('"WindowsLiveId":"')
        s += len('"WindowsLiveId":"')
        e = page.index('"', s)

        url = BingAuth._escapeString(page[s:e])

        request = urllib2.Request(url = url, headers = self.httpHeaders)
        request.add_header("Referer", bingCommon.BING_URL)
        with self.opener.open(request) as response:
            referer = response.geturl()
# get Facebook authenctication form action url
            page = helpers.getResponseBody(response)

# get PPFT parameter
        s = page.index("sFTTag")
        s = page.index('value="', s)
        s += len('value="')
        e = page.index('"', s)
        PPFT = page[s:e]

        PPSXs = ["P","Pa","Pas","Pass","Passp","Passpo","Passpor","Passport","PassportR","PassportRN"]
        PPSX = random.choice(PPSXs)

# generate ClientLoginTime
        clt = 20000 + int(random.uniform(0, 1000))

# get url to post data to
        s = page.index(",urlPost:'")
        s += len(",urlPost:'")
        e = page.index("'", s)
        url = page[s:e]

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
        helpers.errorOnText(page, 'That password is incorrect.', 'Authentication has not been passed: Invalid password')
        helpers.errorOnText(page, "That Microsoft account doesn\\'t exist", 'Authentication has not been passed: Invalid username')
        # check if there is a new terms of use
        helpers.errorOnText(page, '//account.live.com/tou/accrue', 'Please log in (log out first if necessary) through a browser and accept the Terms Of Use')

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
                    s = "check " + filename + " file for more information"
                except IOError:
                    s = "no further information could be provided - failed to write a file into " + \
                        helpers.RESULTS_DIR + " subfolder"
                raise AuthenticationError("Authentication has not been passed:\n" + s)

    def authenticate(self, authType, login, password):
        """
        throws ValueError if login or password is None
        throws AuthenticationError
        """
        if login is None: raise ValueError("login is None")
        if password is None: raise ValueError("password is None")

        try:
            authMethod = getattr(self, "_" + self.__class__.__name__ + "__authenticate" + authType)
        except AttributeError:
            raise AuthenticationError("Configuration Error: authentication type " + authType + " is not supported")

        authMethod(login, password)
