#!/usr/bin/env python

import xml.etree.ElementTree as ET
import sys
import os
import os.path
import re
#import argparse
import glob
from datetime import datetime, timedelta
import math

for arg in sys.argv[1:]:
  tree = ET.parse(arg)
  root = tree.getroot()
  for project in root.iter("project"):
    projname = project.get("name")
    for stage in project.iter("stage"):
      stagename = stage.get("name")
      print "\n{0:70} {1:20}".format(projname, stagename)
      njobs = int(stage.find("numjobs").text)
      outdir = stage.find("outdir").text
      #print outdir
      logdir = os.path.join(outdir,"log")
      try:
        jobdirContents = os.listdir(logdir)
      except OSError:
        print " logdir doesn't exist, maybe run --fetchlog ?"
        continue
      else:
        nBadTimes = 0
        deltas = []
        for logfn in jobdirContents:
          if logfn[-4:] != ".out":
            continue
          if logfn[:6] == "start-":
            continue
          if logfn[:5] == "stop-":
            continue
          if logfn[:7] == "submit.":
            continue
          logfnabs = os.path.join(logdir,logfn)
          firstLine = None
          lastLine = None
          with open(logfnabs) as logfile:
            for line in logfile:
              if firstLine is None:
                firstLine = line[:28]
              else:
                lastLine = line[:28]
          try:
            startTime = datetime.strptime(firstLine,r"%a %b %d %X %Z %Y")
            endTime = datetime.strptime(lastLine,r"%a %b %d %X %Z %Y")
            #print firstLine, startTime
            #print lastLine, endTime
            delta = endTime-startTime
          except ValueError:
            nBadTimes += 1
          else:
            deltas.append(delta)
        nDeltas = len(deltas)
        if nDeltas > 0:
          deltas.sort()
          averageTime = timedelta()
          for delta in deltas:
            averageTime += delta
          try:
            averageTime /= nDeltas
          except ZeroDivisionError:
            pass
          averageTime = timedelta(averageTime.days,averageTime.seconds)
          frstQ = deltas[int(math.floor(nDeltas*0.25))]
          scndQ = deltas[min(int(math.ceil(nDeltas*0.5)),nDeltas-1)]
          thrdQ = deltas[min(int(math.ceil(nDeltas*0.75)),nDeltas-1)]
          perc95 = deltas[min(int(math.ceil(nDeltas*0.95)),nDeltas-1)]
          print "nJobs Found: {}/{}".format(nDeltas,njobs)
          if nBadTimes > 0:
            print "Couldn't find or parse times in {} files".format(nBadTimes)
          print "{:12} {:12} {:12} {:12} {:12} {:12}".format("Min", "25%", "50%", "75%", "95%", "Max")
          print "{:12} {:12} {:12} {:12} {:12} {:12}".format(deltas[0], frstQ, scndQ, thrdQ, perc95, deltas[-1])
          print "{:12} {:12} {:12}".format("Average: ","",averageTime)
          goal1 = timedelta(hours=2,minutes=30)
          goal2 = timedelta(hours=2,minutes=50)
          print "For {:}, could be longer by:  {:12.2f} {:12.2f} {:12.2f}".format(goal1,goal1.total_seconds()/thrdQ.total_seconds(),goal1.total_seconds()/perc95.total_seconds(),goal1.total_seconds()/deltas[-1].total_seconds())
          print "For {:}, could be longer by:  {:12.2f} {:12.2f} {:12.2f}".format(goal2,goal2.total_seconds()/thrdQ.total_seconds(),goal2.total_seconds()/perc95.total_seconds(),goal2.total_seconds()/deltas[-1].total_seconds())
          print ""
        else:
          print "No times found"
