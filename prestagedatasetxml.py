#!/usr/bin/env python

import xml.etree.ElementTree as ET
import subprocess
import argparse

parser = argparse.ArgumentParser(description='Prestage the datasets found in the xml file')
parser.add_argument('xmlfile',
                    help='project xml file')
parser.add_argument('-p',"--parallel", type=int, default=1,
                    help='number of processes to use')

args = parser.parse_args()

tree = ET.parse(args.xmlfile)
root = tree.getroot()
for i in root.iter("inputdef"):
  subprocess.call(["samweb","prestage-dataset","--parallel={:d}".format(args.parallel),"--defname={}".format(i.text)])
