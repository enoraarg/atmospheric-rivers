#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Jan 2025
author @eno

Module to colocate some field info to atmospheric rivers

NOTE : suggestions pour Jeanne
- ajouter les fonctions qui t'intéressent ex. get_angle
'''
# ------------------------------------------
#%%       Imports
# ------------------------------------------

# -- System things
import dask

# -- Open and play with data 
import xarray as xr
import numpy  as np

# -- Homemade
from sys import path
path.append('/home/elegall/AR/scripts')
path.append('/home/elegall/routines')
from work_with_tARget.class_AR import AtmosphericRiver
import config as cf
from auxi_src import physics as phy
from auxi_src import open_files as of
from auxi_src import manage_maps as maps
# ------------------------------------------
# %%      Auxilliary functions and definitions
# ------------------------------------------

shortnames = {'rain_rate':'rain rates', 
              'ivt':'IVT',
              'w':'vertical velocities'}

def get_barycenter(AR,da,thresmode='abs',thres=0.1,value='mean',**kwargs) :
    '''
    Docstring for get_barycenter
    
    :param AR: Description
    :param da: Description
    :param thresmode: str. default to 'abs'. Options are :
        - 'abs' : selects precipitation values above a rain rate threshold, specified by parameter `thres``
        - 'quantile' : selects precipitation values above a quantile, specifid by parameter `thres`
    :param thres: float. threshold used to select part of the precipitation data
        either in units [da] (ex. mm.h-1 for rain rates), or between 0 and 1 (percentile value)
    :param kwargs: Description

    NOTE #todo :
    associer l'aire correspondante à la sélection
    '''
    value_name = value[0].upper() + value[1:]
    if value == 'area' :
        value_name += ' of'
    if thresmode == 'abs' :
        da = da.where(da > thres)
        long_name = f'{value_name} {shortnames[da.name]} above {thres}{da.units}'
        name = f'{da.name}_{value}_thres{int(thres)}'

    elif thresmode == 'quantile' :
        qvalue = da.quantile(thres)
        da = da.where(da > qvalue)
        long_name = f'{value_name} {shortnames[da.name]} above {thres*100:.0f}th quantile'
        str_thres = str(thres).split(sep='.')
        name = f'{da.name}_{value}_q{str_thres[1]}'

    else :
        print(thresmode,thres)
        print("Sorry, I didn't understand the threshold mode")

    if value == 'area' :
        # Get the area of the zone above the input threshold
        grid_res = 0.25 #° grid resolution for ERA5 (and thus also for my IMERG data set)
        weights = np.abs(np.cos(np.deg2rad(da.latitude))) 
        gridsize = weights * (phy.R*np.deg2rad(grid_res))**2
        area = ((da > 0) * gridsize).sum() #m2
        da_area = area.assign_coords({'ID':AR.ID,
                                      'thres':thres})
        da_area.name = name
        da_area.attrs['long_name'] = long_name
        da_area.attrs['units'] = 'm**2'
        return da_area

    if da.sum() == 0 :
        # No data points are found
        # returns nan
        print('no value found.',AR.ID)
        barvalue = (da.sum()*np.nan).assign_coords({'ID':AR.ID,
                                      'latitude':np.nan,
                                      'longitude':np.nan,
                                      'frac_axis':np.nan,
                                      'time' : np.array('nat',dtype='datetime64[ns]'),
                                      #da.time[0],#np.nan,#np.datetime64('nat'),
                                      #numpy.dtypes.DateTime64DType'
                                      'frac_time':np.nan,
                                      'dist_to_axis':np.nan})
        barvalue.dist_to_axis.attrs = {'units':'°',
                                   'long_name':'Shortest Haversine distance to the tARget axis'}
        barvalue.name = name
        barvalue.attrs['long_name'] = long_name
        return barvalue

    barvalue = da.mean()

    # Compute weights = the precipitation values
    weights = np.ravel(da.values)
    weights = weights[~np.isnan(weights)]
    weights_spatial = np.array([weights for dim in da.values.shape]).T

    # Get location (indices) of points where there is precipitation
    # vérifier sortby ?
    np_data = np.where(da.values > 0,1,0)
    data_points = np.array(np.where(np_data)).T

    if len(data_points) == 1 :
        G = data_points[0]

        def get_value(coordname) : 
            coords = da[coordname]
            i_axiscoord = da.get_axis_num(coordname)
            return coords[G[i_axiscoord]]

        lat_G = get_value('latitude')
        lon_G = get_value('longitude')
        timestep = get_value('time')

    else : 
        # Multiply coordinates by the weight
        weighted_coords = weights_spatial*data_points
        # The barycenter G is at location = sum(wi * Ai)/sum(wi)
        G = np.sum(weighted_coords,axis=0)/np.sum(weights)

        # Get closest coordinates correponding to indices 
        def get_closest_coordinate(coordname) :
            """
            Returns the existing coordinate value 
            that is closest to the one corresponding to the actual coordinate value
            """
            coords = da[coordname]

            if coordname == 'longitude' :
                coords = maps.to_180(coords,
                                flag_to_180=((0 in coords) 
                                            or (coords.max() > 359 and coords.min() < 1)))
            
            i_axiscoord = da.get_axis_num(coordname)
            icoord= round(G[i_axiscoord]) # G is in units pixels
            if icoord == len(coords) :
                icoord -= 1

            coord = coords[icoord]

            if coordname == 'longitude' :
                coord = coord%360
            return coord
        
        # Get coordinates corresponding to indices 
        def interp_lin_coord(coordname) :
            """
            Returns a precise coordinate, independant of the spatial resolution of the dataset
            """
            coords = da[coordname]

            if coordname == 'longitude' :
                coords = maps.to_180(coords,
                                flag_to_180=((0 in coords) 
                                            or (coords.max() > 359 and coords.min() < 1)))
                
            icoord = da.get_axis_num(coordname)
            icoord_low = int(np.floor(G[icoord])) # G is in units pixels
            if icoord_low+1 == len(coords) :
                coord = coords[icoord_low]
            coord = (G[icoord] - icoord_low) \
                * (coords[icoord_low+1] - coords[icoord_low]) \
                + coords[icoord_low]
            
            if coordname == 'longitude' :
                coord = coord%360
            return coord

        lat_G = interp_lin_coord('latitude')
        lon_G = interp_lin_coord('longitude')

        # Get additional coordinates 
        itime = da.get_axis_num('time')
        frac_time_G = G[itime]/da.time.size

        closest_time = da.time[int(np.around(G[itime]))]
        # En attendant l'interpolation en temps de l'axe :
        timestep = AR.mask.sel(time=closest_time,method='nearest').time.values
    frac_axis_G,dist_to_axis = AR.get_fracaxis_coord(timestep,lat_G,lon_G,
                                                        out='coord_and_dist')

    # Mise au propre
    # NOTE #todo : changer le nom des coords, 
    # pour avoir + facilement des fichiers avec les coords de différentes variables ? 
    # ex : latitude_rain10 et latitude_rain01
    barvalue = barvalue.assign_coords({'ID':AR.ID,
                                      'latitude':lat_G,
                                      'longitude':lon_G,
                                      'frac_axis':frac_axis_G,
                                      'time' : timestep,#closest_time,
                                      'frac_time':frac_time_G,
                                      'dist_to_axis':dist_to_axis})
    barvalue.dist_to_axis.attrs = {'units':'°',
                                   'long_name':'Shortest Haversine distance to the tARget axis'}
    barvalue.name = name
    barvalue.attrs['long_name'] = long_name

    return barvalue

dicr_des_fonctions = {'bar':get_barycenter,'angles':get_ang}
# ------------------------------------------
# %%       Colocate some data and one AR mask
# ------------------------------------------
#@dask.delayed
def coloc_metric(ID,func='get_barycenter',da_variable=None,**kwargs) :
    '''
    Function to colocate 
    ID : AR identification label (tARget identification)

    NOTE #todo
    optimiser en n'ouvrant qu'un niveau pour les fichiers omega
    '''
    flag_close = False
    AR = AtmosphericRiver(ID)
    AR.get_mask(delayed=False)
    #AR.mask = AR.get_AR_without_Tstorm()

    if type(da_variable) == type(None) :
        print("You didn't provide any dataset. I'll open one ")
        flag_close = True
        variable = kwargs.get('variable','ivt')
        if 'spec' in kwargs :
            add_kwargs = dict(spec=kwargs['spec'],basin=kwargs.get('basin','.'))
        try : 
            da_variable = of.open_timeslice_ERA5(AR.mask.time,variable,
                                             mask=AR.mask,maskonly='rain' not in variable,
                                             **add_kwargs)[variable]
            # if variable is the rain, 
            # then we look at a broader zone than just the very masked region
            if kwargs.get('spec_var','bar') == 'w500up' :
                da_variable = da_variable.sel(level=500)
                da_variable = -da_variable.where(da_variable < 0)

            elif kwargs.get('spec_var','bar') == 'w850up' :
                da_variable = da_variable.sel(level=850)
                da_variable = -da_variable.where(da_variable < 0)
                
        except :
             print("Sorry, I don't know how to process this so far")

    elif 'rain' not in da_variable.name :
        #print("Keeping data only where the AR is. Assuming any necessary computations have already been done")
        da_variable = da_variable.where(AR.mask,drop=True)

    if 'rain' in da_variable.name :
        da_variable = AR.get_precipitation(da_variable)

    result = get_barycenter(AR,da_variable,**kwargs)

    result = dict_des_fonctions[func](AR,da_variable)

    if kwargs.get('spec_var','bar') in ['w850up','w500up'] :
        result = -result

    if flag_close :
        da_variable.close()

    return result

# %%
if __name__ == '__main__' :
    ID = 201011140004
    ivt = coloc_metric(ID)
    ivt = dask.compute(ivt)[0]

    ID = 202303130615
    rr = coloc_metric(ID,variable='rain_rate')
    rr = dask.compute(rr)[0] 
