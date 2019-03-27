#!/usr/bin/env python

import xml.etree.ElementTree as ET
import sys
import os
import os.path
import re
import argparse
import glob

from samweb_client import SAMWebClient
sam = SAMWebClient()
#sam.verbose = True

parser = argparse.ArgumentParser(description='Displays the number of events in a dataset found in an xml file')
parser.add_argument('xmlfiles', nargs="+",
                    help='project xml files')
parser.add_argument('-r',"--runover",action="store_true",default=False,
                    help="Shows run over events")
parser.add_argument('-p',"--percent",action="store_true",default=False,
                    help="Shows run over events and their percentage of the dataset events")

args = parser.parse_args()

print "{0:70} {1:20} {2:70}".format("","","Dataset")
print "{0:70} {1:20} {2:70}".format("Project","Stage","nEvents")
process_counts_set = set()
file_counts_set = set()
for xmlfilename in args.xmlfiles:
  tree = ET.parse(xmlfilename)
  root = tree.getroot()
  for project in root.iter("project"):
    projname = project.get("name")
    for stage in project.iter("stage"):
      stagename = stage.get("name")
      nEventsDef = -1
      nRun = -1
      nPass = -1
      for inputdefEl in stage.iter("inputdef"):
        inputdef = inputdefEl.text
        try:
          summaryjson = sam.listFilesSummary(defname=inputdef)
        except Exception as e:
          print e
        else:
          nEventsDef = summaryjson["total_event_count"]
      if args.runover or args.percent:
        outdir = stage.find("outdir").text
        try:
          jobdirContents = os.listdir(outdir)
        except OSError:
          print projname, stagename, " outdir doesn't exist"
        else:
          nRun = 0
          nPass = 0
          for jobdir in jobdirContents:
            jobdirabs = os.path.join(outdir,jobdir)
            isDir = os.path.isdir(jobdirabs)
            match = re.match(r"\d+_(\d+)",jobdir)
            if isDir and match:
              outLogFn = os.path.join(jobdirabs,"larStage0.out")
              statusfn = os.path.join(jobdirabs,"lar.stat")
              try:
                statusfile = open(statusfn)
                exitcode = int(statusfile.read())
              except IOError:
                pass
              else:
                if exitcode == 0:
                  try:
                    with open(outLogFn) as outLogFile:
                      for line in outLogFile:
                        if line[:10] == "TrigReport":
                          match = re.match(r"^TrigReport Events total = (\d+) passed = (\d+) failed = \d+\s*$",line)
                          if match:
                            nRun += int(match.group(1))
                            nPass += int(match.group(2))
                  except IOError:
                    pass
              finally:
                statusfile.close()
      if args.runover or args.percent:
        print "{0:70} {1:20} {3:8} {4:8} {5:8}".format(projname, stagename, inputdef,nEventsDef,nRun,nPass)
        if args.percent:
          print "{0:70} {1:20} {3:8} {4:8.1%} {5:8.1%}".format("","","","",nRun/ float(nEventsDef),nPass/float(nEventsDef))
          print "{0:70} {1:20} {3:8} {4:8} {5:8.1%}".format("","","","","",nPass/ float(nRun))
      else:
        print "{0:70} {1:20} {3:8}".format(projname, stagename, inputdef,nEventsDef)
        
