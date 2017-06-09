#  Copyright (c) 2014 John Biddiscombe
#
#  Distributed under the Boost Software License, Version 1.0. (See accompanying
#  file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

#!/usr/bin/python
import optparse
import itertools
from io import StringIO
import csv
import os
import re
import glob
import math
import numpy
from numpy import array
import matplotlib
from plot_utils import *
from functools import reduce
import pprint

workdir = os.getcwd()

#----------------------------------------------------------------------------
if len(args) == 0 :
    print("No input CSV file given")
    exit(0)

#----------------------------------------------------------------------------
# to plot something not already included, add it to this list
G1 = {}
G2 = {}
G3 = {}
G4 = {}

#----------------------------------------------------------------------------
#
# read results data in and generate arrays/maps of values
# for each parcelport, threadcount, blocksize, ...
for csvfile in args :

    print("\nReading file ", csvfile)

    # output file path for svg/png
    base = os.path.splitext(csvfile)[0]
    # empty list of graphs we will be fill for exporting
    graphs_to_save = []

    # open the CSV file
    with open(csvfile) as f:
      io = StringIO(f.read().replace(':', ','))
      reader = csv.reader(io)
      # loop over the CSV file lines,
      # if the CSV output is changed for the test, these offsets will need to be corrected
      for row in reader:
          Network  = row[1].strip()
          print("network" , Network)
          Threads  = int(row[2])
          Nodes    = int(row[3])
          Level    = int(row[5])
          Grids    = int(row[7])
          Time     = float(row[9])
          Computation = float(row[11])
          Regrid      = float(row[13])
          Compare     = float(row[15])
          Find        = float(row[17])
          Coalesce    = int(row[19])

          print("Network=%s Nodes=%4i Threads=%3i Level=%3i Grids=%9i Time=%6.1f "  % (Network, Nodes, Threads, Level, Grids, Time))
          grids_per_sec = Grids/Computation

          print("Network, Level, Coalesce", Network, Level, Coalesce)

          # we use a map structure 3 deep with an array at the leaf,
          # this allows us to store param1, param2, param3, {x,y}
          # combinations of params cen be plotted against each other
          # by rearranging the map levels and {x,y} vars.
          insert_safe(G1, None, Network, Level, [Nodes, grids_per_sec])
          insert_safe(G2, Network, Coalesce, Level, [Nodes, grids_per_sec])
          insert_safe(G3, Network, Level, Coalesce, [Nodes, grids_per_sec])


average_map(G1)
average_map(G2)
average_map(G3)

mpi = G2['mpi']
lf  = G2['libfabric']

print("MPI : ")
pprint.pprint(mpi)

print("libfabric : ")
pprint.pprint(lf)

def speedup(d1, d2, result, tkeys, depth=0):
    for k1,v1 in sorted(d1.items(), key=lambda x: x[0]):
        newkeys = tkeys[:]
        newkeys.append(k1)
        if isinstance(v1, dict):
            speedup(v1, d2, result, newkeys, depth+1)
        else:
            for x in v1:
                print("newkeys are", newkeys[0], newkeys[1], newkeys[2], x)
                other = retrieve_safe(d2, newkeys[0], newkeys[1], newkeys[2], x[0])
                if other is not None:
                    ratio = (x[1]/x[2])/other
                    print('retrieve safe', x[0], other, ratio)
                    insert_safe(result, 'Speedup', newkeys[1], newkeys[2], [x[0], ratio])

speedup_result = {}
speedup(lf, G2, speedup_result, ['mpi'])

pprint.pprint(speedup_result)

##-------------------------------------------------------------------
F1 = plot_configuration(G1,
  ["Coalesce", "Parcelport", "Level"],
  ["Nodes", "Grids/s"],
  lambda x: x,                                    # Plot title
  lambda x: str(x),                               # Legend text
  lambda x: "", #"Coalesce = " + str(int(x)),           # legend title
  lambda y,pos: str(int(y)),                      # Y Axis labels
  lambda x,pos: str(int(x)),                      # X Axis labels
  [[2, 5, 11,0.1], [2,8,15,0.1]],          # minmax (base, min, max, padding)
  [0.0, 0.0]                                      # legend offset
  )
graphs_to_save.append([F1,"fig_level-grids"])

##-------------------------------------------------------------------
F2 = plot_configuration(speedup_result,
  ["Speedup", "Coalesce", "Level"],
  ["Nodes", "Speedup Libfabric/MPI"],
  lambda x: str(x),                               # Plot title
  lambda x: str(x)+" ",                           # Legend text
  lambda x: "",                          # legend title
  lambda y,pos: str(float(y)),                      # Y Axis labels
  lambda x,pos: str(int(x)),                      # X Axis labels
  [[2, 5, 11, 0.1], [0, 0.5, 2.0, 0.1]],             # minmax (base, min, max, padding)
  [-0.5, 0.05]                                      # legend offset
  )
graphs_to_save.append([F2,"fig_speedup"])

##-------------------------------------------------------------------
F3 = plot_configuration(G3,
  ["Parcelport", "Level", "Coalesce"],
  ["Nodes", "Grids/s"],
  lambda x: str(x),                               # Plot title
  lambda x: str(x)+" ",                           # Legend text
  lambda x: "Parcelport = " + str(x),             # legend title
  lambda y,pos: str(int(y)),                      # Y Axis labels
  lambda x,pos: str(int(x)),                      # X Axis labels
  [[2, 5, 11, 0.0], [2, 8, 15, 0.0]],             # minmax (base, min, max, padding)
  [0.0, 0.0]                                      # legend offset
  )
graphs_to_save.append([F3,"fig_coalesce-level"])

##-------------------------------------------------------------------
# save plots to png and svg
for fig in graphs_to_save:
  svg_name = base + "-" + fig[1] + ".svg"
  png_name = base + "-" + fig[1] + ".png"
  print("Writing %s" % svg_name)
  fig[0].savefig(svg_name)
  fig[0].savefig(png_name)

#-------------------------------------------------------------------
