#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 2025

@author: elegall

Module to define a class of atmospheric rivers, 
on the basis of the detected tARget - ERA5 database.

Méthodes importantes là-dedans : 
Pour manipuler les données
-get_mask

Pour manipuler l'axe fourni par tARget :
-get_axis

Pour visualiser :
-get_crs
-get_latlon_for_plot
-plot
-

NOTE #todo
une init() avec self, timeslice :
- interpoler axe et mask en temps .... pour avoir une plus haute res...
- distance à l'axe
"""
# ----------------------------------------------
#%%                Imports
# ----------------------------------------------
from datetime import datetime, timedelta
import xarray as xr
import numpy as np
from scipy.stats import linregress
import cartopy.crs as ccrs
import dask
import metpy.calc as mpcalc

from sys import path
path.append('/home/elegall/AR/scripts')
#from IBTrACS.get_storms import which_storm_associated_to_mask
#import config as cf

import auxi_src.local_paths as local
import auxi_src.manage_maps as maps
import auxi_src.open_files as open_local

# ----------------------------------------------
#%%             Auxilliary
# ----------------------------------------------

def find_which_ID(timestep,lat,lon,da_kidmap=None) :
    '''
    Returns ID of the AR in a given zone (defined by a `lat`,`lon` range) at a given `timestep``
    If several IDs are found : prints all IDs and returns the first one.
    '''
    if isinstance(da_kidmap,type(None)) :
        da_kidmap = xr.open_mfdataset(local.path_tARget_db \
            + 'globalARcatalog_ERA5_1940-2023_v4.0.nc',
            preprocess=lambda ds: ds.sel(time=timestep,lat=lat,lon=lon).kidmap)
        da_kidmap = da_kidmap.kidmap

    ID = np.unique(da_kidmap.values)
    ID = ID[~np.isnan(ID)]

    if len(ID) > 1 :
        print('more than one ID')
        for single_ID in ID :
            print(single_ID)

    da_kidmap.close()
    
    return ID[0]

# ----------------------------------------------
#%%                Physics
# ----------------------------------------------
kappa = 0.286 # = Rd/c_p
P0 = 1000
celsius2K = 273.15
g = 9.81

# ----------------------------------------------
#%%                Class
# ----------------------------------------------
class AtmosphericRiver :
    def __init__(self,ID,**kwargs):
        self.ID = ID
    
    def get_idx_at_timestep(self,timestep,da_kid=None,flag_close=False,**kwargs) :
        if isinstance(da_kid,type(None)) :
            flag_close = True
            def preprocess_time(ds) :
                '''
                Preselection
                '''
                ds = ds.sel(time=timestep).kid
                return ds
        
            da_kid = xr.open_mfdataset(local.path_tARget_db \
            + 'globalARcatalog_ERA5_1940-2023_v4.0.nc',preprocess=preprocess_time)

        else : 
            if 'time' in da_kid.dims :
                da_kid = da_kid.sel(time=timestep)

        idx  = da_kid.isel(ens=0,lev=0).to_index().get_loc(self.ID)
        
        if flag_close :
            da_kid.close()
        return idx

    def get_timeslice(self,ds = None,flag_close_ds = False) :
        if isinstance(ds,type(None)) :
            flag_close_ds = True
            ds = xr.open_dataset(local.path_tARget_db \
            + 'globalARcatalog_ERA5_1940-2023_v4.0.nc')[['kid','klifetime']]

        # Pre select a timeslice 
        firstdate = datetime.strptime(str(self.ID)[:10],'%Y%m%d%H')#.strftime('%Y-%m-%dT%H')
        ifirstdate = self.get_idx_at_timestep(firstdate,da_kid=ds.kid)
        seconds_per_timestep = 60*60*6
        n_timesteps = int(ds.klifetime.sel(time=firstdate).isel(lat=ifirstdate).values[0][0] / seconds_per_timestep)
        delta = timedelta(hours = (n_timesteps-1)*6)
        timeslice = ds.time.sel(time=slice(firstdate,firstdate + delta))
        # delta      = timedelta(days=14) # arbitraire.
        # lastdate   = firstdate + delta
        # timeslice  = slice(firstdate,lastdate)
        # # Ou alors
        # # Get actual timeslice from database
        # timeslice  = ds.kid.where(ds.kid == self.ID,drop='True').dropna('time',how='all').time

        if flag_close_ds :
            ds.close()

        return timeslice
    
    def get_month(self) :
        '''
        returns valid months where AR exists
        as `YYYY-MM`
        '''
        timeslice = self.get_timeslice()
        months = np.unique([f'{date.dt.year.values}-{date.dt.month.values:02d}' for date in timeslice])
        return months
    
    def get_axis_at_timestep(self,timestep,ds_AR=None,**kwargs) :
        '''
        - timestep : single time instance (not a range, not a slice)
        transect.axis = np.array((axislat,axislon)).T

        Renvoie axis sous la forme d'une liste de couples (lat,lon)
        '''
        if isinstance(ds_AR,type(None)) :
            def preprocess_time(ds) :
                '''
                Preselection
                '''
                ds = ds.sel(time=timestep)
                return ds[['kid','axislat','axislon']]

            ds_AR = xr.open_mfdataset(local.path_tARget_db \
                + 'globalARcatalog_ERA5_1940-2023_v4.0.nc',preprocess=preprocess_time)

        if 'time' in ds_AR.dims :
            ds_AR = ds_AR.sel(time=timestep)

        idx  = self.get_idx_at_timestep(timestep,da_kid = ds_AR.kid)

        axislat = ds_AR.axislat.isel(ens=0,lev=0,lat=idx).values
        axislat = axislat[~np.isnan(axislat)] 

        axislon = ds_AR.axislon.isel(ens=0,lev=0,lat=idx).values
        axislon = axislon[~np.isnan(axislon)]

        return np.array((axislat,axislon)).T
    
    def get_fracaxis_coord(self,timestep,ylat,ylon,out='coord',**kwargs) :
        '''
        Returns the index of the point of the tARget axis that is closest to the point 
        Y of coordinates (ylat,ylon)
        Using the Haversine (great circle) distances

        = the space coordinate in terms of frac_axis
        '''
        try : 
            axis = self.get_axis_at_timestep(timestep,**kwargs)
        except :
            timeslice = self.get_timeslice()
            timestep = timeslice[np.abs(timestep-timeslice).argmin()]
            axis = self.get_axis_at_timestep(timestep,**kwargs)

        from sklearn.metrics.pairwise import haversine_distances
        distances = haversine_distances(np.deg2rad(axis),[np.deg2rad([ylat,ylon])])
        imin = np.argmin(distances)

        if out == 'coord' :
            return imin/len(axis) #,axis[imin]
        elif out == 'coord_and_dist' :
            return imin/len(axis),np.rad2deg(distances[imin])[0]
    
    def get_normalized_axis(self,axis=None,timestep=None,**kwargs) :
        '''
        Takes as input an axis and returns a normalized list of indices along this axis.
        If no `axis` is provided, a `timestep`must be,
        in which case the indices are calculated along the tARget axis at that timestep.
        '''
        if isinstance(axis,type(None)) :
            axis = self.get_axis_at_timestep(timestep,**kwargs)

        npoints = len(axis)
        fraction_of_axis = np.linspace(0,1,npoints)

        return fraction_of_axis

    def get_point_at_fraction_of_axis(self,timestep,fraction) :
        axis = self.get_axis_at_timestep(timestep)
        idx_norm = self.get_normalized_axis(timestep,axis)
        
        i_fraction = np.abs(idx_norm - fraction).argmin()

        return axis[i_fraction]
        
    def get_mask_v1(self,ds=None,flag_close_ds=False,out=True) : 
        '''
        '''
        if isinstance(ds,type(None)) :
            flag_close_ds = True
            ds = xr.open_dataset(local.path_tARget_db \
            + 'globalARcatalog_ERA5_1940-2023_v4.0.nc')

        # -- Get timeslice
        timeslice = self.get_timeslice(ds=ds)
        extrait = ds.kidmap.sel(time=timeslice)

        # -- Define mask of AR
        lats = extrait.where(extrait == self.ID).dropna('lat',how='all').lat
        lons = extrait.where(extrait == self.ID).dropna('lon',how='all').lon

        mask_AR = (ds.kidmap.sel(lat=lats,lon=lons,time=timeslice) == self.ID)
        # pq je n'utilisais pas extrait ? enfin bon ça revient au même je pense

        mask_AR = mask_AR.squeeze().drop_vars(['lev','ens'])
        mask_AR = mask_AR.rename({'lat':'latitude','lon':'longitude'})

        hemisphere = 'N' if lats.mean().values > 0 else 'S'
        self.hemisphere = hemisphere
        
        self.mask = mask_AR
        
        if flag_close_ds :
            ds.close()

        if out :
            return mask_AR
        
    def get_mask_singletimestep(self,da_kidmap) :
        '''
        da_kidmap : xr.DataArray,
        preselected at the timestpe of interest
        '''
        #timestep = timestep
        #extrait = da_kidmap.sel(time=timestep)
        # -- Define mask of AR
        lats = da_kidmap.where(da_kidmap == self.ID).dropna('lat',how='all').lat
        lons = da_kidmap.where(da_kidmap == self.ID).dropna('lon',how='all').lon

        mask_AR = (da_kidmap.sel(lat=lats,lon=lons) == self.ID)

        mask_AR = mask_AR.squeeze().drop_vars(['lev','ens'])
        mask_AR = mask_AR.rename({'lat':'latitude','lon':'longitude'})
        
        return mask_AR
        
    def get_mask(self,ds=None,flag_close_ds=False,out=False,delayed=True) : 
        '''
        '''
        if isinstance(ds,type(None)) :
            flag_close_ds = True
            ds = xr.open_dataset(local.path_tARget_db \
            + 'globalARcatalog_ERA5_1940-2023_v4.0.nc')[['kid','klifetime','kidmap']]

        # -- Get timeslice
        timeslice = self.get_timeslice(ds=ds)
        
        all_masks = []
        for timestep in timeslice :
            if delayed :
                all_masks.append(dask.delayed(self.get_mask_singletimestep)(ds.kidmap.sel(time=timestep)))
            else :
                all_masks.append(self.get_mask_singletimestep(ds.kidmap.sel(time=timestep)))

        if delayed :
            all_masks = dask.compute(all_masks)[0]
        mask_AR = xr.concat(all_masks,join='outer',dim='time').fillna(0)
        mask_AR = mask_AR.sortby(mask_AR.latitude,ascending=False)

        hemisphere = 'N' if mask_AR.latitude.mean().values > 0 else 'S'
        self.hemisphere = hemisphere
        self.mask = mask_AR
        
        if flag_close_ds :
            ds.close()

        if out :
            return mask_AR

    def get_projection_matrix_at_t(self,axis_lon,axis_lat) : 
        '''
        Performs a linear approximation of the input axis 
        (e.g. moisture transport axis within the AR)
        The axis must be non-redundent
        Computes the matrix to project vectors in an AR-referential :
        (O,(tail->head),(pole->equator))
        (the matrix is thus hemisphere-dependant)
        using the linear regresssion to get the (tail->head) axis
        '''
        reg   = linregress(axis_lon,axis_lat)
        theta = np.arctan(reg.slope)

        if self.hemisphere  == 'N' :
            proj_matrix = np.array([[np.cos(theta), np.sin(theta)],
                                    [np.sin(theta),-np.cos(theta)]])

        else :
            proj_matrix = np.array([[ np.cos(theta), np.sin(theta)],
                                    [-np.sin(theta), np.cos(theta)]])

        return proj_matrix

    def get_projection_matrix_lifetime(self,edges=None,data=None,mask_AR=None,**kwargs) :
        '''
        At least one of edges or data shoukd be provided
        If edges are not provided, data is used to compute the edge at each time
        edges and data, when provided, should be arrays of length of the lifetime of the AR
        '''

        all_proj_mat = []

        timeslice = self.get_timeslice()
        
        if isinstance(mask_AR,type(None)) and isinstance(edges,type(None)) :
            mask_AR = self.get_mask()

        for itime in range(timeslice) : 
            if isinstance(edges,type(None)) :
                print('No edge was provided. Importing edge detection (no conflicts, fingers crossed)')
                from scripts.axes.tARget_get_axes_v1 import find_edge_at_timestep
                edge = find_edge_at_timestep(self.ID,data[itime],mask_AR=mask_AR,**kwargs) 
            else :
                edge = edges[itime]

            proj_matrix = self.get_projection_matrix_at_t(edge.border_lon,edge.border_lat)

            all_proj_mat.append(proj_matrix)

        self.proj_mat = all_proj_mat

    def get_projected_vectors_at_t(self,timestep,u,v) :
        '''
        Arguments :
        -----------
        u = zonal component
        v = meridional component
        Both are components of the horizontal vector

        Returns :
        ---------
        cross-AR and along-AR component of the vetor
        '''
        axis = self.get_axis_at_timestep(timestep)
        proj_matrix  = self.get_projection_matrix_at_t(axis.T[1],axis.T[0])

        along_AR = proj_matrix[0][0]*u + proj_matrix[0][1]*v
        cross_AR = proj_matrix[1][0]*u + proj_matrix[1][1]*v

        return cross_AR,along_AR
    
    def get_crs(self,timestep=slice(None)) :
        #if isinstance(timestep,type(None)) :
        lonslice = self.mask.sel(time=timestep).longitude.dropna('longitude',how='all')
        #else : 
        lon_min = lonslice.min().values ; lon_max = lonslice.max().values

        # -- Whether to center the plot on the pacific or on the atlantic
        center_at_180 = ((lon_min <= 180) 
                        and (lon_max >= 180)
                        and (0 not in lonslice.values))

        self.plot_to_180 = center_at_180 # justement ça c'est un cas pacifique ????
        print('center plot at 180 ? ', center_at_180)
        # Coordinate system to use to create the ax :
        crs_ax = ccrs.PlateCarree(central_longitude=180*center_at_180)
        self.crs = crs_ax
        
        return crs_ax
        
    def get_latlon_for_plot(self,timestep=slice(None),out=True) :

        mask = self.mask.sel(time=timestep)
        lonslice = mask.where(mask >0 ).dropna('longitude',how='all').longitude
        latslice = mask.where(mask >0 ).dropna('latitude',how='all').latitude

        if type(timestep) != slice :
            latslice,lonslice = maps.get__larger_latlonbox(latslice,lonslice)

        data_to_180 = ((0 in lonslice) 
                    or (lonslice.max()+ 10 > 360)
                    or (lonslice.min() - 10 < 0))
        self.data_to_180 = data_to_180

        lonslice = maps.to_180(lonslice,flag_to_180=data_to_180)
        #True if lonW >= lonE else False 


        #lonW = maps.to_180(lonW,flag_to_180=data_to_180) ; lonE = maps.to_180(lonE,flag_to_180=data_to_180)
        #mask = maps.to_180_ds(self.mask,long='longitude',flag_to_180=data_to_180)

        #lonslice = mask.longitude
        #lonslice = lonslice[(lonslice >= lonW) & (lonslice <= lonE)] if (lonW <= lonE) \
        #        else lonslice[(lonslice >= lonW) | (lonslice <= lonE)]
            
        # -- Latitudes : 
        #latslice = self.mask.latitude
        
        # si le plot est en [-180 180 ]
        # alors je dois mettre mes données en de même ???
        
        if out :
            return latslice,lonslice
        
    def get_ivt(self,timeslice=None,
                mask=None,only_AR=False,vector=False,
                **kwargs) :
        '''
        timeslice : list of timesteps where to compute the IVT ; 
            if not provided, default is to compute the IVT for the full lifetime of the AR
        mask : spacial domain where to compute the IVT.
            Default would be the tARget mask ;  but could be any other mask
        only_AR : whether to compute the IVT strictly where there is the mask
            Default is `False`, which computes the IVT for the full latitude-longitude box that encompasses the mask
        vector : whether to return the wo components for the vec(IVT), or the norm  ||IVT||
            Default is False (computes the norm)
        '''
        try :
            self.mask
        except :
            self.get_mask()

        if isinstance(timeslice,type(None)) :
            timeslice = self.mask.time
            
        mask = self.mask if isinstance(mask,type(None)) else mask
        kwargs = kwargs | {'mask':mask}

        # -- Get data
        u = open_local.open_timeslice_ERA5(timeslice,'u',**open_local.ERA5_variables['u'],**kwargs)
        v = open_local.open_timeslice_ERA5(timeslice,'v',**open_local.ERA5_variables['v'],**kwargs)
        q = open_local.open_timeslice_ERA5(timeslice,'q',**open_local.ERA5_variables['q'],**kwargs)
        
        # -- Compute
        uflux = (u.u * q.q)#.where(mask)
        vflux = (v.v * q.q)#.where(mask)
        if only_AR :
            uflux = uflux.where(mask,drop=True)
            vflux = vflux.where(mask,drop=True)
        
        g = 9.81
        
        hPa_to_Pa = 1e2
        uflux = 1/g * uflux.integrate('level') * hPa_to_Pa
        vflux = 1/g * vflux.integrate('level') * hPa_to_Pa
        
        if vector :
            # -- Attributes
            uflux.name = 'ivt_u'
            uflux.attrs['long_name'] = "Zonal component of the integrated water vapour transport"
            uflux.attrs['units'] = 'kg m**-1 s**-1'
            
            vflux.name = 'ivt_v'
            vflux.attrs['long_name'] = "Meridional component of the integrated water vapour transport"
            vflux.attrs['units'] = 'kg m**-1 s**-1'
            
            return uflux,vflux
        
        else :
            ivt = xr.apply_ufunc(lambda a,b : np.sqrt(a**2+b**2),uflux,vflux,dask='allowed')
            
            # -- Attributes
            ivt.name = 'ivt'
            ivt.attrs['long_name'] = "Integrated water vapour transport"
            ivt.attrs['units'] = 'kg m**-1 s**-1'
            
            return ivt
       
    def get_ivt_h75(self,timeslice=None,mask=None,only_AR=False,**kwargs) :
        try :
            self.mask
        except :
            self.get_mask()
        if isinstance(timeslice,type(None)) :
            timeslice = self.mask.time

        mask = self.mask if isinstance(mask,type(None)) else mask
        kwargs = kwargs | {'mask':mask}
        
        u = open_local.open_timeslice_ERA5(self.mask.time,'u',**open_local.ERA5_variables['u'],**kwargs)
        v = open_local.open_timeslice_ERA5(self.mask.time,'v',**open_local.ERA5_variables['v'],**kwargs)
        q = open_local.open_timeslice_ERA5(self.mask.time,'q',**open_local.ERA5_variables['q'],**kwargs)

        uflux = (u.u * q.q)#.where(self.mask)
        vflux = (v.v * q.q)#.where(self.mask)
        
        flux = xr.apply_ufunc(lambda a,b : np.sqrt(a**2 + b**2),uflux,vflux,dask='allowed')
        
        h      = 0.75
        flux75 = flux.quantile(h,dim='level')
        H75    = flux.where(flux==flux75)

        h_idx  = H75.fillna(0).argmax('level')
        # Create a list of indices (instead of a 3D matrix)
        h_idx  = h_idx.stack(points=('latitude','longitude','time')) 
        # use the list to get corresponding level values
        H75    = flux.level.isel(level=h_idx)
        # go back to the 3D matrix, with correct labeling of axes (and correct order for points) (<3)
        H75    = H75.unstack()
        
        if only_AR :
            H75 = H75.where(self.mask)

        # -- Attributes 
        H75.name = 'H75'
        H75.attrs['long_name'] = 'Height of 75th percentile of moisture flux'
        H75.attrs['units'] = 'hPa'
        
        return H75
    
    def get_thetav(self,level='low',timeslice=None,mask=None,only_AR=False,**kwargs) :
        try :
            self.mask
        except :
            self.get_mask()
        if isinstance(timeslice,type(None)) :
            timeslice = self.mask.time

        mask = self.mask if isinstance(mask,type(None)) else mask
        kwargs = kwargs | {'mask':mask}
            
        if level == 'low' :
            levelslice = slice(850,1000)
        elif level == 'mid' :
            levelslice = slice(400,500)
        elif level == 'high' :
            levelslice = slice(200,300)
            
        # -- Get data
        q  = open_local.open_timeslice_ERA5(timeslice,'q',**open_local.ERA5_variables['q'],**kwargs).q
        ta = open_local.open_timeslice_ERA5(timeslice,'ta',**open_local.ERA5_variables['ta'],**kwargs).ta
        
        if only_AR :
            q = q.where(mask)
            ta = ta.where(mask)

        # -- Compute virtual potential temperature
        levels = q.sel(level=levelslice).level
        thetav_levels = []
        for Plevel in levels :

            ta_lev = ta.sel(level=Plevel)
            q_lev  = q.sel(level=Plevel)

            # -- Compute mixing ratio
            r  = q_lev/(1-q_lev) 

            # Calculate potential temperature (theta)
            theta = (ta_lev + celsius2K) * ((P0/Plevel)**kappa)
            
            # Calculate virtual potential temperature (thetav)
            thetav = theta * (1 + 0.608 * r)

            #tlevel = theta.compute_at_level(Plevel,ta,q)
            thetav_levels.append(thetav)
            
        def compute_thetav_at_level(P,ta,q) :
            ta_lev = ta.sel(level=P)
            q_lev  = q.sel(level=P)

            # -- Compute mixing ratio
            r  = q_lev/(1-q_lev) 

            # Calculate potential temperature (theta)
            theta = (ta_lev + celsius2K) * ((P0/P)**kappa)
            
            # Calculate virtual potential temperature (thetav)
            thetav = theta * (1 + 0.608 * r)
            
            return thetav
            
        #thetav_levels = xr.apply_ufunc(lambda ta,q,levelslice : [compute_thetav_at_level(P,ta,q) for P in levels],
        #                        ta,q,levelslice,
        #                        dask='allowed') # iy oara

        thetav = xr.concat(thetav_levels,dim='level')
        thetav = thetav.mean(dim='level')
        thetav = thetav.squeeze()

        # -- Attributes
        thetav.name = level+'_thetav'
        thetav.attrs['long_name'] = f"Mean virtual potential temperature at {levelslice}"
        thetav.attrs['units'] = 'K'
        
        return thetav
    
    def get_AR_without_Tstorm(self) : 
        from IBTrACS.get_storms import get_timesteps_without_Tstorm
        mask = get_timesteps_without_Tstorm(self.mask)
        return mask
    
    def is_AR_associated_to_storm(self) :
        from IBTrACS.get_storms import is_mask_associated_to_storm
        return is_mask_associated_to_storm(self.mask)

    def get_storm_characteristics(self) :
        if not hasattr(self,'mask') :
            self.get_mask()
        from IBTrACS.get_storms import which_storm_associated_to_mask
        infos = which_storm_associated_to_mask(self.mask)
        return xr.Dataset(infos,coords={'ID':self.ID})
         

    def plot(self,timestep=None,itime=0,out=False):
        """
        Plots a simple map around the AR, 
        at a given `timestep` value
        if `timestep` is not given, then a time index `itime` is used (int, default to 0)
        `out` : bool, default to False. Whether to returns the figure and axis
        """
        if not hasattr(self,'mask') :
            self.get_mask(out=False)
        #if not hasattr(self,'plot_to_180') :
        import cartopy.crs as ccrs
        from cartopy import feature as cft
        from   cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
        import matplotlib.pyplot as plt

        crs_ax = self.get_crs()
        crs_0 = ccrs.PlateCarree(central_longitude=0)
        fig  = plt.figure()
        ax = plt.axes(projection=crs_ax)

        if timestep == None : 
            timestep = self.mask.time[itime]

        self.mask.sel(time=timestep).plot.contour(ax=ax,transform=crs_0,
                                    zorder=20,
                                    linewidths=1,
                                    colors='tab:red')
        ax.coastlines(linewidth=0.5)
        ax.add_feature(cft.LAND,alpha=0.5,zorder=18)
        gl = ax.gridlines(crs=crs_0, linewidth=1, color='black', alpha=0.4, linestyle=':', draw_labels=True)
        gl.top_labels   = False
        gl.right_labels = False
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        gl.xlabel_style = {'size': 12}
        gl.ylabel_style = {'size': 12}
        
        if out :
            return fig,ax

# ----------------------------------------------
#%%                Main
# ----------------------------------------------

if __name__ == '__main__' :
    ID = 202202270005
    AR = AtmosphericRiver(ID)
    AR.get_mask(out=False)
# %%
