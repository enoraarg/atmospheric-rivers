#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21  2024

@author: elegall
config file for general AR manipulations

NOTE todo :
- open _ ivt (date)
- plot map selon les variables..?
"""
#from calendar import month
from sys import path
path.append('/home/elegall/routines')
#import routine_basemap as bm

# ----------------------------------------------
#                Path
# ----------------------------------------------

path_data_AR   = '/data/elegall/AR/'
path_tARget_db = path_data_AR + 'tARget_db/ERA5/'
path_datax     = '/homedata/elegall/ERA5/' 
path_IPART     = path_data_AR + 'IPART/THR/'
path_results   = path_data_AR + 'results/'
path_ERA5_025  = '/bdd/ERA5/NETCDF/GLOBAL_025/'
path_ERA5_PL   = path_ERA5_025 + '4xdaily/AN_PL/'
path_scratchu  = '/scratchu/elegall/'
path_IMERG     = '/proju/smos/xperrot/IMERG/' # 2000 - 2024 
#path_IMERG_ERA5 = path_IMERG + 'ERA5_GRID/' # 2001 - 2022 ; 1 dossier par année, 1 fichier par mois.
path_IMERG_ERA5 = '/proju/smos/xperrot/IMERG_V7_ERA5_GRID/'
# ----------------------------------------------
#                Physics
# ----------------------------------------------
rho = 1e3 # water density, in units kg.m-3
m_to_mm = 1e3
mm_to_m = 1e-3
kgs_to_mmd = (3600*24) /rho *m_to_mm # conversion from kg s**-1 to mm day**-1
R = 6.3396e6 # Earth radius, in units m
grid_res = 0.25 # Grid resolution, in °
g_cte = 9.81 # m s**-2
Cp = 1006 # 

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
max_ID    = 10 # number of colors in the palette,,
norm_ID   = Normalize(0,max_ID)
norm_tcwv = TwoSlopeNorm(vmin=0,vcenter=20,vmax=70) # center=48
norm_ivt  = TwoSlopeNorm(vmin=0,vcenter=250,vmax=600)
cmap_ID   = LinearSegmentedColormap.from_list('Custom cmap', 
                                              sns.color_palette('bright'), 
                                              len(sns.color_palette('bright')))
norm_altflux  = TwoSlopeNorm(vmin=0,vcenter=850,vmax=1000)
# ----------------------------------------------
#         Areas
# ----------------------------------------------
#import cartopy.crs as ccrs
#fig = plt.figure(transform = ccrs.PlateCarree())
#fig_width, fig_height = fig.get_size_inches()
ratio_global_map = 4/3 #fig_width/fig_height

#projections = [ccrs.PlateCarree(), ccrs.LambertCylindrical, ccrs.Robinson()]

# global_area = bm.area_of_study(-90,90,0,360,name='Global')
# #NAtl        = bm.area_of_study(0,65,260,360,name='North Atlantic')
# #NPac        = bm.area_of_study(0,65,-110+360,-80+360,name='North Pacific')

# # # -- Définition de bassins : 
# # global_area = bm.area_of_study(-90,90,0,360,name='Global')

# NAtl        = bm.area_of_study(5,60,-80,0,name='North Atlantic')
# NAtl.flag_to_180 = True

# SAtl = bm.area_of_study(-60,-5,-60,20,name='South Atlantic')
# SAtl.flag_to_180 = True

# NPac = bm.area_of_study(5,60,140,250,name='North Pacific')
# SPac = bm.area_of_study(-60,-5,180,280,name='South Pacific')

# IOce = bm.area_of_study(-60,-5,50,120,name='Indian Ocean')

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
#all_bassins = [NAtl,SAtl,NPac,SPac,IOce]
# all_bassins_dict = {bassin.shortname:bassin
#                for bassin in all_bassins}

# ----------------------------------------------
#         Manage boxes
# ----------------------------------------------
import numpy as np
def get_larger_latlonbox(latitude,longitude,
                         margin=10,
                         all_lat = np.arange(90,-90-0.25,-0.25),
                         all_lon = np.arange(0,360,0.25)) :
    """
    latitude,longitude : current range of latitude and longitude values for the box (°)
    margin : 

    returns an extend 
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

