#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Jan 2026
author @eno
Module to colocate all ARs with their IVT info in a systematic way.

> Peut être exécuté individuellement,
ou combiné avec compute_coloc.sh, qu'il faut exécuter en utilisant `sbatch`:
sbatch compute_coloc.sh
dans compute_coloc.sh, tu peux modifier les paramètres (ceux dans la variable `pars`)
compute_coloc.sh permet d'exécuter ce script mois par mois pour une année pour un bassin

> A priori tu as besoin de l'utiliser pour le bassin SP,
pour les années 2010-2023 ( = ce que j'ai pour le moment)
soit environ 1500 ARs ? ish

> pour exécuter compute_coloc.sh pour ces 14 années,
tu peux utilsier submit_job.py,
qui permet de sbatch compute_coloc.sh plusieurs fois de suite,
avec une certaine gamme de paramètres (ici, avec l'année qui est modifiée à chaque fois),
avec en bonus un petit délai entre chaque exécution pour ne pas surcharger

> important ! toujours faire des tests progressivement
= pour un mois entier
puis pour un an
puis pour tout

> attention il y aura tjr une erreur pour le mois de décembre 2023 car le mois suivant n'existe pas dans les données que j'ai

NOTE #todo : 
utiliser la fonction get_IDs de auxi_src pour éviter le sacré pavé dans main()

NOTE : suggestions pour Jeanne
- ajouter un argument à pars (parameters)
    / une possibilité par exemple spec = 'andes'
    > modifier prepropress (dans la fonction main) pour utiliser le masque correspondant
- attention aux noms de chemins 
    pour trouver ton masque d'orographie
    pour enregistrer les fichiers au bon endroit
'''

# ------------------------------------------
#%%       Imports
# ------------------------------------------

# -- System things
import glob
import sys # to check whether session is interactive with the sys.ps1 attribute
import dask
from time import time

# -- Open and play with data 
import xarray as xr
import numpy  as np
from datetime import datetime,timedelta
import pandas as pd

# -- Homemade
from sys import path
path.append('/home/elegall/AR/scripts')
path.append('/home/elegall/routines')
from work_with_tARget.class_AR import AtmosphericRiver
from config import *
import config as cf
from auxi_src.write_files import does_file_exist
import auxi_src.local_paths as lp
from auxi_src.manage_ID_groups import get_precise_timeslice
from auxi_src.getargs import getargs
from auxi_src.routine_save_objects import open_object
from Coloc_metrics.coloc_singleAR import coloc_metric

def get_outfilename(pars) : 
    return pars['outputdir'] + f"tARget/{pars['variable']}/temp.{pars['year']}.{pars['month']}.{pars['delta']}.{pars['basin']}.{pars['variable']}.{pars['thres']}.{pars['value']}.{pars['spec']}.nc"

rain_threshold = 0.1
# ------------------------------------------
# %%       Write to NetCDF
# ------------------------------------------

def write_to_netcdf(data,**kwargs) :
    print('saving dataset to netcdf....')
    encoding_info = dict(time={'dtype':'int64'}) if 'time' in data.coords else {}
    data.to_netcdf(get_outfilename(pars),encoding=encoding_info)

# ------------------------------------------
# %%       Main
# ------------------------------------------

def mainID():
    # -- Parameters
    global pars
    pars = {'is_test':True,
            'year':2022,
            'month':12,
            'delta':31,
            'spec':'coast',
            'variable':'rain_rate',
            'thresmode':'quantile',
            'basin':'IO',
            'thres':0.99,
            'value':'mean',
            'plots':False,
            'vraitest':False,#hasattr(sys,'ps1'),# = is interactif
            'outputdir':cf.path_scratchu}

    if not hasattr(sys,'ps1') :
        pars = getargs(pars)

    # -- Check if file already exists
    if does_file_exist(get_outfilename(pars)) :
        return

    date =  int(f"{pars['year']}{pars['month']}")
    date1 = datetime.strptime(str(date),'%Y%m')
    date2 = date1 + timedelta(days=pars['delta']) # permet juste de sélectionner le mois suivant
    if pars['vraitest'] :
        date2 = date1 + timedelta(days=7)
        print('test - until', date2)
    
    # ------------------------ 
    # -- Get IDs
    # ------------------------
    IDs = open_object(cf.path_tARget_db 
                      + f"lists_of_IDs/IDs_1940-2023_{pars['basin']}.init.long.ocean.pkl")

    IDs = np.array(IDs)
    IDs = IDs[IDs > int(f"{date1.year}{str(date1.month).zfill(2)}")*1e6]
    if pars['vraitest'] :
        IDs = IDs[IDs <  int(f"{date2.year}{str(date2.month).zfill(2)}{str(date2.day).zfill(2)}")*1e4 ]
    else : 
        IDs = IDs[IDs < int(f"{date2.year}{str(date2.month).zfill(2)}")*1e6]

    last = date2
    for ID in IDs :
        AR = AtmosphericRiver(ID)
        times = AR.get_timeslice()
        local_last = datetime.strptime(np.datetime_as_string(times.max())[:10],'%Y-%m-%d')
        if local_last > last :
            last = local_last
    date2 = last
    print('going from',date1,'to',date2)
    timeslice = pd.date_range(date1,date2+timedelta(days=30),freq='ME').strftime('%Y-%m').tolist()
    # + 1 mois pour être sûr d'inclure la dernière date
    # sinon pd fait la différence stricte

    #IDs,timeslice,date1,date2 = get_precise_timeslice(pars)
    # à venir mais pas encore au point

    def preprocess(ds) :
        basin = xr.open_dataarray(f"{lp.path_ocean_masks}{lp.all_basins_files[pars['basin']]}")
        basin = basin.where(basin > 0,drop=True)
        ds = ds.sel(time=slice(date1.strftime('%Y-%m-%d'),date2.strftime('%Y-%m-%d')))
        ds = ds.sel(latitude  = basin.latitude,
                    longitude = basin.longitude)
        
        if pars['spec'] == 'coast' :
            coast = xr.open_dataarray(f'{lp.path_ocean_masks}{lp.all_coast_files[pars['basin']]}')
            ds = ds.where(coast>0)
            coast.close()

        if pars['spec'] == 'land' :
            ds = ds.where(np.isnan(basin))
        basin.close()

        if pars['variable'] == 'rain_rate' :
            ds = ds.where(ds.rain_rate > rain_threshold)

        return ds
    
    variable = pars['variable']
    if variable == 'storm' :
        pass
    else : 
        da_variable = cf.open_timeslice_ERA5(timeslice,variable,preprocess=preprocess)[variable]
 
    if pars['spec'] == 'w500up' : # ce n'est plus `spec``
        da_variable = da_variable.sel(level=500)
        da_variable = -da_variable.where(da_variable < 0)

    elif pars['spec'] == 'w850up' :
        da_variable = da_variable.sel(level=850)
        da_variable = -da_variable.where(da_variable < 0)

    # ----------------------------
    # -- Colocate ARs and values!
    # ----------------------------
    print(f"Colocating {variable} ({pars['spec']}) and ARs")
    da_coloc = []

    for ID in IDs :
        if variable == 'storm' :
            AR = AtmosphericRiver(ID)
            da_coloc.append(AR.get_storm_characteristics())
        else :
            da_coloc.append(dask.delayed(coloc_metric)(ID,
                            da_variable=da_variable,
                            func='nom_de_la_fonction',
                            **pars
                            ))
    da_coloc = dask.compute(da_coloc)[0]
    da_coloc = xr.concat(da_coloc,dim='ID')

    if pars['spec'] == 'land' :
        da_coloc.name += 'land'
        da_coloc.attrs['long_name'] += ' over land'

    if pars['spec'] == 'coast' : 
        da_coloc.name += 'coast'
        da_coloc.attrs['long_name'] += ' near the coast'

    # ------------------------
    # -- Save
    # ------------------------
    # -- Close files to limit memory use
    if variable != 'storm' :
        da_variable.close()

    # -- Write data to netcdf
    write_to_netcdf(da_coloc)
    print('all done, ciao !')
    return da_coloc

#%%
def merge(basin,name_pattern) :
    """
    je réécris cette fonction à chaque situation différente.
    adapter le chemin (scratchx/u)
    adapter le nom de sortie
    adapter la variable (imerg,ivt...)
    """
    print(basin)
    temp = glob.glob(f"/scratchu/elegall/tARget/ivt/*{basin}*{name_pattern}.nc")
    temp = [xr.open_dataset(file) for file in temp]
    temp = [file.drop_vars('quantile') if 'quantile' in file.coords else file for file in temp]

    if len(temp) == 0 :
        print('no files')
        return

    total = xr.concat(temp,dim='ID')
    total = total.drop_duplicates(dim='ID')
    total.attrs['basin'] = basin

    total.to_netcdf(f'/data/elegall/AR/tARget_db/ERA5/ivt/ivt_{basin}_2010-2023.bar_q95.coast.nc')

#%%
if __name__ == '__main__' :
    t0 = time()
    da_coloc = mainID()
    print(f"all done in {(time()-t0)//60}min")

