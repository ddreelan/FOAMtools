print("Welcome to OpenFOAMtoIPF.py, created by Danny Dreelan")
print("If packages are not installed, please run this first:\n")
print("\tpython3.9 -m pip install --upgrade pip matplotlib orix\n\n\n")

print("Loading packages...")
import time
import string
# from os import listdir, system, linesep
import os
# Load packages
print("\tmatplotlib...",end='')
tick = time.time()
import matplotlib.pyplot as plt
timeTaken = time.time() - tick
print("\tDONE in " + str(timeTaken) + "s")

print("\tnumpy...",end='')
tick = time.time()
timeTaken = time.time() - tick
import numpy as np
print("\tDONE in " + str(timeTaken) + "s")

print("\tre...\t",end='')
tick = time.time()
import re
timeTaken = time.time() - tick
print("\tDONE in " + str(timeTaken) + "s")

print("\tmath...\t",end='')
tick = time.time()
import math
timeTaken = time.time() - tick
print("\tDONE in " + str(timeTaken) + "s")

print("\torix...\t",end='')
tick = time.time()
from orix import data, io, plot, sampling
from orix.crystal_map import CrystalMap, Phase, PhaseList
from orix.quaternion import Orientation, symmetry
from orix.quaternion.rotation import Rotation
from orix.vector import Vector3d
from orix.projections import StereographicProjection
timeTaken = time.time() - tick
print("\tDONE in " + str(timeTaken) + "s")

print("\n\t\tALL PACKAGES LOADED!!\n\n")


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

symmetryGroup = symmetry.Oh
saveIPFkeyBool_input = True
ViewAvailablePG = False

if ViewAvailablePG:
    # View available point groups
    pg_laue = [
        symmetry.Ci,
        symmetry.C2h,
        symmetry.D2h,
        symmetry.S6,
        symmetry.D3d,
        symmetry.C4h,
        symmetry.D4h,
        symmetry.C6h,
        symmetry.D6h,
        symmetry.Th,
        symmetry.Oh,
    ]
    for pg in pg_laue:
        ipfkey = plot.IPFColorKeyTSL(pg)
        ipfkey.plot()
    
# We'll want our plots to look a bit larger than the default size
# new_params = {
#     "figure.facecolor": "w",
#     "figure.figsize": (20, 7),
#     "lines.markersize": 0.1,
#     "font.size": 15,
#     "axes.grid": True,
# }
# plt.rcParams.update(new_params)


print("Defining functions for parsing OpenFOAM field files...")
# Functions for parsing OpenFOAM field files
def ReadFromOpenFOAMfield(ValueType,filePath):
#     filePath = CasePath + TimeStr + "/" + FieldName
#     Open file and read and split the lines
    with open(filePath) as f:
        lines = f.read().splitlines() 
    
    i = 0
    for line in lines:
        if lines[i] == "(":
            iStart = i+1
            
        if lines[i] == "boundaryField":
            iBoundary = i
            iEnd = i-3
        i = i+1

    nValues = iEnd-iStart

    boundaryLines = lines[iBoundary:-1]
    lines = lines[iStart:iEnd]
    boundaryStr = ""
    b = 0
    for B in boundaryLines:
        boundaryLines[b] = re.sub("calculated","zeroGradient",B)
        boundaryLines[b] = re.sub("fixedValue","zeroGradient",B)
        boundaryLines[b] = re.sub("slip","zeroGradient",B)
        if "value" in B:
            boundaryLines[b]=""
        boundaryStr = boundaryStr + str(boundaryLines[b]) + str("\n")
        b = b+1
    
    if ValueType == "scalar":
        fieldValues = np.zeros(nValues)    
        for i in range(0,nValues):
            fieldValues[i] = float(lines[i])
            
    elif ValueType == "vector":
        for i in range(0,nValues):
            lines[i] = lines[i].strip('(')
            lines[i] = lines[i].strip(')')
            lines[i] = lines[i].split()

            j=0
            for c in lines[i]:
                lines[i][j] = float(c)
                j=j+1

        fieldValues = np.array(lines,dtype=object)

    
    return fieldValues, boundaryStr 

print("Defining functions for writing of fields back to the OpenFOAM case...")
# Functinos for writing
def writeToOpenFOAMfield(ValueType,CasePath,TimeStr,FieldName,FieldValues,boundaryStr):
    buffer=[]
    buffer.append('/*--------------------------------*- C++ -*----------------------------------*\\')
    buffer.append('|=========                 |                                                 |')
    buffer.append('| \\      /  F ield         | foam-extend: Open Source CFD                    |')
    buffer.append('|  \\    /   O peration     | Version:     4.0                                |')
    buffer.append('|   \\  /    A nd           | Web:         http://www.foam-extend.org         |')
    buffer.append('|    \\/     M anipulation  |                                                 |')
    buffer.append('\*---------------------------------------------------------------------------*/')
    buffer.append('//             THIS FILE WAS CREATED BY D. DREELAN IN PYTHON')
    buffer.append('FoamFile')
    buffer.append('{')
    buffer.append('    version     2.0;')
    buffer.append('    format      ascii;')
#     iStart = len(buffer)
#     i = iStart + 1;

    if ValueType == 'vector':
        buffer.append('    class       volVectorField;')
    elif ValueType == 'scalar':
        buffer.append('    class       volScalarField;')
#     else: # Need to quit out and say not recognised

    buffer.append('    location   "' + TimeStr + '";')
    buffer.append('    object    ' + FieldName + ';')
    buffer.append('}')
    if FieldName == "T":
        buffer.append('dimensions      [0 0 0 1 0 0 0];')
    else:
        buffer.append('dimensions      [0 0 0 0 0 0 0];')
    buffer.append('internalField   nonuniform List<'+str(ValueType)+'>')
    buffer.append(str(len(FieldValues)))
    buffer.append('(')

