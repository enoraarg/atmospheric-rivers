#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author : elegall

This module contains functions to manage maps extensions and longitude values.
"""

# ----------------------------------------------
#          [0,360] to [-180,180]
# ----------------------------------------------

def to_180(lon,flag_to_180=False,flag_to_360=True) :
    """"
    Transform longitude values of longitude list.

    - flag_to_180 : bool, default to False. 
        whether to have longitude ranging from -180° to 180°
    - flag_to_360 : bool, default to True.
        whether to have longitude ranging from 0° to 360°

    - lon : longitude values.
    """

    if flag_to_180 :
        return (lon+180)%360 -180
    elif flag_to_360 :
        return lon%360
    else : 
        return lon

def to_180_ds(ds,long='longitude',**kwargs) :
    '''
    Transform longitude values of an xarray.Dataset, 

    - flag_to_180 : bool, default to False. 
        whether to have longitude ranging from -180° to 180°
    - flag_to_360 : bool, default to True.
        whether to have longitude ranging from 0° to 360°

    - long : str, default to 'longitude'. 
        name of longitude variable for this dataset
        (expected something like `longitude` or `lon`)
    '''

    ds = ds.assign_coords({long:to_180(ds[long],**kwargs)})
    return ds.sortby(ds[long])


# ----------------------------------------------
#         Manage boxes
# ----------------------------------------------
import numpy as np
import xarray as xr

def get_larger_latlonbox(latitude,longitude,
                         margin=10,
                         all_lat = np.arange(90,-90-0.25,-0.25),
                         all_lon = np.arange(0,360,0.25)) :
    """
    latitude,longitude : current range of latitude and longitude values for the box (°)
    margin : degrees. extension to add to the current range. 
        Same margin is used both for latitudinal and longitudinal extension.

    all_lat, all_lon : range of possible values for latitude and longitude.
        Default has a 0.25° resolution, with longitude within the [0°,360°] range.
    
    Returns an extended range of values. 
    Takes into account th
    """
    if type(latitude) == xr.DataArray :
        latitude = latitude.values
    # Latitudes
    latmax = min(90,max(latitude)+margin)
    latmin = max(-90,min(latitude)-margin)
    latslice = all_lat[(all_lat >= latmin) & (all_lat <= latmax)] #slice(latmax,latmin)

    # Longitudes
    if type(longitude) == xr.DataArray :
        longitude = longitude.values
    flag_to_180 = ((0 in longitude) 
            or (longitude.max() + margin > 360)
            or (longitude.min() - margin < 0))
    if flag_to_180 :
        longitude = to_180(longitude,flag_to_180=flag_to_180)
        lonmax = min(180, #to_180(360,flag_to_180=flag_to_180),
                 max(longitude) + margin)
        lonmin = max(-180,#to_180(0,flag_to_180=flag_to_180),
                 min(longitude) - margin)
        all_lon = to_180(all_lon,flag_to_180=flag_to_180)
        lonslice = all_lon[(all_lon >= lonmin) & (all_lon <= lonmax)]
        lonslice = lonslice%360 
        # et normalement l'ordre est conservé
    else :
        lonmax = min(360,max(longitude) + margin)
        lonmin = max(0,min(longitude) - margin)
        lonslice = all_lon[(all_lon >= lonmin) & (all_lon <= lonmax)]
    
    return latslice,lonslice