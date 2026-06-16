#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created in Dec 2025
@author : elegall

Module to create a mask for each ocean 
"""
# ----------------------------------------------
#%%                Imports
# ----------------------------------------------

import xarray as xr
import numpy as np
from scipy.ndimage import label

from sys import path
path.append('/home/elegall/AR/scripts')
import config as cf
path_ocean = '/data/elegall/AR/ERA5/ocean_basins/'
is_ocean = xr.open_dataset(path_ocean+'is_ocean.nc')
is_ocean = is_ocean.is_ocean

lat,lon = 0,1

# ----------------------------------------------
#%%                North Atlantic
# ----------------------------------------------

NAtl = cf.to_180_ds(is_ocean,flag_to_180=True)
NAtl = NAtl.where(((NAtl.latitude < 80)
                  &(NAtl.latitude > 0) 
                  &(NAtl.longitude < 25)
                  &(NAtl.longitude > -100))) #drop=True
# drop nécessaire sinon tout les océans osnt connectés
center = (30,-10)
labels,n = label(np.where(NAtl.values > 0,1,0))
label_NAtl = labels[NAtl.latitude.to_index().get_loc(center[lat]),
                    NAtl.longitude.to_index().get_loc(center[lon])]
# en vérité ça inclue aussi la méditerranée bref

NAtl = NAtl.where(labels==label_NAtl)
NAtl = cf.to_180_ds(NAtl,flag_to_360=True)
NAtl.attrs['flag_to_180'] = 1
NAtl.attrs['long_name'] = 'North Atlantic'
NAtl.name = 'is_north_atlantic'

NAtl.to_netcdf(path_ocean + 'NAtl_ocean.nc')

# ----------------------------------------------
#%%                North Pacific
# ----------------------------------------------

NPac = is_ocean
NPac = NPac.where(((NPac.latitude < 80)
                  &(NPac.latitude > 0) 
                  &(NPac.longitude < 360-75)
                  &(NPac.longitude > 100)))
center = (30,200)
labels,n = label(np.where(NPac.values >0,1,0))
label_NPac = labels[NPac.latitude.to_index().get_loc(center[lat]),
                    NPac.longitude.to_index().get_loc(center[lon])]

NPac = NPac.where(labels==label_NPac)
NPac.attrs['flag_to_180'] = 0
NPac.attrs['long_name']= 'North Pacific'
NPac.name = 'is_north_pacific'

NPac.to_netcdf(path_ocean + 'NPac_ocean.nc')

# # ----------------------------------------------
# #%%                South Pacific
# # ----------------------------------------------

# SPac = is_ocean
# SPac = SPac.where(((SPac.latitude > -80)
#                   &(SPac.latitude < 0) 
#                   &(SPac.longitude < 300)
#                   &(SPac.longitude > 150)))
# center = (-30,230)
# labels,n = label(np.where(SPac.values >0,1,0))
# label_SPac = labels[SPac.latitude.to_index().get_loc(center[lat]),
#                     SPac.longitude.to_index().get_loc(center[lon])]

# SPac = SPac.where(labels==label_SPac)
# SPac.attrs['flag_to_180'] = 0
# SPac.attrs['long_name'] = 'South Pacific'
# SPac.name = 'is_south_pacific'

# SPac.to_netcdf(path_ocean + 'SPac_ocean.nc')

# ----------------------------------------------
#%%                South Atlantic
# ----------------------------------------------

SAtl = cf.to_180_ds(is_ocean,flag_to_180=True)
SAtl = SAtl.where(((SAtl.latitude > -90)
                  &(SAtl.latitude < 0) 
                  &(SAtl.longitude < 30)
                  &(SAtl.longitude > -50)))
center = (-30,-10)
labels,n = label(np.where(SAtl.values >0,1,0))
label_SAtl = labels[SAtl.latitude.to_index().get_loc(center[lat]),
                    SAtl.longitude.to_index().get_loc(center[lon])]
# en vérité ça inclue aussi la méditerranée bref

SAtl = SAtl.where(labels==label_SAtl)
SAtl = cf.to_180_ds(SAtl,flag_to_360=True)
SAtl.attrs['flag_to_180'] = 1
SAtl.attrs['long_name'] = 'South Atlantic'
SAtl.name = 'is_south_atlantic'

SAtl.to_netcdf(path_ocean + 'SAtl_ocean.nc')

# ----------------------------------------------
#%%                South Pacific
# ----------------------------------------------

SPac = is_ocean
SPac = SPac.where(((SPac.latitude > -90)
                  &(SPac.latitude < 0) 
                  &(SPac.longitude < 310)
                  &(SPac.longitude > 150)))
center = (-30,230)
labels,n = label(np.where(SPac.values >0,1,0))
label_SPac = labels[SPac.latitude.to_index().get_loc(center[lat]),
                    SPac.longitude.to_index().get_loc(center[lon])]

SPac = SPac.where(labels==label_SPac)
SPac.attrs['flag_to_180'] = 0
SPac.attrs['long_name'] = 'South Pacific'
SPac.name = 'is_south_pacific'

SPac.to_netcdf(path_ocean + 'SPac_ocean.nc')

# ----------------------------------------------
#%%                Indian Ocean
# ----------------------------------------------

IOce = is_ocean
IOce = IOce.where(((IOce.latitude > -90)
                  &(IOce.latitude < 0) 
                  &(IOce.longitude < 150)
                  &(IOce.longitude > 30)))
center = (-30,70)
labels,n = label(np.where(IOce.values >0,1,0))
label_IOce = labels[IOce.latitude.to_index().get_loc(center[lat]),
                    IOce.longitude.to_index().get_loc(center[lon])]

IOce = IOce.where(labels==label_IOce)
IOce.attrs['flag_to_180'] = 0
IOce.attrs['long_name'] = 'Indian Ocean'
IOce.name = 'is_indian_ocean'

IOce.to_netcdf(path_ocean + 'IOce_ocean.nc')

# ----------------------------------------------
#%%                Main
# # ----------------------------------------------

if __name__ == '__main__' :
    import cartopy.crs  as ccrs
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.colors import Normalize
    #sns.color_palette('colorblind')[ibassin]

    fig = plt.figure()
    ax = plt.axes(projection=ccrs.PlateCarree())
    #cmap = 'Pastel1'
    norm = Normalize(vmin=0,vmax=4)

    for ibassin,bassin in enumerate([NPac,SAtl,NAtl,SPac,IOce]) :
        #['NA','NP','SA','SP','IO']
        (ibassin*bassin).plot.contourf(transform = ccrs.PlateCarree(),
                    colors = sns.color_palette('colorblind',as_cmap=True),
                    norm=norm,
                    add_colorbar=False)
        
    ax.coastlines(linewidth=0.5)
    #ax.add_feature(cft.LAND,alpha=0.5,zorder=18)

    gl = ax.gridlines(crs=ccrs.PlateCarree(), linewidth=1, color='black', 
                      alpha=0.4, linestyle=':', draw_labels=True)
    gl.top_labels   = False
    gl.right_labels = False
    #gl.xformatter = LONGITUDE_FORMATTER
    #gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 12}
    gl.ylabel_style = {'size': 12}
        
    fig.savefig(path_ocean + 'map_of_oceanic_basins.png')
# %%
