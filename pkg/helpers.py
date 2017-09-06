#!/usr/bin/python2.7 -B

#
# developed by Sergey Markelov (2013)
#

import StringIO
import zlib
import gzip
import os
import errno
from datetime import datetime
import sys

class BingAccountError(ValueError):
    def __init__(self, message):
        Exception.__init__(self, message)

RESULTS_DIR = "result/"

def getXmlChildNodes(xmlNode):
    childNodes = None
    version = sys.version_info
    if version[0] == 2 and version[1] < 7:
        childNodes = xmlNode.getchildren()
    else:
        childNodes = list(xmlNode)
    return childNodes

def getLoggingTime():
    dt = datetime.now()
    dtStr = dt.strftime("%Y-%m-%d %H:%M:%S") + "." + str(dt.microsecond / 100000)
    return dtStr

def createResultsDir(f):
    """
    Creates results dir where all output will go based on
    __file__ object which is passed through f

    Note: results dir is created with 755 mode

    RESULTS_DIR global variable will be updated
    """
    global RESULTS_DIR
    scriptDir = os.path.dirname(os.path.realpath(f))
    resultsDir = scriptDir + "/" + RESULTS_DIR
    try:
        os.makedirs(resultsDir, 0o755)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise
    RESULTS_DIR = resultsDir


def getResponseBody(response):
    """ Returns response.read(), but does gzip deflate if appropriate"""

    encoding = response.info().get("Content-Encoding")

    if encoding in ("gzip", "x-gzip", "deflate"):
        page = response.read()
        if encoding == "deflate":
            return zlib.decompress(page)
        else:
            fd = StringIO.StringIO(page)
            try:
                data = gzip.GzipFile(fileobj = fd)
                try:     content = data.read()
                finally: data.close()
            finally:
                fd.close()
            return content
    else:
        return response.read()

def dumpErrorPage(page):
    """
    Dumps page into a file. The resulting file is placed into RESULTS_DIR subfolder
    with error_dtStr.html name, where dtStr is current date and time with
    microseconds precision

    returns filename
    """
    if page is None: raise TypeError("page is None")

    dtStr = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
    filename = "error_" + dtStr + ".html"
    with open(RESULTS_DIR + filename, "w") as fd:
        fd.write(page)

    return filename

def errorOnText(page, query_string, err):
    p = page.find(query_string)
    if p != -1:
        raise BingAccountError(err)
