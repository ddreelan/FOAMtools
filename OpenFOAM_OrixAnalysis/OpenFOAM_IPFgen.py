# Note, add FOAMtools to your PYTHONPATH variable
# i.e.
# 		echo "export PYTHONPATH=$PYTHONPATH:[path to FOAMtools]" >> ~/.bashrc && . ~/.bashrc

# from OpenFOAM_IO import ReadFromOpenFOAMfield as readField, writeToOpenFOAMfield as writeField
from OpenFOAM_Orix import IPF

import os

# Get the current directory
current_directory = os.getcwd()

# Get all subdirectories in the current directory
subdirectories = [subdir for subdir in os.listdir(current_directory) if os.path.isdir(os.path.join(current_directory, subdir))]

# Filter subdirectories with a number in their name and exclude '0'
subdirectories_numbered = [subdir for subdir in subdirectories if any(char.isdigit() for char in subdir) and subdir != '0']

# Sort subdirectories chronologically
Times = sorted(subdirectories_numbered, key=lambda x: int(''.join(filter(str.isdigit, x))))

# Add the trailing /
for i in range(0,len(Times)):
    Times[i] = Times[i] + "/"

CasePath = current_directory + "/"

IPF(CasePath,Times)