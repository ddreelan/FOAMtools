from OpenFOAM_IO import readOpenFOAMfield, writeOpenFOAMfield

from orix import data, io, plot, sampling
from orix.crystal_map import CrystalMap, Phase, PhaseList
from orix.quaternion import Orientation, symmetry
from orix.quaternion.rotation import Rotation
from orix.vector import Vector3d
from orix.projections import StereographicProjection

import matplotlib.pyplot as plt
import time
import numpy as np
# import re

# print("Defining functions for IPF generation...")
# Functions for IPF generation
def q2rot(CasePath,Time):
    qw , _ = readOpenFOAMfield("scalar",CasePath+Time+"qw")
    qv, boundaryStr = readOpenFOAMfield("vector",CasePath+Time+"qv")
#     qv = ReadVectorFieldValues(CasePath,Time,"qv")
    
    nValues = len(qw)
  
    rot_ms = []
    
    for i in range(0,nValues):
        q0 = float(qw[i])
        q1 = float(qv[i][0])
        q2 = float(qv[i][1])
        q3 = float(qv[i][2])

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

def IPFq(CasePath,Time,symmetryIn=symmetry.Oh):
    ipfkeyX = plot.IPFColorKeyTSL(symmetryIn,direction=Vector3d.xvector())
    ipfkeyY = plot.IPFColorKeyTSL(symmetryIn,direction=Vector3d.yvector())
    ipfkeyZ = plot.IPFColorKeyTSL(symmetryIn,direction=Vector3d.zvector())
    
    rot_ms, boundaryStr = q2rot(CasePath,Time)
    
    ori = Orientation.from_matrix(rot_ms, symmetry=symmetryIn)
    rgbX = ipfkeyX.orientation2color(ori)
    rgbY = ipfkeyY.orientation2color(ori)
    rgbZ = ipfkeyZ.orientation2color(ori)
        
    writeOpenFOAMfield("vector",CasePath,Time,"IPFx",rgbX,boundaryStr)
    writeOpenFOAMfield("vector",CasePath,Time,"IPFy",rgbY,boundaryStr)
    writeOpenFOAMfield("vector",CasePath,Time,"IPFz",rgbZ,boundaryStr)
    
def saveIPFkey(CasePath,symmetryIn=symmetry.Oh):
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
    plt.close()

    fig.savefig(
        CasePath+"IPFkey.png",
        bbox_inches="tight",
        pad_inches=0,
        dpi=150
    )
    
def IPF(CasePath,Times,symmetryIn=symmetry.Oh,saveIPFkeyBool=True):
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