#!/usr/bin/env python -B

#
# developed by kenneyhe@gmail.com (2017)
#


import sys
import os
import main
from pathos.multiprocessing import ProcessingPool
import re

sys.path.append(os.path.join(os.path.dirname(__file__), "pkg"))
sys.path.append(os.path.join(os.path.dirname(__file__), "pkg", "queryGenerators"))


from config import Config

PATTERN_SEL = re.compile(r'<login.*?>(.+?)</login>', re.MULTILINE)
PATTERN_ACCS = re.compile(r'<accounts>(.+?)</accounts>', re.MULTILINE)
PATTERN_ACC = re.compile(r'<account.*?>(.+?)</account>', re.MULTILINE)
PATTERN_REFS = re.compile(r'<account ref.*Live_.*</account>', re.MULTILINE)
PATTERN_REF = re.compile(r'<account ref.*Live_.*</account> |.*', re.MULTILINE)


def run_v1(config):
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
    return pool.map(helper, runlist)


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
    try:
        accounts = PATTERN_REFS.findall(newXML)[0]
        for account in PATTERN_REF.findall(accounts):
            if selector in account:
                break
        newXML = PATTERN_REFS.sub(account, newXML)
    except IndexError, e:
        # do not care if no ref
        pass
    return newXML


def helper(args):
    """
    return XML string for running just that account
    :param XMLString: XML with all account
    :param selector:
    :return:
    """
    class runnable:
        def __init__(self):
            self.config = Config()

    [xml, selector] = args
    newXML = replace(xml, selector)
    run = runnable()
    run.config.parseFromString(newXML)
    run_v1(run.config)

if __name__ == "__main__":
    if len(sys.argv) > 1 and int(sys.argv[1])> 0:
        run(int(sys.argv[1]), "config.xml")
    else:
        run(1, "config.xml")