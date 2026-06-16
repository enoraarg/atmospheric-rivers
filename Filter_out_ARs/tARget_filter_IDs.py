#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
April 2025
author @enoraarg

Module to get IDs per basin within the tARget database
'''

# ------------------------------------------
#%%       Imports
# ------------------------------------------

# -- Open and play with data 
import glob
import xarray as xr
import numpy  as np

# -- Homemade
from sys import path
path.append('/home/elegall/AR/scripts')
path.append('/home/elegall/routines')
#from ARs_and_tropics.AR_composites import IDs
import config as cf
from getargs import getargs
from routine_save_objects import save_object,open_object

# ------------------------------------------
# %%       Get IDs, save, merge
# ------------------------------------------

def get_IDs_per_basin(pars) :
    """
    Docstring for get_IDs_per_basin
    
    :param pars: Description

    returns a lsit 
    """
    basin = xr.open_dataarray(f"/data/elegall/AR/ERA5/{cf.all_basins_files[pars['basin']]}")
    print(' basin :',basin.name)
    print('getting IDs...')

    # -- Open dataset and select (to limit computational costs)
    timerange = pars['timerange']
    basin = cf.to_180_ds(basin,flag_to_180=basin.flag_to_180)

    lonmin = basin.dropna('longitude',how='all').longitude.min()
    lonmax = basin.dropna('longitude',how='all').longitude.max()
    latmin = basin.dropna('latitude',how='all').latitude.min()
    latmax = basin.dropna('latitude',how='all').latitude.max()
    #year = np.unique(ds.time.dt.year)[0]
    def preprocess(ds) :
        ds = ds.sel(time = timerange)
        ds_maps = cf.to_180_ds(ds,
                               flag_to_180=basin.flag_to_180,
                               long='lon').sel(lon = slice(lonmin, lonmax),
                                              lat = slice(latmax,latmin))[['kidmap','kstatusmap']]
        ds_k = ds[['kid','klifetime','clon','clat']]
        return xr.merge((ds_k,ds_maps))
    
    ds = xr.open_mfdataset(cf.path_tARget_db + 
                           'globalARcatalog_ERA5_1940-2023_v4.0.nc',
                            preprocess=preprocess) 

    da_kidmap = ds.kidmap.where(basin.rename({'latitude':'lat','longitude':'lon'}))
    init = np.unique(da_kidmap.where(ds.kstatusmap % 10 == 1).values)

    s_per_min = 60
    min_per_h = 60
    h_per_day = 24
    s_per_d = s_per_min*min_per_h*h_per_day
    ndays = 1
    long = np.unique(ds.kid.where(ds.klifetime > ndays*s_per_d).values)

    ds.close()

    IDs = np.array(list(set(long) & set(init)))
    IDs = IDs[~np.isnan(IDs)]

    # -- Save list
    print('saving...')
    filename = cf.path_scratchu + 'tARget/bassins/' \
        + f"temp_{pars['basin']}_{timerange}_init.long.pkl"
    print(filename)
    save_object(IDs,filename)

def get_unique_IDs_and_save(pars) :
    
    basin = cf.all_basins_dict[pars['basin']]
    print(' basin :',basin.name)
    print('getting IDs...')
    # -- Open dataset and select (to limit computational costs)
    ds = xr.open_dataset(cf.path_tARget_db + 'globalARcatalog_ERA5_1940-2023_v4.0.nc')
    
    if basin.flag_to_180 :
        print('flag 180')
        ds = cf.to_180_ds(ds,flag_to_180=True,long='lon')
        basin.lonmin,basin.lonmax = cf.to_180(basin.lonmin,flag_to_180=True),cf.to_180(basin.lonmax,flag_to_180=True)
        
    timerange = pars['timerange']
    ds = ds.sel(time = slice(timerange.split(sep='-')[0],timerange.split(sep='-')[-1]))
    ds = ds.sel(lon = slice(basin.lonmin, basin.lonmax),
                lat = slice(basin.latmax,basin.latmin))

    # -- Get list of unique IDs at this timerange & region
    init = ds.kidmap.where(ds.kstatusmap % 10 == 1)
    IDs = np.unique(ds.kidmap.values)
    IDs = IDs[~np.isnan(IDs)]

    ds.close()

    # -- Save list
    print('saving...')
    filename = cf.path_scratchu + 'tARget/bassins/' \
        + f"temp_{basin.shortname}_{pars['timerange']}_init.pkl"
    save_object(IDs,filename)
    
def filter_out_short_ARs(pars) :
    '''
    '''
    ds_AR = xr.open_dataset(cf.path_tARget_db + 'globalARcatalog_ERA5_1940-2023_v4.0.nc')
    ds_AR = ds_AR.sel(time=pars['timerange'])
    ndays = pars['ndays']

    s_per_min = 60
    min_per_h = 60
    h_per_day = 24
    s_per_d = s_per_min*min_per_h*h_per_day

    IDs_more_than_1day = np.unique(ds_AR.kid.where(ds_AR.klifetime > ndays*s_per_d))
    IDs_more_than_1day = IDs_more_than_1day[~np.isnan(IDs_more_than_1day)]

    ds_AR.close()

    # -- Save list
    filename = cf.path_scratchu + 'tARget/bassins/' + \
        f"temp_longAR_{ndays}d.{pars['timerange']}.pkl"
    print('saving...', filename)
    save_object(IDs_more_than_1day,filename)

def filter_timerange(pars) :
    # filtrer strict pour ne pas avoir des AR qui dépassent !!
    ds = xr.open_dataset(cf.path_tARget_db + 'globalARcatalog_ERA5_1940-2023_v4.0.nc')
    ds = ds.sel(time=pars['timerange'])

    # -- Get list of unique IDs at this timerange & region
    IDs = np.unique(ds.kidmap.values)
    IDs = IDs[~np.isnan(IDs)]

    ds.close()

    # -- Save list
    print('saving...')
    filename = cf.path_tARget_db + f"lists_of_IDs/IDs_{pars['timerange']}.pkl" 
    save_object(IDs,filename)

def filter_out_continent(pars) :
    is_ocean = xr.open_dataset('/data/elegall/AR/ERA5/is_ocean.nc')
    is_ocean = is_ocean.is_ocean
    
    def frac_ocean(mask) : return np.mean([(mask.sel(time=time)*is_ocean.where(mask.sel(time=time))).sum()/mask.sel(time=time).sum() for time in mask.time]) 
    
    from work_with_tARget.class_AR import AtmosphericRiver
    from tqdm import tqdm
    
    IDs = open_object(cf.path_tARget_db + f"lists_of_IDs/IDs_{pars['timerange']}_{pars['basin']}.init.long.pkl")    
    
    ocean_ID = []
    for ID in tqdm(IDs) :
        AR = AtmosphericRiver(ID)
        AR.get_mask(out=False,delayed=False) # HUM DELAYED CA VA ON TENNUIE ?
        
        if frac_ocean(AR.mask) > 0.5 :
            ocean_ID.append(ID)
    #(AR.mask.isel(time=-1)*is_ocean.where(AR.mask.isel(time=-1))).sum()/AR.mask.isel(time=-1).sum()
    # si une trop grosse fraction d'AR est sur le continent ? mmmh

    filename  = cf.path_tARget_db + f"lists_of_IDs/IDs_{pars['timerange']}_{pars['basin']}.init.long.ocean.pkl"
    save_object(ocean_ID,filename)
    
def merge_lists_and_save(name_pattern) :
    filenames = glob.glob(cf.path_scratchu \
        + f"tARget/bassins/temp_{name_pattern}*.pkl")

    files = [open_object(filename) for filename in filenames]

    all_IDs = np.concatenate(files,axis=None)
    all_IDs = np.unique(all_IDs)

    save_object(all_IDs,
                cf.path_tARget_db + f"lists_of_IDs/IDs_{name_pattern}.pkl")

def filter_basin_and_length():
    long = open_object(cf.path_tARget_db + f"lists_of_IDs/IDs_longAR_{pars['ndays']}d.pkl")
    all_basins = {}
    long_basins = {}
    for basin in ['NP','SP','NA','SA','IO'] :
        all_basins[basin] = open_object(cf.path_tARget_db + f"lists_of_IDs/IDs_{basin}.pkl")
        long_basins[basin] = list(set(long) & set(all_basins[basin]))
        save_object(long_basins[basin],cf.path_tARget_db + f"lists_of_IDs/IDs_long_{pars['ndays']}d_{basin}.pkl")

    for basin in ['NP','SP','NA','SA','IO'] :
        print('-----',basin,'----')
        print(len(long_basins[basin]),'ARs > 1day')
        print('=',round(len(long_basins[basin])/len(all_basins[basin])*100),'% retained')

# filter years where q = à partir de 1994

# ------------------------------------------
# %%       Main
# ------------------------------------------

def main():

    global pars
    pars = {'is_test':False,
            'timerange':'1940-2023',
            #'ngroups':10,
            'basin':'NP',
            'filter':'ocean',
            'ndays':1,
            'merge':False}
    pars = getargs(pars)

    if pars['is_test'] : 
        pars['timerange'] = '2022'
    
    if pars['filter'] == 'longbasin' :
        get_IDs_per_basin(pars)
        print('ok')

    elif pars['filter'] == 'basin' :
        get_unique_IDs_and_save(pars)
        print('ok')
    elif pars['filter'] == 'long' :
        filter_out_short_ARs(pars)
        print('ok')
    elif pars['filter'] == 'timerange' :
        filter_timerange(pars)
        print('ok')
    elif pars['filter'] in ['ocean','continent','land'] :
        filter_out_continent(pars)
        print('ok')

    if pars['merge'] : 
        name_pattern = pars['basin'] if (pars['filter'] == 'basin') else f"longAR_{pars['ndays']}d"
        merge_lists_and_save(name_pattern)

if __name__ == '__main__' :
    main()