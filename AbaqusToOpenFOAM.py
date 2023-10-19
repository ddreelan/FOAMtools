# File for parsing .csv file as output from Fluent
import pandas as pd
import numpy as np
import re
from scipy.interpolate import griddata
import time
import os
import sys
from decimal import Decimal


abaqusCSVpath = sys.argv[1]
# ofCasePath = "/Users/dd/openfoam/CellularAutomataFoam/run/CFD-Coupling/AbaqusToOpenFOAM_deeper/"
ofTime = "0"
ofCellPosName = "CellPos"
outputFieldName = "T"
ofCasePath = os.getcwd()


def ReadVectorFieldValues(CasePath,TimeStr,FieldName):
    filePath = CasePath + TimeStr + "/" + FieldName
#     Open file and read and split the lines
    with open(filePath) as f:
        lines = f.read().splitlines() 
    i = 0
    for line in lines:
        if lines[i] == "(":
            nValues = int(lines[i-1]);
            iStart = i+1;
            
        if lines[i] == "boundaryField":
            iEnd = i-4;
        i = i+1

    lines = lines[iStart:iEnd+1]

    i =0
    for l in lines:
        lines[i] = lines[i].strip('(')
        lines[i] = lines[i].strip(')')
        lines[i] = lines[i].split()

        j=0
        for c in lines[i]:
            lines[i][j] = float(c)
            j=j+1
        
        i = i+1
        
    lines = np.array(lines)
    
    return lines

def getBoundaryStr(CasePath,TimeStr,FieldName):
    filePath = CasePath + TimeStr + "/" + FieldName
    with open(filePath) as f:
        lines = f.read().splitlines() 
    i = 0
    for line in lines:
        if lines[i] == "boundaryField":
            iBoundary = i
        i = i+1

    boundaryLines = lines[iBoundary:-1]
    boundaryStr = ""

    b = 0
    for B in boundaryLines:
        boundaryLines[b] = re.sub("calculated","zeroGradient",B)
        if "value" in B:
            boundaryLines[b]=""
        boundaryStr = boundaryStr + str(boundaryLines[b]) + str("\n")
        b = b+1
    
    boundaryStr = str(boundaryStr)
    return boundaryStr

def  writeField(ValueType,CasePath,TimeStr,FieldName,FieldValues,boundaryInfoStr):
    buffer=[]
    buffer.append('/*--------------------------------*- C++ -*----------------------------------*\\')
    buffer.append('|=========                 |                                                 |')
    buffer.append('| \\      /  F ield         | foam-extend: Open Source CFD                    |')
    buffer.append('|  \\    /   O peration     | Version:     4.0                                |')
    buffer.append('|   \\  /    A nd           | Web:         http://www.foam-extend.org         |')
    buffer.append('|    \\/     M anipulation  |                                                 |')
    buffer.append('\*---------------------------------------------------------------------------*/')
    buffer.append('//             THIS FILE WAS CREATED BY D. DREELAN IN MATLAB')
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
            buffer.append("(" +str(FieldValues[v,0])+" " +str(FieldValues[v,1])+" " +str(FieldValues[v,2])+")")
            
    buffer.append(")")
    buffer.append(";")    
    buffer.append(boundaryInfoStr)

    pathToFile = CasePath + TimeStr + "/" + FieldName
    os.makedirs(os.path.dirname(pathToFile), exist_ok=True)
    f = open(pathToFile, 'w+')
    f.truncate()
    for line in buffer:
        f.write(line + "\n")
    f.close()


def splitAbaqusDF(abaqusCSVpath,ofTime,ofCellPosName,outputFieldName="T",T0=21,Tl=1660,writeVoF=True):
    ofCasePath = ""
    # print("test")
    print("Reading " ,abaqusCSVpath)#, end=" ...")
    df = pd.read_excel(abaqusCSVpath)
    print("DONE")
    FrameStringArr = df["Frame"].unique()
    
    # create dataframe dict for each
    dfDict = {elem : pd.DataFrame()  for elem in FrameStringArr}
#     Create list of times
    TimeArr = [float(f.partition("=")[-1].strip()) for f in FrameStringArr]
    
#     Populate dict of dataframes
    for key in dfDict.keys():
        dfDict[key] = df[:][df.Frame == key]
    
#     Read openfoam cell centres
    ofXYZ = ReadVectorFieldValues(ofCasePath,ofTime,ofCellPosName)
    bdStr = getBoundaryStr(ofCasePath,ofTime,ofCellPosName)
    X = ofXYZ[:,0]
    Y = ofXYZ[:,1]
    Z = ofXYZ[:,2]
    
    
#   record max and min of melt pool size over all timesteps
    xMeltMinG, yMeltMinG, zMeltMinG = 1e12, 1e12, 1e12
    xMeltMaxG, yMeltMaxG, zMeltMaxG = -1e12, -1e12, -1e12
    meltPoolSizes = []
    layerHeights = []

    for i in range(len(dfDict)):
        timeStr = '%g'%(TimeArr[i])        
        x =  np.array(dfDict[FrameStringArr[i]]["X"])
        y =  np.array(dfDict[FrameStringArr[i]]["Y"])
        z =  np.array(dfDict[FrameStringArr[i]]["Z"])
        T =  np.array(dfDict[FrameStringArr[i]]["          NT11"])
        