# %      ADD ALL FIELD VALUES
    if ValueType == 'scalar':
        for v in range(0,len(FieldValues)):
            buffer.append(str(FieldValues[v]))

    elif ValueType == 'vector':
        for v in range(0,len(FieldValues)):
            buffer.append("(" +str(FieldValues[v][0])+" " +str(FieldValues[v][1])+" " +str(FieldValues[v][2])+")")
            
    buffer.append(")")
    buffer.append(";")    
    buffer.append(boundaryStr)

    pathToFile = CasePath + TimeStr + "/" + FieldName
    
    f = open(pathToFile, "a")
    f.seek(0)
    f.truncate()
    for line in buffer:
        f.write(line + "\n")
    f.close()
    
print("Defining functions for IPF generation...")
# Functions for IPF generation
def q2rot(CasePath,Time):
    qwFilePath = ReadFromOpenFOAMfield
    qw , _ = ReadFromOpenFOAMfield("scalar",CasePath+Time+"qw")
    qv, boundaryStr = ReadFromOpenFOAMfield("vector",CasePath+Time+"qv")
#     qv = ReadVectorFieldValues(CasePath,Time,"qv")
    
    nValues = len(qw)
  
    rot_ms = []
    
    for i in range(0,nValues):
        q0 = float(qw[i])
        q1 = float(qv[i][0])
        q2 = float(qv[i][1])
        q3 = float(qv[i][2])
#         print("q0:",q0.type())
#         print("q1:",q1.type())
#         print("q2:",q2.type())
#         print("q3:",q3.type())

        r00 = 2 * (q0 * q0 + q1 * q1) - 1
        r01 = 2 * (q1 * q2 - q0 * q3)
        r02 = 2 * (q1 * q3 + q0 * q2)

        r10 = 2 * (q1 * q2 + q0 * q3)
        r11 = 2 * (q0 * q0 + q2 * q2) - 1
        r12 = 2 * (q2 * q3 - q0 * q1)

        r20 = 2 * (q1 * q3 - q0 * q2)
        r21 = 2 * (q2 * q3 + q0 * q1)
        r22 = 2 * (q0 * q0 + q3 * q3) - 1
     
        rot_ms.append(np.array([[r00, r01, r02],
                           [r10, r11, r12],
                           [r20, r21, r22]]))
    return rot_ms, boundaryStr

def IPFq(CasePath,Time,symmetryIn=symmetryGroup):
    ipfkeyX = plot.IPFColorKeyTSL(symmetryIn,direction=Vector3d.xvector())
    ipfkeyY = plot.IPFColorKeyTSL(symmetryIn,direction=Vector3d.yvector())
    ipfkeyZ = plot.IPFColorKeyTSL(symmetryIn,direction=Vector3d.zvector())
    
    rot_ms, boundaryStr = q2rot(CasePath,Time)
    
    ori = Orientation.from_matrix(rot_ms, symmetry=symmetryIn)
    rgbX = ipfkeyX.orientation2color(ori)
    rgbY = ipfkeyY.orientation2color(ori)
    rgbZ = ipfkeyZ.orientation2color(ori)
        
    writeToOpenFOAMfield("vector",CasePath,Time,"IPFx",rgbX,boundaryStr)
    writeToOpenFOAMfield("vector",CasePath,Time,"IPFy",rgbY,boundaryStr)
    writeToOpenFOAMfield("vector",CasePath,Time,"IPFz",rgbY,boundaryStr)
    
def saveIPFkey(CasePath,symmetryIn=symmetryGroup):
    # Get IPF color key as RGB array
    ckey = plot.IPFColorKeyTSL(symmetryIn)
    fig = ckey.plot(return_figure=True)
    rgb_grid = fig.axes[0].images[0].get_array()
    plt.close(fig)

    # Get extent of fundamental sector (IPF)
    sector = symmetryIn.fundamental_sector
    x, y = StereographicProjection().vector2xy(sector.edges)
    x_min, x_max = x.min(), x.max()
    y_min, y_max = y.min(), y.max()

    fig = plt.figure()
    ax1 = fig.add_subplot(111, projection="ipf", symmetry=symmetryIn)
#     ax1.imshow(rgb_grid, extent=(x_min, x_max, y_min, y_max), zorder=0)
    plt.close()

    fig.savefig(
        CasePath+"IPFkey.png",
        bbox_inches="tight",
        pad_inches=0,
        dpi=150
    )
    
def IPF(CasePath,Times,symmetryIn=symmetryGroup,saveIPFkeyBool=saveIPFkeyBool_input):
    nTimes = len(Times)
    print("Generating IPF. Number of times: " + str(nTimes) +"\n")
    if saveIPFkeyBool:
        print("\n\tSaving IPFkey.png to the case directory...\n\n")
        saveIPFkey(CasePath,symmetryIn)

    i = 0
    for t in Times:
        tick = time.time()
        print("\tTime " + t + "...",end='')
        IPFq(CasePath,t,symmetryIn)
        timeTaken = time.time() - tick
        timeRem = timeTaken * (nTimes - i - 1)
        print("\tDONE in " + str(round(timeTaken,3)) + " s\t\tEst. Time Rem.: " + str(round(timeRem,3)) + "s")
        i = i+1


print("\n\t\tALL FUNCTIONS DECLARED, READY TO GO!!\n\n")

IPF(CasePath,Times,)

print("\n\n\t\t\tPROGRAM COMPLETE!!")