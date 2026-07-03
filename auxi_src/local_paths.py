#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author : elegall

Module storing all paths.
"""

# ----------------------------------------------
#                Path
# ----------------------------------------------

path_data_AR   = '/data/elegall/AR/'
path_tARget_db = path_data_AR + 'tARget_db/ERA5/'
tARget_db_file = 'globalARcatalog_ERA5_1940-2023_v4.0.nc'
path_datax     = '/homedata/elegall/ERA5/' 
path_IPART     = path_data_AR + 'IPART/THR/'
path_results   = path_data_AR + 'results/'
path_ERA5_025  = '/bdd/ERA5/NETCDF/GLOBAL_025/'
path_ERA5_PL   = path_ERA5_025 + '4xdaily/AN_PL/'
path_scratchu  = '/scratchu/elegall/'
path_IMERG     = '/proju/smos/xperrot/IMERG/'
path_IMERG_ERA5 = '/proju/smos/xperrot/IMERG_V7_ERA5_GRID/'

path_ocean_masks = '/data/elegall/AR/ERA5/ocean_basins/'

path_ocean_file = path_ocean_masks + 'is_ocean.nc' 

all_basins_files = {'NP':'NPac_ocean.nc',
                     'NA':'NAtl_ocean.nc',
                     'SP':'SPac_ocean.nc',
                     'SA':'SAtl_ocean.nc',
                     'IO':'IOce_ocean.nc'}
all_coast_files = {'NP':'NPac_coast.nc',
                     'NA':'NAtl_coast.nc',
                     'SP':'SPac_coast.nc',
                     'SA':'SAtl_coast.nc',
                     'IO':'IOce_coast.nc'}