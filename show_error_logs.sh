#!/bin/bash

for statfile in $(grep -v 0 $1/*/lar.stat); do
  jobdir=${statfile%/lar.stat:*}
  logfile=${jobdir}/larStage0.out
  echo "============================================================"
  echo $jobdir
  tail -n 25 $logfile
  cat $jobdir/lar.stat
done
