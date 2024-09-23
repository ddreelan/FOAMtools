# Orix analysis
# This script is for carrying out crystallographic analysis using Orix

from OpenFOAM_IO import readOpenFOAMfield, writeOpenFOAMfield
from OpenFOAM_Orix import q2rot

from orix import plot, sampling
from orix.quaternion import Orientation, symmetry
from orix.vector import Vector3d

import os
import matplotlib.pyplot as plt


CasePath = os.getcwd() + "/"
Time = "0.1/"

# First need to read in a qw and 
rot_ms, boundaryStr = q2rot(CasePath,Time)
ori = Orientation.from_matrix(rot_ms, symmetry=symmetry.Oh)

print(type(ori))

ipfkey = plot.IPFColorKeyTSL(symmetry.Oh,direction=Vector3d.xvector())
rgb_z = ipfkey.orientation2color(ori)


# fig = plt.figure()
fig = ori.scatter("ipf", c=rgb_z, direction=ipfkey.direction)
# fig.savefig(
#     CasePath+"PoleFigure.png",
#     bbox_inches="tight",
#     pad_inches=0,
#     dpi=150
# )
ori.show()

# fig = plt.figure()
# ax1 = fig.add_subplot(111, projection="stereographic")
# # ax1.scatter(ori.scatter("ipf", c=rgb_z, direction=ipfkey.direction)
# ax1.scatter(ori)

# fig.savefig(
#     CasePath+"PoleFigure.png",
#     bbox_inches="tight",
#     pad_inches=0,
#     dpi=150
# )

print("Finished")