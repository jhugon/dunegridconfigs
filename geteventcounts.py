#!/usr/bin/env python

import xml.etree.ElementTree as ET
import sys
import os
import os.path
import re
#import argparse

from samweb_client import SAMWebClient
sam = SAMWebClient()
#sam.verbose = True

#parser = argparse.ArgumentParser(description='Prestage the datasets found in the xml file')
#parser.add_argument('xmlfile',
#                    help='project xml file')
#
#args = parser.parse_args()

print "{0:70} {1:20} {2:70}".format("","","Dataset")
print "{0:70} {1:20} {2:70}".format("Project","Stage","nEvents")
process_counts_set = set()
file_counts_set = set()
for arg in sys.argv[1:]:
  tree = ET.parse(arg)
  root = tree.getroot()
  for project in root.iter("project"):
    projname = project.get("name")
    for stage in project.iter("stage"):
      stagename = stage.get("name")
      for inputdefEl in stage.iter("inputdef"):
        inputdef = inputdefEl.text
        nEvents = -1
        try:
          summaryjson = sam.listFilesSummary(defname=inputdef)
        except Exception as e:
          print e
        else:
          nEvents = summaryjson["total_event_count"]
        print "{0:70} {1:20} {3:8} ".format(projname, stagename, inputdef,nEvents)
        
#print process_counts_set
#print file_counts_set
