#!/bin/bash
rsyncFieldsTimes () {
  echo "arg1 is the source case, full of time directories"
  echo "arg2 is the target case name"
  echo "arg3 is the file of times to be mapped"
  echo "arg4 is the file of fields to be mapped"

  echo "Copying constant"
  rsync -azvhm --include="constant/" --include="processor*/constant" --exclude="*"  "${1}/" $2/

  echo "Copy system"
  rsync -vazhm $1/system/* $2/system/

  while read t; do
    echo  "Rsyncing time ${t}" 
#    while read f; do
 #   echo "Copying field ${f} for time ${t}"
    rsync -azvhm --include="${t}/" --include="processor*/" --include-from=$4 --exclude="*"  "${1}/" $2/
#    done <$4
  done <$3

  echo "Rsyncing complete"
}