#         Get the melt pool dimensions for this timestep
        xMeltMin, yMeltMin, zMeltMin = 1e12, 1e12, 1e12
        xMeltMax, yMeltMax, zMeltMax = -1e12, -1e12, -1e12

        for k in range(len(T)):
            if T[k] > Tl:
                xMeltMin = min(xMeltMin,x[k])
                yMeltMin = min(yMeltMin,y[k])
                zMeltMin = min(zMeltMin,z[k])
                xMeltMax = max(xMeltMax,x[k])
                yMeltMax = max(yMeltMax,y[k])
                zMeltMax = max(zMeltMax,z[k])
#         print("Melt pool size for time ", timeStr)
#         print("x:",xMeltMin,xMeltMax)
#         print("y:",yMeltMin,yMeltMax)
#         print("z:",xMeltMin,zMeltMax,"\n")
        layerHeights.append(zMeltMax)
        xMeltMinG = min(xMeltMin,xMeltMinG)
        yMeltMinG = min(yMeltMin,yMeltMinG)
        zMeltMinG = min(zMeltMin,zMeltMinG)
        xMeltMaxG = max(xMeltMax,xMeltMaxG)
        yMeltMaxG = max(yMeltMax,yMeltMaxG)
        zMeltMaxG = max(zMeltMax,zMeltMaxG)
        meltPoolSizes.append([(xMeltMin,xMeltMax),(yMeltMin,yMeltMax),(zMeltMin,zMeltMax)])
        
        
    print("MELT POOL BOUNDS FOR ALL TIMESTEPS")
    print("x:\t",xMeltMinG,"\t",xMeltMaxG)
    print("y:\t",yMeltMinG,"\t",yMeltMaxG)
    print("z:\t",xMeltMinG,"\t",zMeltMaxG,"\n")
    
    # Check if OpenFOAM Mesh contains the melt pool at all times
    ofXmax, ofXmin = max(X), min(X)
    ofYmax, ofYmin = max(Y), min(Y)
    ofZmax, ofZmin = max(Z), min(Z)
    
    print("OpenFOAM MESH DIMENSIONS")
    print("x:\t",ofXmin,"\t",ofXmax)
    print("y:\t",ofYmin,"\t",ofYmax)
    print("z:\t",ofZmin,"\t",ofZmax,"\n")

    meshNotOK = False
    if (ofXmax > xMeltMaxG): 
        print("ofXmax > xMeltMaxG : ", ofXmax, xMeltMaxG)
        meshNotOK = True
    if (ofYmax > yMeltMaxG):
        print("ofYmax > yMeltMaxG : ", ofYmax, yMeltMaxG)
        meshNotOK = True
    if (ofZmax > zMeltMaxG):
        print("ofZmax > zMeltMaxG : ", ofZmax , zMeltMaxG)
        meshNotOK = True
    if (ofXmin > xMeltMinG):
        print("ofXmin > xMeltMinG : ", ofXmin , xMeltMinG)
        meshNotOK = True
    if (ofYmin > yMeltMinG):
        print("ofYmin > yMeltMinG : ", ofYmin , yMeltMinG)
        meshNotOK = True
    if (ofZmin > zMeltMinG):
        print("ofZmin > zMeltMinG : ", ofZmin , zMeltMinG)
        meshNotOK = True
        
    if meshNotOK:
        print("ERROR: OpenFOAM mesh does not encapsulate the melting region")
#         sys.exit()

    for i in range(len(dfDict)):
    	# print("Time index",i,"of",len(dfDict))
        timeStr = '%g'%(TimeArr[i])        
        x =  np.array(dfDict[FrameStringArr[i]]["X"])
        y =  np.array(dfDict[FrameStringArr[i]]["Y"])
        z =  np.array(dfDict[FrameStringArr[i]]["Z"])
        T =  np.array(dfDict[FrameStringArr[i]]["          NT11"])
        
#         print("Layer Height for step ",i, "\time ", timeStr, " = ",layerHeights[i] )
        
        print("Interpolating T for time ", timeStr, "\tlayerHeight: ", layerHeights[i], end=" ...\t")
        start_time = time.perf_counter()
        Tof = griddata((x,y,z), T, (X,Y,Z), method='linear')
        
        VoF = np.zeros(len(Tof))
#         Stop interpolation between surface and above
        for j in range(len(Tof)):
            if Z[j] > layerHeights[i]:
                Tof[j] = T0
                VoF[j] = 0
            else:
            	VoF[j] = 1
        
        print("Time taken = ",time.perf_counter() - start_time," s")
        writeField("scalar",ofCasePath,timeStr,outputFieldName,Tof,bdStr)
        # print(outputFieldName," field written for time",timeStr)
        if (writeVoF):
        		writeField("scalar",ofCasePath,timeStr,"alpha.material",VoF,bdStr)
			# print("alpha.material"," field written for time",timeStr)

splitAbaqusDF(abaqusCSVpath,ofTime,ofCellPosName,outputFieldName="T",T0=21,Tl=1660,writeVoF=True)