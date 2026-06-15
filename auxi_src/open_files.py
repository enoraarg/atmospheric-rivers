#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author : elegall

This module contains functions and variables to open properly ERA5 and IMERG files.
"""

import xarray as xr
from datetime import datetime
import glob 
import numpy as np 

from auxi_src.local_paths import *
from auxi_src.manage_maps import to_180_ds
# ----------------------------------------------
#         Open ERA5 data
# ----------------------------------------------

# Toutes les variables ne sont pas stockées à toutes les résolutions verticales/temporelles
# sur la base de donnée de spirit.
ERA5_variables = {'tcwv' : {'resolution' : 'hourly',
                            'level' : 'AN_SF'},
                  'w' : {'resolution' : 'hourly',
                         'level' : 'AN_PL'},
                  'd' : {'resolution' : '4xdaily',
                         'level' : 'AN_PL'},
                  'u' :  {'resolution' : '4xdaily',
                          'level' : 'AN_PL'},
                  'v' : {'resolution' : '4xdaily',
                         'level' : 'AN_PL'},
                  'q' : {'resolution' : 'hourly',
                         'level' : 'AN_PL'},
                  'u10' : {'resolution' : 'hourly',
                         'level' : 'AN_SF'},
                  'v10' : {'resolution' : 'hourly',
                         'level' : 'AN_SF'},
                  'ta' : {'resolution' : 'hourly',
                          'level':'AN_PL'},
                  'cc' : {'resolution' : 'hourly',
                         'level' : 'AN_PL'},
                  'r' : {'resolution' : '4xdaily',
                         'level' : 'AN_PL'},
                  'ivtx':{'resolution':None,
                          'level':'AN_SF'},
                  'ivty':{'resolution':None,
                            'level':'AN_SF'},
                  'ivt':{'resolution':None,
                            'level':'AN_SF'},
                  'low_thetav' : {'resolution':None,
                                  'level':'AN_SF'},
                  'geopt' : {'resolution':'hourly',
                             'level':'AN_PL'}
}

# ----------------------------------------------
#         Opening ERA5 (and IMERG) files
# ----------------------------------------------

def open_month_ERA5(date,variable,resolution='hourly',level='AN_SF',verbose=True,**kwargs):
    """
    """
    if type(date) == np.datetime64 :
        date = str(date)
    if type(date) in [str,np.str_] :
        datefile = datetime.strptime(date[:7],'%Y-%m').strftime('%Y%m')
        year = date[:4]
    elif type(date) == datetime :
        datefile = str(date.year)+str(date.month).zfill(2)
        year = date.year

    if variable in ERA5_variables :
        resolution = ERA5_variables[variable]['resolution']
        level = ERA5_variables[variable]['level']

        if verbose : print(f'opening ERA5 file for variable {variable}, res. {resolution}, at date {datefile}')

    spec = 'aphe5' if variable in ['u','v','r'] else ''
    if variable in ['ivtx','ivty','ivt'] : 
        filename = path_datax + f'ivt/{year}/{variable}_{datefile}.nc'
    elif variable == 'low_thetav' :
        filename = path_datax + f'low_thetav/{year}/{variable}_{datefile}.nc'
    elif 'rain' in variable :
        if verbose : print(f'opening IMERG file at date {date}')
        filename = path_IMERG_ERA5 + f'{year}/*{datefile}*.nc'
    else : 
        filename = path_ERA5_025 + f'{resolution}/{level}/{year}/{variable}.{datefile}.{spec}*.nc'
        
    resolutions = ['hourly','4xdaily']

    try :
        file = glob.glob(filename)[0]
    except IndexError :
        if variable in ERA5_variables :
            resolution = resolutions[resolutions != resolution]
            filename = path_ERA5_025 + f'{resolution}/{level}/{year}/{variable}.{datefile}.{spec}*.nc'
            try : 
                file = glob.glob(filename)[0]
            except IndexError :
                print('I could not find your file.',date)
                return None
        else :
            print('Sorry, i could not find requested file for variable',variable, 'at date', date)
            return None
    
    ds = xr.open_mfdataset(file,**kwargs)

    if kwargs.get('flag_to_180',False) :
        ds = to_180_ds(ds)

    return ds

def open_timeslice_ERA5(timeslice,variable,**kwargs) :
    '''
    Opens IMERG files or ERA5 files for a given `variable`(str, see ERA5 variable names), 
    for a given `timeslice`,
    using the default time resolution available (see dictionnary ERA5_variables).

    Assuming timeslice is a data array time range
    Arguments are passed to function open_month_ERA5

    **kwargs : 
     - mask : xarray, default to None. The output is a box limited to the mask's longitude-latitude area. 
     - maskonly : bool, default toFalse. If set to True, the output is further limited to the input `mask`
     - latitude : a slice of longitude values, to select a latitude-longitude box. 
        It is assumed that a `longitude`argument is also passed. 
        See also `mask` argument.

    '''
    if type(timeslice) in [np.datetime64,datetime] :
        timeslice = str(timeslice)
    if type(timeslice) in [str,np.str_]:
        months_from_timeslice = [timeslice] #[datetime.strptime(timeslice[:7],'%Y-%m')] #.strftime('%Y%m')]
    else : 
        if type(timeslice[0]) == datetime :
            months_from_timeslice = np.unique([f'{date.year}-{date.month:02d}' 
                                        for date in timeslice])
        elif type(timeslice[0]) == str :
            months_from_timeslice = timeslice
        else :
            months_from_timeslice = np.unique([f'{date.dt.year.values}-{date.dt.month.values:02d}' 
                                        for date in timeslice])
        
    if 'mask' in kwargs :
        mask = kwargs.get('mask',None)
        maskonly = kwargs.get('maskonly',False)
        del kwargs['mask']
        if 'maskonly' in kwargs : del kwargs['maskonly']
        def preprocess(ds) :
            ds = ds.sel(longitude=mask.longitude,
                        latitude=mask.latitude) # lat par ordre décroissant
            if maskonly :
                print('keeping mask only !')
                ds = ds.where(mask)
            return ds
        
        kwargs['preprocess'] = preprocess
        
    if 'latitude' in kwargs :
        # Assuming that 'longitude' is also in kwargs
        latitude = kwargs.get('latitude',None) ; longitude = kwargs.get('longitude',None)
        del kwargs['latitude'] ; del kwargs['longitude']
        def preprocess(ds) :
            ds = ds.sel(longitude=longitude,
                        latitude=latitude) # lat par ordre décroissant
            return ds
        kwargs['preprocess'] = preprocess
    
    # if 'resolution' in kwargs :
    #     del kwargs['resolution']
    # if 'level' in kwargs :
    #     del kwargs['level']

    ds = []
    for date in months_from_timeslice :
        # ajouter un preprocess pour n'ouvrir que les bonnes dates du mois ? 
        #def preprocess() :
        ds_month = open_month_ERA5(date,variable,**kwargs)
        if type(ds_month) == xr.Dataset :
            ds.append(ds_month)

    try :
        ds = xr.concat(ds,dim='time').sel(time=slice(timeslice[0],timeslice[-1]))
    except : 
        ds = ds[0] #.sel(time=slice(timeslice[0],timeslice[-1]))

    return ds

