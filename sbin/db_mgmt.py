#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Manager for the database
#
# Copyright (c) 2012 		Wim Remes
# Copyright (c) 2012-2014 	Alexandre Dulaunoy - a@foo.be
# Copyright (c) 2014-2016 	Pieter-Jan Moreels - pieterjan.moreels@gmail.com

# Imports
# make sure these modules are available on your system
import os
import sys
runPath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(runPath, ".."))

import argparse
import datetime
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

from dateutil.parser import parse as parse_datetime

from lib.ProgressBar import progressbar
from lib.Toolkit import toStringFormattedCPE
from lib.Config import Configuration
import lib.DatabaseLayer as db
import lib.Zipfile as zipfile

# Variables
direction = "/root/cnnvd"

# parse command line arguments
argparser = argparse.ArgumentParser(description='populate/update the local CVE database')
argparser.add_argument('-u', action='store_true', help='update the database')
argparser.add_argument('-p', action='store_true', help='populate the database')
argparser.add_argument('-cp', action='store_true', help='populate the chinese database')
argparser.add_argument('-a', action='store_true', default=False, help='force populating the CVE database')
argparser.add_argument('-f', help='process a local xml file')
argparser.add_argument('-v', action='store_true', help='verbose output')
args = argparser.parse_args()


# init parts of the file names to enable looped file download
file_prefix = "nvdcve-2.0-"
file_suffix = ".xml.gz"
file_mod = "modified"
file_rec = "recent"

# get the current year. This enables us to download all CVE's up to this year :-)
date = datetime.datetime.now()
year = date.year + 1

# default config
defaultvalue = {}
defaultvalue['cwe'] = "Unknown"

cveStartYear = Configuration.getCVEStartYear()

# define the CVE parser. Thanks to Meredith Patterson (@maradydd) for help on this one.

