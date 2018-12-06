#!/usr/bin/env python

import ROOT as root
import sys

for iArg, arg in enumerate(sys.argv):
    if iArg == 0:
        continue
    #print "Checking: ", arg
    f = root.TFile(arg)
    if not f:
      print f, " is bad"
    if f.IsZombie():
      print f, " is zombie"
    if f.GetSize() == 0:
      print f, " len zero"
    


