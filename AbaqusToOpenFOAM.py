# File for parsing .csv file as output from Fluent
import pandas as pd
import numpy as np
import re
from scipy.interpolate import griddata
import time
import os
import sys
from decimal import Decimal


# def readOpenFOAMfield(ValueType,filePath):
# def writeOpenFOAMfield(ValueType,CasePath,TimeStr,FieldName,FieldValues,boundaryStr):
from OpenFOAM_IO import readOpenFOAMfield, writeOpenFOAMfield


abaqusCSVpath = sys.argv[1]
# ofCasePath = "/Users/dd/openfoam/CellularAutomataFoam/run/CFD-Coupling/AbaqusToOpenFOAM_deeper/"
ofTime = "0"
ofCellPosName = "CellPos"
outputFieldName = "T"
ofCasePath = os.getcwd()

def readAbaqusDF(abaqusCSVpath):
    print("Reading",abaqusCSVpath,"as a DataFrame")
    tick = time.time()
    df = pd.read_csv(abaqusCSVpath)
    timeTaken = time.time() - tick
    print("\tDone in " + str(round(timeTaken,3)), "seconds")

    FrameStringArr = df["Frame"].unique()
    TimeArr = [float(f.partition("=")[-1].strip()) for f in FrameStringArr]
    print("Number of time frames:", len(TimeArr))
    print("Times:",TimeArr)

    dfDict = {elem : pd.DataFrame()  for elem in TimeArr}
    
#     Populate dict of dataframes
    for key in dfDict.keys():
        dfDict[key] = df[:][df.Frame == key]

    return dfDict

dfDict = readAbaqusDF(abaqusCSVpath)

# print(dfDict)

def getDomainSize(dfDict):
    print("\nGetting range of X, Y, Z for dfDict")
    minX, maxX = 1e12, -1e12

    print(dfDict.keys())
    for key in dfDict.keys():
        # print(dfDict[key])
        # print(dfDict[:]["X"])
        x =  np.array(dfDict[key]["X"])
        print(x)
        # minX = min(min(x),minX)
        # y =  np.array(df["Y"])
        # z =  np.array(df["Z"])
    # print("minX:",minX)
# getDomainSize(dfDict)


def getDomainSize(abaqusCSVpath, Tl=1500, cellSizeTol=1e-5):
    # print("test")
    print("Reading " ,abaqusCSVpath)#, end=" ...")
    # df = pd.read_excel(abaqusCSVpath)
    df = pd.read_csv(abaqusCSVpath)
    print("DONE")
    FrameStringArr = df["Frame"].unique()
    
    # create dataframe dict for each
    dfDict = {elem : pd.DataFrame()  for elem in FrameStringArr}
#     Create list of times
    TimeArr = [float(f.partition("=")[-1].strip()) for f in FrameStringArr]
    
#     Populate dict of dataframes
    for key in dfDict.keys():
        dfDict[key] = df[:][df.Frame == key]

    
    xMinG, yMinG, zMinG = 1e12, 1e12, 1e12
    xMaxG, yMaxG, zMaxG = -1e12, -1e12, -1e12
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

        xu =  sorted(dfDict[FrameStringArr[i]]["X"].unique())
        yu =  sorted(dfDict[FrameStringArr[i]]["Y"].unique())
        zu =  sorted(dfDict[FrameStringArr[i]]["Z"].unique())
        