class CVEHandler(ContentHandler):
    def __init__(self):
        self.cves = []
        self.inCVSSElem = 0
        self.inSUMMElem = 0
        self.inDTElem = 0
        self.inPUBElem = 0
        self.inAccessvElem = 0
        self.inAccesscElem = 0
        self.inAccessaElem = 0
        self.inCVSSgenElem = 0
        self.inImpactiElem = 0
        self.inImpactcElem = 0
        self.inImpactaElem = 0

    def startElement(self, name, attrs):
        if name == 'entry':
            self.cves.append({'id': attrs.get('id'), 'references': [], 'vulnerable_configuration': [], 'vulnerable_configuration_cpe_2_2':[]})
            self.ref = attrs.get('id')
        elif name == 'cpe-lang:fact-ref':
            self.cves[-1]['vulnerable_configuration'].append(toStringFormattedCPE(attrs.get('name')))
            self.cves[-1]['vulnerable_configuration_cpe_2_2'].append(attrs.get('name'))
        elif name == 'cvss:score':
            self.inCVSSElem = 1
            self.CVSS = ""
        elif name == 'cvss:access-vector':
            self.inAccessvElem = 1
            self.accessv = ""
        elif name == 'cvss:access-complexity':
            self.inAccesscElem = 1
            self.accessc = ""
        elif name == 'cvss:authentication':
            self.inAccessaElem = 1
            self.accessa = ""
        elif name == 'cvss:confidentiality-impact':
            self.inImpactcElem = 1
            self.impactc = ""
        elif name == 'cvss:integrity-impact':
            self.inImpactiElem = 1
            self.impacti = ""
        elif name == 'cvss:availability-impact':
            self.inImpactaElem = 1
            self.impacta = ""
        elif name == 'cvss:generated-on-datetime':
            self.inCVSSgenElem = 1
            self.cvssgen = ""
        elif name == 'vuln:summary':
            self.inSUMMElem = 1
            self.SUMM = ""
        elif name == 'vuln:published-datetime':
            self.inDTElem = 1
            self.DT = ""
        elif name == 'vuln:last-modified-datetime':
            self.inPUBElem = 1
            self.PUB = ""
        elif name == 'vuln:reference':
            self.cves[-1]['references'].append(attrs.get('href'))
        elif name == 'vuln:cwe':
            self.cves[-1]['cwe'] = attrs.get('id')

    def characters(self, ch):
        if self.inCVSSElem:
            self.CVSS += ch
        if self.inSUMMElem:
            self.SUMM += ch
        if self.inDTElem:
            self.DT += ch
        if self.inPUBElem:
            self.PUB += ch
        if self.inAccessvElem:
            self.accessv += ch
        if self.inAccesscElem:
            self.accessc += ch
        if self.inAccessaElem:
            self.accessa += ch
        if self.inCVSSgenElem:
            self.cvssgen += ch
        if self.inImpactiElem:
            self.impacti += ch
        if self.inImpactcElem:
            self.impactc += ch
        if self.inImpactaElem:
            self.impacta += ch

    def endElement(self, name):
        if name == 'cvss:score':
            self.inCVSSElem = 0
            self.cves[-1]['cvss'] = self.CVSS
        if name == 'cvss:access-vector':
            self.inAccessvElem = 0
            if 'access' not in self.cves[-1]:
                self.cves[-1]['access'] = {}
            self.cves[-1]['access']['vector'] = self.accessv
        if name == 'cvss:access-complexity':
            self.inAccesscElem = 0
            if 'access' not in self.cves[-1]:
                self.cves[-1]['access'] = {}
            self.cves[-1]['access']['complexity'] = self.accessc
        if name == 'cvss:authentication':
            self.inAccessaElem = 0
            if 'access' not in self.cves[-1]:
                self.cves[-1]['access'] = {}
            self.cves[-1]['access']['authentication'] = self.accessa
        if name == 'cvss:confidentiality-impact':
            self.inImpactcElem = 0
            if 'impact' not in self.cves[-1]:
                self.cves[-1]['impact'] = {}
            self.cves[-1]['impact']['confidentiality'] = self.impactc
        if name == 'cvss:integrity-impact':
            self.inImpactiElem = 0
            if 'impact' not in self.cves[-1]:
                self.cves[-1]['impact'] = {}
            self.cves[-1]['impact']['integrity'] = self.impacti
        if name == 'cvss:availability-impact':
            self.inImpactaElem = 0
            if 'impact' not in self.cves[-1]:
                self.cves[-1]['impact'] = {}
            self.cves[-1]['impact']['availability'] = self.impacta
        if name == 'cvss:generated-on-datetime':
            self.inCVSSgenElem = 0
            self.cves[-1]['cvss-time'] = parse_datetime(self.cvssgen, ignoretz=True)
        if name == 'vuln:summary':
            self.inSUMMElem = 0
            self.cves[-1]['summary'] = self.SUMM
        if name == 'vuln:published-datetime':
            self.inDTElem = 0
            self.cves[-1]['Published'] = parse_datetime(self.DT, ignoretz=True)
        if name == 'vuln:last-modified-datetime':
            self.inPUBElem = 0
            self.cves[-1]['Modified'] = parse_datetime(self.PUB, ignoretz=True)

class CNNVDHandler(ContentHandler):
    def __init__(self):
        self.cnnvd = []
        self.CVE_IDElem = 0

    def startElement(self, name, attrs):

        if name == 'entry':
            self.cnnvd.append({'title': attrs.get('title')})
            #self.ref = attrs.get('cve-id')
            #print ("entry")
        elif name == 'vuln-id':
            self.CVE_IDElem = 1
            self.CVE_ID = ""

    def characters(self, ch):
        if self.CVE_IDElem:
            self.CVE_ID += ch

    def endElement(self, name):
        if name == 'vuln-id':
            self.CVE_IDElem = 0
            self.cnnvd[-1]['vuln-id'] = self.CVE_ID

            
