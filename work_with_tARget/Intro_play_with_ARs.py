#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
juin-juillet 2026

@author: elegall

Un petit script d'intro pour jouer avec les données et s'approprier les méthodes.
"""
# ----------------------------------------------
#%%                Imports vrac
# ----------------------------------------------
import xarray as xr 

# ----------------------------------------------
#                Modules faits maison
# ----------------------------------------------
from sys import path
path.append('/home/elegall/AR/scripts')
# nécessaire dans l'éxecution 

import source.manage_maps as maps
import source.open_files as open_local

# ----------------------------------------------
#                Base de données tARget
# ----------------------------------------------
import source.local_paths as local

#ds_tARget = xr.open_dataset(local.path_tARget_db + local.tARget_db_file)
#print(ds_tARget.variables)
# Ici, n'hésite pas à fouiner un peu dans les différentes variables.
# La base de données est assez riche, mais organisée bizarrement 
# (cf article qui la décrit, Guan and Waliser 2024)
# Il y a notamment quelques variables concernant l'IVT.

# Attention notamment aux coordonnées lat,lon (cf article)

# Base de donnée qui s'arrête en décmebre 2023
# Note à moi-même : prolonger ?

# ----------------------------------------------
#                Définir un domaine
# ----------------------------------------------
lon_andes_coastline = slice(280,300)
lat_andes_coastline = slice(-30,-60)
# Proposition grossière, à préciser
# Il faut de plus préciser la zone costale pré-relief et sur l'amont du relief :
#~~~~__/\___ (où ~ est l'eau, _ la terre et /\ le relief)
#    ^^^

# Pour distinguer l'océan du continent, voici un masque  
is_ocean = xr.open_dataarray(local.path_ocean_file)
mask_andes = is_ocean.sel(latitude=lat_andes_coastline,longitude=lon_andes_coastline)
mask_andes.plot()

# ----------------------------------------------
#                Trouver une AR dans une zone donnée
# ----------------------------------------------
# Une manière de faire est de chiner sur un outil de visualisation.
#ex. : https://worldview.earthdata.nasa.gov/?v=-125.61485094788222,-76.05115214363698,3.0974194290006096,4.363831037417377&z=4&ics=true&ici=5&icd=30&l=Reference_Labels_15m(hidden),Reference_Features_15m(hidden),Coastlines_15m,IMERG_Precipitation_Rate_30min,OCI_PACE_True_Color(hidden),VIIRS_NOAA21_CorrectedReflectance_TrueColor(hidden),VIIRS_NOAA20_CorrectedReflectance_TrueColor(hidden),VIIRS_SNPP_CorrectedReflectance_TrueColor(hidden),MODIS_Aqua_CorrectedReflectance_TrueColor(hidden),MODIS_Terra_CorrectedReflectance_TrueColor&lg=true&t=2023-04-19-T13%3A44%3A59Z

timestep='2023-04-19T12'
lat=lat_andes_coastline
lon=lon_andes_coastline

from class_AR import find_which_ID
ID = find_which_ID(timestep,lat,lon)

# ----------------------------------------------
#               Jouer avec un cas de rivière atmosphérique
# ----------------------------------------------
# J'ai créé une classe pour manipuler la base de données tARget
# Tu peux y ajouter des trucs
# Faire une classe héritée par exemple ? 
from class_AR import AtmosphericRiver

AR = AtmosphericRiver(ID)
AR.get_mask() # pour voir à quoi ressemble un masque tARget pour une AR donnée
AR.plot(itime=0) # Tu peux changer l'indice pour visualier d'autres moments

# ----------------------------------------------
#%%                Associer des données de pluie, d'IVT
# ----------------------------------------------
# Les données d'IVT (norme) et de composantes latitudinale (y) et longitudinale (x) du vecteur
# sont stockées sur `local.path_datax` (calcul fait à partir des données d'ERA5) 
ivt = open_local.open_timeslice_ERA5(AR.mask.time,'ivt',mask=AR.mask)
ivtx = open_local.open_timeslice_ERA5(AR.mask.time,'ivtx',mask=AR.mask)
ivty = open_local.open_timeslice_ERA5(AR.mask.time,'ivty',mask=AR.mask)

rain_rate = open_local.open_timeslice_ERA5(AR.mask.time,'rain_rate',mask=AR.mask)

from cartopy import crs as ccrs
from source.manage_figures import norm_ivt

crs_0 = ccrs.PlateCarree()
itime = 0
AR.plot(itime=itime)
ivt.ivt.isel(time=itime).plot(transform=crs_0,cmap='coolwarm',norm=norm_ivt)
ivt_vec = xr.merge([ivtx,ivty])
step = 10
ivt_vec.isel(time=itime).sel(latitude=ivt_vec.latitude[::step],
                    longitude=ivt_vec.longitude[::step]).plot.quiver(transform=crs_0,
                                    x = 'longitude', y='latitude',
                                    u='ivtx',v='ivty',
                                    color='dimgrey',
                                            headaxislength=1,headlength=2,
                                            add_guide=False)
rain_rate.rain_rate.where(rain_rate.rain_rate >0.5).isel(time=itime).plot(cmap='gist_earth_r',transform=crs_0)

# Checker la pluie 
# et hop

# %%
