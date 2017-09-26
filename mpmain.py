#!/usr/bin/env python -B

#
# developed by kenneyhe@gmail.com (2017)
#
# pragma: no cover
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
    """
    run 3.x script's main.__run(config)
    :param config:
    :return:
    """
    return main.__run(config)


def run(nodes=1, filename="config.xml"):
    """
    Dispatch Wrapper to run xml by dispatching each login to a multiprocess pool
    :param nodes: sys argument 1
    :param filename: (determine) by sys argument 2
    :return: array of status of pool
    """
    file_xml = ""
    with open(filename, "r") as fd:
        lines = fd.readlines()
        for line in lines:
            file_xml += line
    xml = " ".join(file_xml.rsplit())

    pool = ProcessingPool(nodes)
    run_list = [[xml, value] for value in PATTERN_SEL.findall(xml)]
    return pool.map(helper, run_list)


def replace(xml, selector):
    """
    replace xml accounts with only selector inside
    :param xml: original xml
    :param selector: login user
    :return: xml file for just login user
    """
    new_xml = " ".join(xml.rsplit())
    accounts = PATTERN_ACCS.findall(new_xml)[0]
    type = accounts.split(">")[0] + ">"
    found = [account for account in PATTERN_ACC.findall(accounts) if selector in account]
    assert len(found) == 1, "should be one and only one account login"
    new_xml = PATTERN_ACCS.sub('<accounts> ' + type + found[0] + "</account> </accounts>", new_xml)
    try:
        accounts = PATTERN_REFS.findall(new_xml)[0]
        found = [account for account in PATTERN_REF.findall(accounts) if selector in account]
        new_xml = PATTERN_REFS.sub(found[0], new_xml)
    except IndexError, e:
        # do not care if ref is optional
        pass
    return new_xml


def helper(args):
    """
    run just that account on main.__run(config object)
    :param XMLString: XML with all account
    :param selector:
    :return:  XML string for running just that account
    """
    class runnable:
        def __init__(self):
            self.config = Config()

    [xml, selector] = args
    new_xml = replace(xml, selector)
    run = runnable()
    run.config.parseFromString(new_xml)
    run_v1(run.config)

if __name__ == "__main__": # pragma: no cover
    file = "config.xml"
    if len(sys.argv) > 1 and int(sys.argv[1])> 0:
        if len(sys.argv) == 3:
            file = sys.argv[2]
        run(int(sys.argv[1]), file)
    else:
        run(1, "config.xml")
