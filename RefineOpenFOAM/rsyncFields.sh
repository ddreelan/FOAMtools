#!/bin/bash
# $1 is the source case, temporary source case is automatically created
# $2 is the target directory name.
# $3... the rest of the args are the fields to be copied

echo "Step 2: rsync temporary source case, containing only T and alphaM fields"
# source_tmp="${1}_tmp"
source_tmp=${2}

echo "Temporary source case: $source_tmp"
mkdir ${source_tmp}

# Copying system 
cp -r "${1}/system" "${source_tmp}/"

# Copying constant, for mesh
cp -r "${1}/constant" "${source_tmp}/"

echo "system and constant copied"

echo "Starting rsyncing of fields"
# rsync -azvhm --exclude="0_org/" --include="*/" --include="T" --include="alpha.material" --exclude="*"  "${1}/" $source_tmp
for v in "${@:3}"
do
	echo "rsyncing ${v}"
	rsync -azvhm --exclude="0_org/" --include="*/" --include="${v}" --exclude="*"  "${1}/" $source_tmp	
done


echo "Listing files in ${source_tmp}:"
ls ${source_tmp}
echo "Finished step 2"