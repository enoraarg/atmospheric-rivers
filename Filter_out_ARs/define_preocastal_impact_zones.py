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
from scipy.ndimage import gaussian_filter

from sys import path
path.append('/home/elegall/AR/scripts')
import config as cf
is_ocean = xr.open_dataset('/data/elegall/AR/ERA5/ocean_basins/is_ocean.nc')
is_ocean = is_ocean.is_ocean
is_land  = np.logical_not(is_ocean)

lat,lon = 0,1
# ----------------------------------------------
#%%                Imports
# ----------------------------------------------

smooth_dist = 5 # °
pix_per_deg = 4 # spatial resolution

smoothed_land = gaussian_filter(is_land.values.astype(float),sigma=smooth_dist*pix_per_deg,
                                 mode=('reflect','wrap'))
# reflect pour les latitudes, wrap pour les longitudes (boucler d'un côté à l'autre)

path_basins = '/data/elegall/AR/ERA5/ocean_basins/'
shortnames = ['NPac','NAtl','SAtl','SPac','IOce']

longitude_cutoff = {'NPac' : 180,
                    'NAtl' : 330,
                    'SPac' : 200,
                    'SAtl' : 0,
                    'IOce' : 70}
impact_ref = {'NPac' : [[45,235]],
              'NAtl' : [[45,350],[55,5]],
              'SPac' : [[-45,280],[-70,270]],
              'SAtl' : [[-35,15],[-70,340],[-70,10]],
              'IOce' : [[-35,110],[-65,100]]}

latitude_highcutoff = 50
latitude_lowcutoff  = 30

lonlon,latlat = np.meshgrid(is_ocean.longitude,is_ocean.latitude)

for shortname in shortnames :
    basin = xr.open_dataarray(path_basins + f"{shortname}_ocean.nc")
    coast = (smoothed_land>0.005)*basin
    coast = coast.where((np.logical_or((cf.to_180(lonlon,basin.flag_to_180) 
                                       > cf.to_180(longitude_cutoff[shortname],basin.flag_to_180)),
                                      np.abs(latlat) > latitude_highcutoff)
                        & (np.abs(latlat) > latitude_lowcutoff)))

    labels,n = label(np.where(coast.values > 0,1,0))
    label_impact = [labels[coast.latitude.to_index().get_loc(impact[lat]),
                     coast.longitude.to_index().get_loc(impact[lon])]
                    for impact in impact_ref[shortname]]
    labeled_coast = np.zeros_like(labels)
    for lab in label_impact :
        labeled_coast += np.where(labels==lab,1,0)
    
    coast = coast.where(labeled_coast)
    coast.attrs['long_name'] += ' impact coast'
    coast.name +=  '_impact_coast'

    coast.to_netcdf(f'/data/elegall/AR/ERA5/ocean_basins/{shortname}_precoast.nc')

    if shortname in ['NPac','NAtl'] :
        coastE = coast.where(cf.to_180(lonlon,basin.flag_to_180) 
                            >= cf.to_180(longitude_cutoff[shortname],basin.flag_to_180))
        coastO = coast.where(cf.to_180(lonlon,basin.flag_to_180) 
                            < cf.to_180(longitude_cutoff[shortname],basin.flag_to_180))

        for sub,subcoast in zip(['E','O'],[coastE,coastO]) : 
            subcoast.attrs['long_name'] += f' ({sub}) impact coast'
            subcoast.name +=  f'{sub}_impact_coast'

            subcoast.to_netcdf(f'/data/elegall/AR/ERA5/ocean_basins/{shortname}{sub}_precoast.nc')

# %%
if __name__ == '__main__' :
    import cartopy.crs  as ccrs
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.colors import Normalize

    projection = ccrs.Mollweide()#ccrs.PlateCarree()
    fig = plt.figure()
    ax = plt.axes(projection=projection)

    norm = Normalize(vmin=0,vmax=4)

    for ibasin,basin in enumerate(['NPac','SAtl','NAtl','SPac','IOce']) :
        print(basin)
        coast = xr.open_dataarray(f'/data/elegall/AR/ERA5/ocean_basins/{basin}_precoast.nc')

        (ibasin*coast).plot.contourf(transform = ccrs.PlateCarree(),
                    colors = '#0717F9',#'gold',#sns.color_palette('colorblind',as_cmap=True),
                    norm=norm,
                    add_colorbar=False)
        
    ax.coastlines(linewidth=0.5)

    gl = ax.gridlines(crs=ccrs.PlateCarree(), linewidth=1, color='black', 
                      alpha=0.4, linestyle=':')#, draw_labels=True)
    gl.top_labels   = False
    gl.right_labels = True
    gl.left_labels  = False
    gl.bottom_labels = False

    gl.xlabel_style = {'size': 12}
    gl.ylabel_style = {'size': 12}
        
    fig.savefig('/data/elegall/AR/ERA5/ocean_basins/map_of_oceanic_precoasts_forEGU.png')
# %%
