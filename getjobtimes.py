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

VERBOSE=False

def printStats(deltas,njobs,nBadTimes):
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
      if VERBOSE:
        print outdir
      logdir = os.path.join(outdir,"log")
      try:
        logdirContents = os.listdir(logdir)
      except OSError:
        print " logdir doesn't exist, maybe run --fetchlog ?, using larStage0.out"
        try:
          jobdirContents = os.listdir(outdir)
        except OSError:
          print " outdir doesn't exist"
          continue
        else:
          nBadTimes = 0
          deltas = []
          for jobdir in jobdirContents:
            jobdirabs = os.path.join(outdir,jobdir)
            isDir = os.path.isdir(jobdirabs)
            match = re.match(r"\d+_(\d+)",jobdir)
            if isDir and match:
              larStage0fn = os.path.join(jobdirabs,"larStage0.out")
              try:
                larStage0file = open(larStage0fn)
              except IOError:
                if VERBOSE:
                  print "couldn't open larStage0fn: ", larStage0fn
              else:
                startTime = None
                endTime = None
                for line in larStage0file:
                  try:
                    t = datetime.strptime(firstLine,r"%a %b %d %X %Z %Y")
                  except ValueError:
                    continue
                  else:
                    if startTime is None:
                      startTime = t
                    else:
                      endTime = t
                if startTime is None or endTime is None:
                  nBadTimes += 1
                else:
                  deltas.append(endTime-startTime)
              finally:
                larStage0file.close()
          printStats(deltas,njobs,nBadTimes)
      else:
        if VERBOSE:
          print "len(logdirContents): ", len(logdirContents)
        nBadTimes = 0
        deltas = []
        for logfn in logdirContents:
          if VERBOSE:
            print "  logfn: ", logfn
          if logfn[-4:] != ".out":
            continue
          if logfn[:6] == "start-":
            continue
          if logfn[:5] == "stop-":
            continue
          if logfn[:7] == "submit.":
            continue
          logfnabs = os.path.join(logdir,logfn)
          if VERBOSE:
            print "  logfnabs: ",logfnabs
          firstLine = None
          lastLine = None
          with open(logfnabs) as logfile:
            for line in logfile:
              if firstLine is None:
                firstLine = line[:28]
              else:
                lastLine = line[:28]
          try:
            # remove timezone
            if firstLine[9] == ' ':
              firstLine = firstLine[:8]+'0'+firstLine[8:]
            if lastLine[9] == ' ':
              lastLine = lastLine[:8]+'0'+lastLine[8:]
            firstLine = firstLine[:18]
            lastLine = lastLine[:18]
            startTime = datetime.strptime(firstLine,r"%a %b %d %X")
            endTime = datetime.strptime(lastLine,r"%a %b %d %X")
            if VERBOSE:
              print firstLine, startTime
              print lastLine, endTime
            delta = endTime-startTime
          except ValueError:
            nBadTimes += 1
          else:
            deltas.append(delta)
        printStats(deltas,njobs,nBadTimes)
