#!/bin/bash

samweb list-definition-files $@ > filenames.txt
rm -f fullpathnames.txt
while read inline; do 
  #echo $inline; 
  pathname=$(samweb locate-file $inline); 
  pathname=$(echo $pathname | sed "s/^.*:\(.*\)(.*)$/\1/"); 
  fullpath=$pathname/$inline
  echo $fullpath
  echo $fullpath >> fullpathnames.txt
done < filenames.txt
