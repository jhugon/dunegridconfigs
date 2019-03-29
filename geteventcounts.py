#!/usr/bin/env python

import xml.etree.ElementTree as ET
import sys
import os
import os.path
import re
import argparse
import glob

from samweb_client import SAMWebClient

class JobDirNotFoundError(Exception):
  pass

def setOfGoodJobDirs(outdir):
  result = []
  try:
    jobdirContents = os.listdir(outdir)
  except OSError:
    raise JobDirNotFoundError(outdir)
  else:
    badList = []
    badListFn = os.path.join(outdir,"bad.list")
    try:
      with open(badListFn) as badListFile:
        for line in badListFile:
          badList.append(line.strip(" \n\r\t"))
    except IOError:
      pass
    #print "badList: ", badList
    for jobdir in jobdirContents:
      jobdirabs = os.path.join(outdir,jobdir)
      isDir = os.path.isdir(jobdirabs)
      if jobdir in badList:
        #print jobdir, "is in bad.list, skipping"
        continue
      match = re.match(r"\d+_(\d+)",jobdir)
      if isDir and match:
        result.append(jobdirabs)
  return result

def countDataFileUsage(jobdirs,sam,inputdef):
  jobsPerDataFn = {}
  samEventsPerJob = []
  didsam = True
  if sam and inputdef:
    for finfo in sam.listFiles(defname=inputdef,fileinfo=True):
        # (file_name, file_id, file_size, event_count) tuples
        # I'm making n jobs, sam n events, my n events
        jobsPerDataFn[finfo[0]] = [0,finfo[3]]
    didsam = True
  for iJobdir, jobdir in enumerate(jobdirs):
    samEventsPerJob.append(0)
    jobirrel = os.path.basename(jobdir)
    consumedfn = os.path.join(jobdir,"consumed_files.list")
    try:
      with open(consumedfn) as consumedfile:
        for line in consumedfile:
          datafn = line.strip("\n\r\t")
          try:
            if didsam:
              jobsPerDataFn[datafn][0] += 1
              samEventsPerJob[iJobdir] += jobsPerDataFn[datafn][1]
            else:
              jobsPerDataFn[datafn] += 1
          except KeyError:
            if didsam:
              print "Error: found file not in dataset definition: ", datafn, inputdef
            else:
              jobsPerDataFn[datafn] = 1
    except IOError:
      if didsam:
        samEventsPerJob[iJobdir] = -1
  for key in jobsPerDataFn:
    if jobsPerDataFn[key][0] > 1:
      print "Error: ran over file ", key, " more than once"
  return samEventsPerJob

if __name__ == "__main__":

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
        inputdef = None
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
            jobdirs = setOfGoodJobDirs(outdir)
          except OSError:
            print projname, stagename, " outdir doesn't exist"
          else:
            samEventsPerJob = countDataFileUsage(jobdirs,sam,inputdef)
            nRun = 0
            nPass = 0
            for iJobdir, jobdirabs in enumerate(jobdirs):
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
                            #print os.path.basename(jobdirabs), samEventsPerJob[iJobdir], int(match.group(1))
                            if int(match.group(1)) != samEventsPerJob[iJobdir]:
                                "Warning: Job ran over different N events than SAM files say: ", int(match.group(1)), samEventsPerJob[iJobdir]
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
          