# ----------------------------------------------
#         Manage ERA5
# ----------------------------------------------
import xarray as xr
from datetime import datetime
import glob 

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
    #print(filename)
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
    Assuming timeslice is a data array time range
    Arguments are passed to function open_month_ERA5

    **kwargs : 
    if a mask is provided, its longitude and
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
        # Assumed that 'longitude' is also
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
#         Open IMERG data
# ----------------------------------------------

def open_month_IMERG(date,**kwargs) : 
    """
    """
    datefile = datetime.strptime(date[:7],'%Y-%m').strftime('%Y%m')
    year = date[:4] 

    print(f'opening IMERG file at date {date}')
    
    filename = glob.glob(path_IMERG_ERA5 + f'{year}/*{datefile}*.nc')    
    ds = xr.open_mfdataset(filename,**kwargs)

    if kwargs.get('flag_to_180',False) :
        ds = to_180_ds(ds)
    return ds

def open_timeslice_IMERG(timeslice,**kwargs) :
    """
    timeslice :

    kwargs can include preprocess info such as 
        - a `mask` 
        - a given range of `latitude` and `longitude`
        - a `flag_to_180` to switch from the [0,360] longitude coordinates to [-180,180]
    """
    if type(timeslice) == np.datetime64 :
        timeslice = str(timeslice)
    if type(timeslice) in [str,np.str_]:
        months_from_timeslice = [timeslice]
    else : 
        months_from_timeslice = np.unique([f'{date.dt.year.values}-{date.dt.month.values:02d}' 
                                        for date in timeslice])
        
    timeslice = slice(min(months_from_timeslice),
                      max(months_from_timeslice))
    
    if 'mask' in kwargs :
        mask = kwargs.get('mask',None)
        del kwargs['mask']
        def preprocess(ds) :
            ds = ds.sel(longitude=mask.longitude,
                        latitude=mask.latitude,
                        time=timeslice) #.where(mask)
            return ds
        
        kwargs['preprocess'] = preprocess
        
    elif 'latitude' in kwargs :
        # Assumed that 'longitude' is also in kwargs (be coherent bro)
        latitude = kwargs.get('latitude',None) ; longitude = kwargs.get('longitude',None)
        del kwargs['latitude'] ; del kwargs['longitude']
        def preprocess(ds) :
            ds = ds.sel(longitude=longitude,
                        latitude=latitude,
                        time=timeslice)
            return ds
        kwargs['preprocess'] = preprocess

    else :
        def preprocess(ds) :
            ds = ds.sel(time=timeslice)
            return ds
        kwargs['preprocess'] = preprocess

    ds = []
    for date in months_from_timeslice :
        try : 
            ds.append(open_month_IMERG(date,**kwargs))
        except :
            print('oops, could not find an IMERG file for this month : ',date)

    ds = xr.concat(ds,dim='time')
    return ds

# ------------------------------------------
#%%       Parameters
# ------------------------------------------
pars = {'test':False,
            'timerange':'2022-12',
            'igroup':0,
            'nIDpergroup':None,
            'ngroups':10,
            'spec':'.',
            'dim' : 'None',
            'plots':False,
            'outputdir':path_tARget_db}
    
# ------------------------------------------
#%%       Jobarray ID
# ------------------------------------------
import numpy as np

