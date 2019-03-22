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

print "{0:70} {1:20} {2:6} {3:6} {4:6} {5:6} {6:6} {7:6}".format("Project","Stage","nJobs","nDirs","Code=0","ProcFin","nFiles","nConsumed")
process_counts_set = set()
file_counts_set = set()
for arg in sys.argv[1:]:
  tree = ET.parse(arg)
  root = tree.getroot()
  for project in root.iter("project"):
    projname = project.get("name")
    for stage in project.iter("stage"):
      stagename = stage.get("name")
      njobs = int(stage.find("numjobs").text)
      outdir = stage.find("outdir").text
      #print outdir
      nGoodDir = 0
      nGoodExitCode = 0
      try:
        jobdirContents = os.listdir(outdir)
      except OSError:
        print projname, stagename, " outdir doesn't exist"
        continue
      else:
        for jobdir in jobdirContents:
          jobdirabs = os.path.join(outdir,jobdir)
          isDir = os.path.isdir(jobdirabs)
          match = re.match(r"\d+_(\d+)",jobdir)
          if isDir and match:
            nGoodDir += 1
            jobnum = match.group(1)
            #print jobdir, jobnum
            #print os.listdir(jobdirabs)
            #print jobdirab
            statusfn = os.path.join(jobdirabs,"lar.stat")
            with open(statusfn) as statusfile:
              exitcode = int(statusfile.read())
              if exitcode == 0:
                  nGoodExitCode += 1
      samprojnamesfn = os.path.join(outdir,"sam_projects.list")
      nProcFinished = 0
      nFilesTotal = 0
      nFilesConsumed = 0
      nFilesFailed = 0
      with open(samprojnamesfn) as samprojnamefile:
        for samprojname in samprojnamefile:
          samprojname = samprojname.replace('\n','')
          samprojurl = sam.findProject(samprojname)
          try:
            summaryjson = sam.projectSummary(samprojurl)
          except Exception as e:
           print e
          else:
            #print summaryjson.keys()
            #print summaryjson['process_counts'] # completed, finished, bad, error, unknown
            #print summaryjson['file_counts'] # consumed, transferred, skipped, failed, unknown
            #print summaryjson['files_in_snapshot']
            try:
              nProcFinished += summaryjson['process_counts']['finished']
            except:
              pass
            try:
              nFilesTotal += summaryjson['files_in_snapshot']
            except:
              pass
            try:
              nFilesConsumed += summaryjson['file_counts']['consumed']
            except:
              pass
            try:
              nFilesFailed += summaryjson['file_counts']['failed']
            except:
              pass
            for k in summaryjson['file_counts']:
                file_counts_set.add(k)
            for k in summaryjson['process_counts']:
                process_counts_set.add(k)
  
     
      print "{0:70} {1:20} {2:6} {3:6} {4:6} {5:6} {6:6} {7:6}".format(projname, stagename, njobs, nGoodDir, nGoodExitCode, nProcFinished,nFilesTotal, nFilesConsumed)
        
#print process_counts_set
#print file_counts_set
