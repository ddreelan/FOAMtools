#!/bin/bash
# $1 is the source case, full of time directories
# $2 is the target case, empty, no time directories
# $3 is the list of time directories to be mapped, MUST BE IN ORDER OF EARLIEST TO LATEST


echo "Mapping fields from $1 to $2"

echo "Step 1: create new case and refine the mesh"
mkdir -p $2/constant $2/system

echo "Copying constant"
cp -r $1/constant/* $2/constant/

echo "Copy system"
cp -r $1/system/* $2/system/

echo "Refining target mesh"
cd $2
refineMesh -overwrite
cd ..
echo "Finished step 1"


echo "Step 2: rsync temporary source case, containing only T and alphaM fields"
source_tmp="${1}_tmp"

echo "Temporary source case: $source_tmp"
mkdir $source_tmp

rsync -azvhm --exclude="0_org/" --include="*/" --include="T" --include="alpha.material" --exclude="*"  "${1}/" $source_tmp

# Copying system 
cp -r "${1}/system" "${source_tmp}/"

# Copying constant, for mesh
cp -r "${1}/constant" "${source_tmp}/"

echo "Listing files in $source_tmp:"
ls $source_tmp
echo "Finished step 2"

echo "Step 3: mapFields for each directory from $source_tmp to $2"
# Move into target case
cd $2
touch "${2}.foam"

# echo "Current directory:"
# pwd
while read p; do
  echo "mapping Fields for time $p"

  # Create directory for time p
  mkdir $p

  # Remove all lines starting with startTime from target controlDict
  sed -i '/startTime/d' system/controlDict

  # Add new startTime to target controlDict
  echo 'startTime ' $p ';'  >> system/controlDict

  # Map fields for p
  mapFields -consistent -sourceTime $p ../$source_tmp

  done <../$3

cd ..

echo "Removing $source_tmp folder"
rm -r $source_tmp

echo "Mapping of fields complete"