#         Get the melt pool dimensions for this timestep
        xMeltMin, yMeltMin, zMeltMin = 1e12, 1e12, 1e12
        xMeltMax, yMeltMax, zMeltMax = -1e12, -1e12, -1e12

        #         Get the melt pool dimensions for this timestep
        xMin, yMin, zMin = 1e12, 1e12, 1e12
        xMax, yMax, zMax = -1e12, -1e12, -1e12

        for k in range(len(T)):
            xMin = min(xMin,x[k])
            yMin = min(yMin,y[k])
            zMin = min(zMin,z[k])
            xMax = max(xMax,x[k])
            yMax = max(yMax,y[k])
            zMax = max(zMax,z[k])

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


        xMinG = min(xMin,xMinG)
        yMinG = min(yMin,yMinG)
        zMinG = min(zMin,zMinG)
        xMaxG = max(xMax,xMaxG)
        yMaxG = max(yMax,yMaxG)
        zMaxG = max(zMax,zMaxG)
        meltPoolSizes.append([(xMeltMin,xMeltMax),(yMeltMin,yMeltMax),(zMeltMin,zMeltMax)])
 
    print("DOMAIN BOUNDS FOR ALL TIMESTEPS")
    print("x:\t",xMinG,"\t",xMaxG)
    print("y:\t",yMinG,"\t",yMaxG)
    print("z:\t",xMinG,"\t",zMaxG,"\n")          
        
    print("MELT POOL BOUNDS FOR ALL TIMESTEPS")
    print("x:\t",xMeltMinG,"\t",xMeltMaxG)
    print("y:\t",yMeltMinG,"\t",yMeltMaxG)
    print("z:\t",xMeltMinG,"\t",zMeltMaxG,"\n")

    # Getting cell sizes
    xCellSize = []
    yCellSize = []
    zCellSize = []

    for i in range(len(xu)-1):
        xCellSize.append(xu[i+1]-xu[i])

    xCellSize = sorted(xCellSize)
    print("xCellSize:", xCellSize)
    xCellMin = max(xCellSize)
    for xCell in xCellSize:
        if xCell > cellSizeTol:
            xCellMin = min(xCellMin,xCell)
            pass
    print("xCellSize min:",xCellMin,"max:",max(xCellSize))

    

getDomainSize(abaqusCSVpath)

def splitAbaqusDF(abaqusCSVpath,ofTime,ofCellPosName,outputFieldName="T",T0=21,Tl=1660,writeVoF=True):
    ofCasePath = ""
    # print("test")
    print("Reading " ,abaqusCSVpath)#, end=" ...")
    # df = pd.read_excel(abaqusCSVpath)
    df = pd.read_csv(abaqusCSVpath)
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

    xMinG, yMinG, zMinG = 1e12, 1e12, 1e12
    xMaxG, yMaxG, zMaxG = -1e12, -1e12, -1e12
    meltPoolSizes = []
    layerHeights = []

    for i in range(len(dfDict)):
        timeStr = '%g'%(TimeArr[i])        
        x =  np.array(dfDict[FrameStringArr[i]]["X"])
        y =  np.array(dfDict[FrameStringArr[i]]["Y"])
        z =  np.array(dfDict[FrameStringArr[i]]["Z"])
        T =  np.array(dfDict[FrameStringArr[i]]["          NT11"])
        
#         Get the melt pool dimensions for this timestep
        xMin, yMin, zMin = 1e12, 1e12, 1e12
        xMax, yMax, zMax = -1e12, -1e12, -1e12

        for k in range(len(T)):
            xMin = min(xMin,x[k])
            yMin = min(yMin,y[k])
            zMin = min(zMin,z[k])
            xMax = max(xMax,x[k])
            yMax = max(yMax,y[k])
            zMax = max(zMax,z[k])

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

        xMinG = min(xMin,xMinG)
        yMinG = min(yMin,yMinG)
        zMinG = min(zMin,zMinG)
        xMaxG = max(xMax,xMaxG)
        yMaxG = max(yMax,yMaxG)
        zMaxG = max(zMax,zMaxG)
        meltPoolSizes.append([(xMeltMin,xMeltMax),(yMeltMin,yMeltMax),(zMeltMin,zMeltMax)])


    print("DOMAIN BOUNDS FOR ALL TIMESTEPS")
    print("x:\t",xMinG,"\t",xMaxG)
    print("y:\t",yMinG,"\t",yMaxG)
    print("z:\t",xMinG,"\t",zMaxG,"\n")        
        
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

# def getAbaqusCSVdomainSize()

# splitAbaqusDF(abaqusCSVpath,ofTime,ofCellPosName,outputFieldName="T",T0=21,Tl=1660,writeVoF=True)