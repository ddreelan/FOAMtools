# This tool is to used to refine an OpenFOAM case, using the refineMesh and mapFields.

## 1. Get list of times in the case directory that is to be mapped, and check that they are in chrono order
`ls $1 | grep -E '^[0-9]' > times.txt`

Where $1 is the case directory, this could be run as a script or function (getTimes.sh)

Chheck the times.txt file and rearrange it so that it is in chronological order (the scientific notation directories need to be moved to the top, after 0). It is very important that these are in order for the mapFields script to work correctly. Also, there should be a blank line at the end of the file. If I cared enough, I could probably automate this, but it is easy to do manually and it is good to make sure that it worked as intended and to delete any weird directory names that contain numbers.

## 2. run `mapCase.sh`, with input args:
1. is the source case, full of time directories
2. is the target case, empty, no time directories
3. is the list of time directories to be mapped, MUST BE IN ORDER OF EARLIEST TO LATEST



So the script creates a new case, refining the source mesh using refineMesh. This, by default, halves the mesh spacing in each direction, increasing the number of cells by 8.

I then create a temporary folder to store just the T and alpha.material fields using rsync. I do this as mapFields will map every field that is present, and I only care about T and alpha.material.

I then loop through each of the times in the times.txt file, creating an empty directory for that time in the target folder (it is important that this is the oldest time currently in the directory, which is why the times.txt file must be in order). I delete any lines in the controlDict that contain "startTime", and then append a new line with startTime = the current time being mapped i.e. "$p".

I can then use mapFields for the current time, and by this method the source and target time will match.

One major drawback of using mapFields is that both of the meshes need to be generated each time (takes about 1.5 minutes for each time directory. Source nCells=2,048,000, target nCells=16,384,000, T and alphaM interpolation takes ~30sec for every timestep).

Future work will be to do this internally within OpenFOAM, so that mesh does not need to be re-created for each time step
