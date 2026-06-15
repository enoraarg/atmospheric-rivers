#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author : elegall

This module contains physical variables. 
"""

# ----------------------------------------------
#                Physics
# ----------------------------------------------
rho = 1e3 # water density, in units kg.m-3
m_to_mm = 1e3
mm_to_m = 1e-3
kgs_to_mmd = (3600*24) /rho *m_to_mm # conversion from kg s**-1 to mm day**-1
R = 6.3396e6 # Earth radius, in units m
g_cte = 9.81 # m s**-2
Cp = 1006 # 
kappa = 0.286 # = Rd/c_p
P0 = 1000
celsius2K = 273.15
g = 9.81

grid_res = 0.25 # Grid resolution, in °