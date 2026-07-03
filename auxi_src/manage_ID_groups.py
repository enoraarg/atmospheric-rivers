"""
A module to work with ID groups (linked to target.)
> à mettre plutôt dans work_with_target nn?
"""

# ------------------------------------------
#%%       Timeslice
# ------------------------------------------
import xarray as xr
import numpy  as np
from datetime import datetime,timedelta
import pandas as pd

from sys import path
path.append('/home/elegall/AR/scripts')
from work_with_tARget.class_AR import AtmosphericRiver
# from auxi_src.manage_objects import open_object

def get_precise_timeslice(pars) : 
    date =  int(f"{pars['year']}{pars['month']}")
    date1 = datetime.strptime(str(date),'%Y%m')
    date2 = date1 + timedelta(days=pars['delta']) # permet juste de sélectionner le mois suivant
    if pars['vraitest']:
        date2 = date1 + timedelta(days=7)
        print('test - until', date2)
    # ------------------------ 
    # -- Get IDs
    # ------------------------
    IDs = open_object(cf.path_tARget_db 
                      + f"lists_of_IDs/IDs_1940-2023_{pars['basin']}.init.long.ocean.pkl")

    IDs = np.array(IDs)
    IDs = IDs[IDs > int(f"{date1.year}{str(date1.month).zfill(2)}")*1e6]
    if pars['vraitest']:
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

    return IDs, timeslice,date1,date2

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
