import time
import string
import os
import matplotlib.pyplot as plt
import numpy as np
import re
import math

# Functions for parsing OpenFOAM field files
def readOpenFOAMfield(ValueType,filePath):
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

# print("Defining functions for writing of fields back to the OpenFOAM case...")
# Functinos for writing
def writeOpenFOAMfield(ValueType,CasePath,TimeStr,FieldName,FieldValues,boundaryStr):
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