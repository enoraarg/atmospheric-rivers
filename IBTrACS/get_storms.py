
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created in March 2026
@author : elegall

Module to get storm infos, using IBTrACS database

# TODO 
- checker : 201809301201
devrait être associée à des cyclones. pb de taille de masque de cyclone ? de seuil de fraction de temps partagé ? à élucider ! 
et pq je ne vois pas la trace autour de la tempête sur le plot ????
"""
#%%
import sys
import xarray as xr 
import numpy as np
from scipy.ndimage import gaussian_filter, binary_dilation

import matplotlib.pyplot as plt
import matplotlib as mpl
# ----------------------------
#%%  Open IBTrACS
# ----------------------------
IB = xr.open_dataset('/data/elegall/AR/IBTrACS/IBTrACS.since1980.v04r01.nc')
IBtimes = np.ravel(IB.time)
IBtimes = IBtimes[IBtimes.astype(str) != 'NaT']
IBtimes = IBtimes[IBtimes.astype(str) > '2010']

deg_to_pix = 4
storm_diameter = 15 # 15° de diamètre pour un cyclone ; c'est large

#%% Auxilliaire

def plot_sotrm(istorm) :
    plt.plot(IB.isel(storm=istorm).lon,IB.isel(storm=istorm).lat)
    colors=['red','blue','green','yellow']
    for itype,type in enumerate(np.unique(IB.isel(storm=istorm).nature.values)) :
        local = IB.isel(storm=istorm).where(IB.isel(storm=istorm).nature == type,drop=True)
        plt.scatter(local.lon,local.lat,color=colors[itype],label=type.astype(str))
    plt.legend()

def plot_AR_and_storm(ID,test=False,spec=None) :

    '''
    Ajouter ça en méthode plot.
    '''

    fig = plt.figure()

    AR = AtmosphericRiver(ID)
    AR.get_mask(out=False,delayed=False)
    mask = AR.mask

    cmapf = mpl.colormaps['Greens'](np.linspace(0,1,mask.time.size))
    cmap  = mpl.colormaps['Greys'](np.linspace(0,1,mask.time.size))
    
    for itime,timestep in enumerate(mask.time) :
        plt.contour(mask.longitude.values,mask.latitude.values,
                    mask.sel(time=timestep).values,
                    linewidths=0.5,
                    zorder=1,
                    colors=cmap[itime])
        plt.contourf(mask.longitude.values,mask.latitude.values,
                    mask.where(mask >0,drop=True).sel(time=timestep).values,
                    vmin=1,
                    zorder=0,
                    colors=cmapf[itime],alpha=0.3)
    
    candidates = find_potential_storms(AR.mask)
    has_storm = False
    for istorm in candidates :
        plt.plot(IB.isel(storm=istorm).lon%360,IB.isel(storm=istorm).lat,color='tab:blue')

        timesteps = IB.isel(storm=istorm).time.values
        timesteps = timesteps[timesteps.astype(str) != 'NaT']
        inter = 0
        for timestep in mask.time :
            storm = get_storm_mask(istorm,timestep,timesteps,
                                   mask.longitude.values,mask.latitude.values)
            plt.contourf(mask.longitude.values,mask.latitude.values,
                    (storm+mask.isel(time=0)*0).where(storm>0),
                    #edgecolor=None,
                    vmin=1,
                    zorder=0,
                    colors='tab:blue',
                    alpha=0.1)
            
            has_storm_at_t = is_storm_within_mask_at_t(AR.mask,istorm,timestep,timesteps,
                                                       spec='all')

            if has_storm_at_t : 
                plt.scatter(IB.isel(storm=istorm).lon%360,IB.isel(storm=istorm).lat,
                            marker='+',color='r')
                inter += 1

        #print(inter,inter/mask.time.size)
        if inter/mask.time.size > 0.5 :
            plt.plot(IB.isel(storm=istorm).lon%360,IB.isel(storm=istorm).lat,color='tab:red')
            has_storm = True

    plt.title(str(int(ID)) + ' and storms')

    spec = f".{spec}" if type(spec) != type(None) else ''
    fig.savefig(f'/data/elegall/AR/results/storms_and_ARs/{int(ID)}.has_storm.{has_storm}{spec}.png')

    plt.show()

    if not test :
        plt.close()

#%%
def find_potential_storms(mask) :
    candidate_storms = []
    for timestep in mask.time :
        idx_timeclose = np.where(np.abs(IBtimes - timestep.values) < np.timedelta64(10,'m'))[0]
        IB_timeclose = np.unique(IBtimes[idx_timeclose])
        for time in IB_timeclose : 
            candidate_storms += list(np.where([time in timeseries for timeseries in IB.time])[0])
    
    candidate_storms = np.unique(candidate_storms)
    return candidate_storms

def get_storm_mask(istorm,timestep,timesteps,lons,lats) :
    all_lons = np.arange(0,360,0.25)
    all_lats = np.arange(90,-90,-0.25)
    idx_IBtime = np.where(np.abs(timesteps - timestep.values) < np.timedelta64(10,'m'))[0]

    # Get low-pressure position
    lon = IB.isel(storm=istorm).isel(date_time=idx_IBtime).lon.values%360
    lat = IB.isel(storm=istorm).isel(date_time=idx_IBtime).lat.values

    try : 
        # Get low-pressure position in indices
        ilon = np.argmin(np.abs(lons-lon))
        ilat = np.argmin(np.abs(lats-lat))

        storm = np.zeros((len(all_lats),len(all_lons)))
        storm[ilat,ilon] = 1
        storm = gaussian_filter(storm.astype(float),sigma=5*4,mode=('reflect','wrap'))>1e-4

        storm = xr.DataArray(storm,coords={'latitude':all_lats,'longitude':all_lons})
        #storm = binary_dilation(storm,iterations=storm_diameter*deg_to_pix) 

        return storm.sel(latitude=lats,longitude=lons)
    
    except : 
        return xr.DataArray(np.zeros((len(lats),len(lons))),coords={'latitude':lats,'longitude':lons})

def is_storm_within_mask_at_t(mask,istorm,timestep,timesteps,
                            storm_type='tropical',
                            how='any') :
    """
    renvoie un booléen
    """
    # Identifier les tempêtes existantes à ce moment
    idx_IBtime = np.where(np.abs(timesteps - timestep.values) < np.timedelta64(10,'m'))[0]

    # Si aucune tempête : 
    if len(idx_IBtime) == 0 :
        return False

    # Identifier le type de tempête 
    nature = IB.isel(storm=istorm).isel(date_time=idx_IBtime).nature.values.astype(str)
    if nature not in ['TS','SS','MX'] and storm_type=='tropical' :
        # = c'est un type de cyclone extra tropical, et on regarde juste les cyclones tropicaux donc on élimine
        return False

    # On regarde s'il y a intersection/proximité entre le cyclone et le masque de l'AR
    local_mask = mask.sel(time=timestep).values
    lons = mask.longitude.values
    lats = mask.latitude.values

    storm = get_storm_mask(istorm,timestep,timesteps,lons,lats)
    # utiliser plutot un gaussian filter
    # avec un seuil
    # utiliser une empreinte ronde plutôt que carrée
    # 5° de diamètre pour une tempête = 7*4 pixels
    # c'est grossier mais suffisant.?

    if how == 'any' :
        return (storm*local_mask).sum() > 0
    else : 
        return mask - storm
    
    #print(' ',itime,lat,lon)

    # checker où est situé le cyclone : plutôt proche de la queue ou de la tête ?

    #lonAR = np.round(mask.sel(time=timestep).dropna('longitude',how='all').longitude.values)
    #latAR = np.round(mask.sel(time=timestep).dropna('latitude',how='all').latitude.values)

    #inter.append(lon in lonAR and lat in latAR)

def has_storm_at_t(mask,timestep,**kwargs) :
    '''
    Useful to flag timesteps to avoid when checking extreme values
    '''
    candidate_storms = []
    idx_timeclose = np.where(np.abs(IBtimes - timestep.values) < np.timedelta64(1,'h'))[0]
    IB_timeclose = np.unique(IBtimes[idx_timeclose])
    for time in IB_timeclose : 
        candidate_storms += list(np.where([time in timeseries for timeseries in IB.time])[0])
    
    for istorm in candidate_storms :
        timesteps = IB.isel(storm=istorm).time.values
        timesteps = timesteps[timesteps.astype(str) != 'NaT']
        if is_storm_within_mask_at_t(mask,istorm,timestep,timesteps,**kwargs) :
            return True
        
    return False

def get_timesteps_without_storm(mask,storm_type='tropical') :
    '''
    plus subtil ? 
    tailler grossièrement en enlevant genre 6° de diamètre autour du centre de tempête
    et renvoyer le mask ainsi épuré de tempête tropicale
    Je pense que c'est mieux !
    '''
    has_storm = [has_storm_at_t(mask,timestep,storm_type=storm_type) for timestep in mask.time]

    return mask.sel(time=mask.time[~np.array(has_storm)])


def is_storm_close_to_mask(mask,istorm):
    """
    An AR is considered to be associated with a cyclone 
    if it shares points during more than 50% of its lifetime
    "sharing point" using rounded coordinates. crude but enough.
    (= grossier. Une approche plus fine consisterait en l'étude de la trace du cyclone vs axe AR par exemple)
    """
    timesteps = IB.isel(storm=istorm).time.values
    timesteps = timesteps[timesteps.astype(str) != 'NaT']
    inter = 0

    for timestep in mask.time :
        
        inter += is_storm_within_mask_at_t(mask,istorm,timestep,timesteps)
    
    intersection = inter/mask.time.size
    if intersection > 0 and hasattr(sys,'ps1'):
        print(intersection)
    return (intersection > 0.5)*intersection

def is_mask_associated_to_storm(mask) :
    candidates = find_potential_storms(mask)
    for candidate in candidates :
        if is_storm_close_to_mask(mask,candidate) :
            if hasattr(sys,'ps1') :
                print(candidate)
            return True
    return False

def get_basic_storm_info(istorm) :
    storm = IB.isel(storm=istorm)

    vars_of_interest = ['sid','name']

    infos = {var : storm[var] for var in vars_of_interest}

    nature = storm.nature.astype(str)
    if ('TS' in nature or 'SS' in nature) and ('ET' in nature) :
        nature = 'Trans'
    elif 'ET' in nature :
        nature = 'ET'
    elif ('TS' in nature or 'SS' in nature) :
        nature = 'TS'
    else :
        nature = 'MX'
    infos['nature'] = nature

    infos['min_pres'] = storm.wmo_pres.min()

    infos['istorm'] = istorm

    return infos

def which_storm_associated_to_mask(mask) :
    candidates = find_potential_storms(mask)
    intersection_max = 0
    infos = {var:np.nan for var in ['nature','istorm','sid','name','min_pres']}

    for candidate in candidates :
        intersection = is_storm_close_to_mask(mask,candidate)
            #if hasattr(sys,'ps1') :
            #    print(candidate)
        if intersection > intersection_max : 
            intersection_max = intersection
            infos = get_basic_storm_info(candidate)

    return infos

# %%
#if __name__ == '__main__' :
    # from sys import path
    # path.append('/home/elegall/AR/scripts')
    # from class_AR import AtmosphericRiver
    # ID = 201206161805
    # AR = AtmosphericRiver(ID)
    # AR.get_mask()
    # print(is_mask_associated_to_storm(AR.mask))