def get_IDs_of_group(pars,
                     return_valid_timerange=False,
                     return_valid_timeslice=False,
                     return_da_kidmap=True) : 
    '''
    return_valid_timerange : bool, default to False .
        Whether to return the valid timerange (YYYY-MM), e.g. to open correct IMERG files.
    '''
    # -- Ensure test conditions
    if pars['test'] :
        pars['ngroups'] = 2
        pars['timerange'] = '2022-12-12'

    # ----------------
    # -- Load AR data
    ds_AR     = xr.open_dataset(path_tARget_db + 'globalARcatalog_ERA5_1940-2023_v4.0.nc')
    ds_AR     = ds_AR.sel(time=pars['timerange']) # preselection to facilitate computation afterwards
    # -- Get IDs at that timerange
    IDs = np.unique(ds_AR.kid.values)
    IDs = IDs[~np.isnan(IDs)]

    # ---------------
    # -- Define size of groups
    igroup = int(pars['igroup'])
    ngroups = int(pars['ngroups'])
    nIDpergroup = len(IDs)//ngroups + 1 # +1 to be sure that we cover the full range

    if igroup*nIDpergroup >= len(IDs) :
        print('No more IDs left')
        return 'Over'

    # -- The last group could be too big compared to the indices that are left 
    ilastID  = min(len(IDs)-1,(igroup+1)*nIDpergroup)
    groupIDs = IDs[igroup*nIDpergroup:ilastID]

    groups_left = len(IDs[ilastID:])//nIDpergroup +1
    print(f'({groups_left} group(s) left)')

    # -- Get valid time for this ID group
    valid_time_allID = []
    for ID in groupIDs :
        valid_time = ds_AR.kid.where(ds_AR.kid == ID,drop='True').dropna('time',how='all').time
        valid_time_allID.append(valid_time)
    valid_time_allID = xr.concat(valid_time_allID,'time')
    valid_slice      = slice(valid_time_allID.min(),valid_time_allID.max())

    dates = np.unique([f'{date.dt.year.values}-{date.dt.month.values:02d}' for date in valid_time_allID])
    print('valid dates for this group :',*dates)

    # -- Select only variable and time of interest for the rest
    da_kidmap = ds_AR.kidmap.sel(time=valid_slice)
    ds_AR.close()

    # -- Get minimum latitude
    if pars['dim'] == 'time' :
        print('keeping time dimension') 

    to_return = [groupIDs]
    if return_da_kidmap :
        to_return.append(da_kidmap)
    else : 
        da_kidmap.close()
    if return_valid_timerange : 
        to_return.append(dates)
    if return_valid_timeslice :
        to_return.append(valid_slice)
    
    return to_return

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

# ----------------------------------------------
#          [0,360] to [-180,180]
# ----------------------------------------------

def to_180(lon,flag_to_180=False,flag_to_360=True) :
    if flag_to_180 :
        return (lon+180)%360 -180
    elif flag_to_360 :
        return lon%360
    else : 
        return lon

def to_180_ds(ds,long='longitude',**kwargs) :
    '''
    long : str. name of longitude variable for this dataset
        (expected something like `longitude` or `lon`)
    '''
    # if flag_to_180 :
    ds = ds.assign_coords({long:to_180(ds[long],**kwargs)})
    return ds.sortby(ds[long])
    # else :
    #     return ds

# ----------------------------------------------
#         Check files
# ----------------------------------------------
import sys
def does_file_exist(filename,recompute=False) :
    if len(glob.glob(filename)) > 0 :
        if recompute : 
            import os
            os.system(f"rm {filename}")
            test.close()
            return False
        
        test = xr.open_dataset(filename)

        if 'ID' not in test.coords or len(test.coords) == 0 :
            import os
            os.system(f"rm {filename}")
            test.close()
            return False

        for coord in list(test.coords) :
            try : 
                if (coord not in ['latitude','longitude','time']) and (test[coord].values < 0).any()  :
                    # Il y a eu un pb dans l'écriture 
                    # il faut refaire le fichier 
                    # (c'est _un_ des signes pour le besoin de réécriture)
                    import os
                    os.system(f"rm {filename}")
                    test.close()
                    return False
            except :
                continue
                
        if hasattr(sys,'ps1') : print('good news, file exists already ! ciao')
        if hasattr(sys,'ps1') : print(' (file is ',filename)
        return True
    return False

# ----------------------------------------------
#         Vrac
# ----------------------------------------------

def verboseprint(text,**kwargs) :
    if kwargs.get('verbose',False) :
        print(text)


# %%
