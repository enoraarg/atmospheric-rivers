#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author : elegall

This module contains variables to specify some parameters for plots.
"""

# ----------------------------------------------
#         Figure aesthetics
# ----------------------------------------------
# --- Text and resolution
from pylab import rcParams
#import matplotlib.pyplot as plt
#rcParams['axes.labelsize']   = 'large'
#rcParams['axes.labelweight'] = 'bold'
#rcParams['axes.titleweight'] = 'bold'
#rcParams['axes.titlesize']   = 'large'
#rcParams['figure.titleweight'] = 'bold'
rcParams['figure.titlesize'] = 'x-large'
#rcParams['figure.labelweight'] = 'bold'
rcParams['figure.dpi'] = 150 # x1.5
rcParams['font.size'] = 16
#plt.rcParams.update({'font.size':16})
#plt.rcParams['text.usetex'] = True

#plt.xckd() pour avoir un tracé un peu "à la main"

# ----------------------------------------------
#         Norms
# ----------------------------------------------
from   matplotlib.colors   import TwoSlopeNorm, Normalize, LinearSegmentedColormap
import seaborn as sns
max_ID    = 10 # number of colors in the palette
norm_ID   = Normalize(0,max_ID)
norm_tcwv = TwoSlopeNorm(vmin=0,vcenter=20,vmax=70) # center=48 to highlight the tropics
norm_ivt  = TwoSlopeNorm(vmin=0,vcenter=250,vmax=600)
cmap_ID   = LinearSegmentedColormap.from_list('Custom cmap', 
                                              sns.color_palette('bright'), 
                                              len(sns.color_palette('bright')))
norm_altflux  = TwoSlopeNorm(vmin=0,vcenter=850,vmax=1000)

# ----------------------------------------------
#          Formatting text
# ----------------------------------------------

def fmt(x):
    '''
    Format text to integer when first decimal is a 0
    '''
    s = f"{x:.1f}"
    if s.endswith("0"):
        s = f"{x:.0f}"
    return s #rf"{s} \%" if plt.rcParams["text.usetex"] else f"{s} %"

def split_in_two_lines(text,sep=None) :
    split = text.split(sep)
    return ' '.join(split[:len(split)//2]) +'\n' + ' '.join(split[len(split)//2:])