if __name__ == '__main__':

	
    parser = make_parser()
    ch = CVEHandler()
    parser.setContentHandler(ch)
    # start here if it's an update.
    if args.u:
        # get the 'modified' file
        getfile = file_prefix + file_mod + file_suffix
        try:
            (f, r) = Configuration.getFile(Configuration.getFeedURL('cve') + getfile)
        except:
            sys.exit("Cannot open url %s. Bad URL or not connected to the internet?"%(Configuration.getFeedURL("cve") + getfile))
        i = db.getInfo("cves")
        last_modified = parse_datetime(r.headers['last-modified'], ignoretz=True)
        if i is not None:
            if last_modified == i['last-modified']:
                print("Not modified")
                sys.exit(0)
        db.setColUpdate("cves", last_modified)

        # get your parser on !!
        parser = make_parser()
        ch = CVEHandler()
        parser.setContentHandler(ch)
        parser.parse(f)
        for item in ch.cves:
            # check if the CVE already exists.
            x = db.getCVE(item['id'])
            # if so, update the entry.
            if x:
                if 'cvss' not in item:
                    item['cvss'] = None
                if 'cwe' not in item:
                    item['cwe'] = defaultvalue['cwe']
                db.updateCVE(item)
            else:
                db.insertCVE(item)
        # get the 'recent' file
        getfile = file_prefix + file_rec + file_suffix
        try:
            (f, r) = Configuration.getFile(Configuration.getFeedURL('cve') + getfile)
        except:
            sys.exit("Cannot open url %s. Bad URL or not connected to the internet?"%(Configuration.getFeedURL("cve") + getfile))
        parser = make_parser()
        ch = CVEHandler()
        parser.setContentHandler(ch)
        parser.parse(f)
        for item in progressbar(ch.cves):
            # check if the CVE already exists.
            x = db.getCVE(item['id'])
            # if so, update the entry.
            if x:
                if args.v:
                    print("item found : " + item['id'])
                if 'cvss' not in item:
                    item['cvss'] = None
                else:
                    item['cvss'] = float(item['cvss'])
                if 'cwe' not in item:
                    item['cwe'] = defaultvalue['cwe']
                db.updateCVE(item)
            # if not, create it.
            else:
                db.insertCVE(item)
    elif args.p:
        # populate is pretty straight-forward, just grab all the files from NVD
        # and dump them into a DB.
        c = db.getSize('cves')
        if args.v:
            print(str(c))
        if c > 0 and args.a is False:
            print("database already populated")
        else:
            print("Database population started")
            for x in range(cveStartYear, year):
                parser = make_parser()
                ch = CVEHandler()
                parser.setContentHandler(ch)
                getfile = file_prefix + str(x) + file_suffix
                print (getfile)
                try:
                    (f, r) = Configuration.getFile(Configuration.getFeedURL('cve') + getfile)
                except:
                    sys.exit("Cannot open url %s. Bad URL or not connected to the internet?"%(Configuration.getFeedURL('cve') + getfile))
                parser.parse(f)
                if args.v:
                    for item in ch.cves:
                        print(item['id'])
                        print(item["vulnerable_configuration"])
                        #print (len(item[]))
                        #print(item["impact"])
                for item in ch.cves:
                    if 'cvss' in item:
                        item['cvss'] = float(item['cvss'])
                # check if year is not cve-free
                if len(ch.cves) != 0:
                    print("Importing CVEs for year " + str(x))
                    ret = db.insertCVE(ch.cves)
                else:
                    print ("Year " + str(x) + " has no CVE's.")

    elif args.cp:
        # populate is pretty straight-forward, just grab all the files from NVD
        # and dump them into a DB.
        #判断cnnvd目录是否有压缩文件，没有压缩文件并数据库有数据，提示不更新；有压缩文件，解压缩并删除压缩文件
        c = db.getSize('cnnvd')
        fzip = []
        fxml = []
        zipfile.getZipfile(direction,fzip)
        zipfile.listdir(direction,fxml)
        if args.v:
            print(str(c))
        if c > 0 and args.a is False:
            print("Chinese database already populated")
        else:
            print("Chinese Database population started")
            for x in fxml:
                parser = make_parser()
                ch = CNNVDHandler()
                parser.setContentHandler(ch)
                parser.parse(x)
                if args.v:
                    for item in ch.cnnvd:
                        print(item['cve_id'])
                        #print (len(item[]))
                        #print(item["impact"])

                # check if year is not cve-free
                if len(ch.cnnvd) != 0:
                    print("Importing CNNVDs for year " + str(x))
                    ret = db.insertCNNVD(ch.cnnvd)
                else:
                    print ("Year " + str(x) + " has no CVE's.")         
                getfile = x
                print (getfile)
                   
