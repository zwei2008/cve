#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Database layer
#  translates database calls to functions
#
# Software is free software released under the "Modified BSD license"
#

# Copyright (c) 2014-2016       Pieter-Jan Moreels - pieterjan.moreels@gmail.com

# imports
import zipfile
import os

def listdir(path, list_name):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isdir(file_path):
            listdir(file_path, list_name)
        elif os.path.splitext(file_path)[1]=='.xml':
            list_name.append(file_path)
    return list_name

def getZipfile(path, list_name):
    xml = []
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isdir(file_path):
            getZipfile(file_path, list_name)
        elif os.path.splitext(file_path)[1]=='.zip':
            list_name.append(file_path)
    print (len(list_name))
    for x in [0,len(list_name)-1]:
        print (path+list_name[x])
        azip = zipfile.ZipFile(list_name[x], 'r')
        azip.extractall(path)
        #os.remove(list_name[x])
    return xml

''' 
if __name__ == '__main__':
    zip = []
    xml = []
    getZipfile(direction,zip)
    listdir(direction,xml)
    print (xml);
    
           
def getZipfile():
  lst=list(colCPE.find({"id": {"$regex": regex}}))
  if fullSearch: lst.extend(colCPEOTHER.find({"id": {"$regex": regex}}))
  return lst
'''

