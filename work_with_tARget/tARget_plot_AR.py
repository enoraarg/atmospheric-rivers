#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28  2024

@author: elegall

Module to plot maps related to atmospheric rivers 
"""
# ----------------------------------------------
#                Imports
# ----------------------------------------------
import xarray as xr
import numpy as np
from   datetime import datetime
#import glob
import os

import cartopy.crs         as ccrs
from   cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from cartopy import feature as cft
import matplotlib.pyplot   as plt
from   matplotlib.patches  import Patch
from   matplotlib.colors   import Normalize
#import seaborn             as sns

from sys import path
path.append('/home/elegall/AR/scripts')
from config import *
import config as cf
from transects.tARget_get_transect import Transect
from class_AR import AtmosphericRiver
#import axes.get_axes as gaxes
path.append('/home/elegall/routines')
from routine_figure import *

lat,lon = 0,1 # indexing

# ----------------------------------------------
#%%                Auxilliary for maps
# ----------------------------------------------

def plot_ARs(date,mode='all',**kwargs) :
    if kwargs.get('contour_AR',True) :
        # ,flag_to_180=AR.data_to_180
        mask_AR = kwargs.get('mask_AR',None)
        if type(mask_AR) == type(None) :
            AR = AtmosphericRiver(kwargs.get('ID',None))
            mask_AR = AR.get_mask(out=True,delayed=False)
            #AR.get_latlon_for_plot(out=False)
            # get mask
            # get timestep
            # to_180

        mask_AR = cf.to_180_ds(mask_AR,flag_to_180=flag_to_180)
        lons = sorted(list(set(lonslice) & set(mask_AR.longitude.values)))
        lats = sorted(list(set(latslice) & set(mask_AR.latitude.values)))
        mask_AR = mask_AR.sel(longitude=lons,latitude=lats)
        mask_AR.plot.contour(ax=ax,transform=crs_0,
                                    zorder=20,
                                    linewidths=1,
                                    colors='white')
    else : 
        da_kidmap = kwargs.get('da_kidmap',None)
        if type(da_kidmap) == type(None) :
            print('eh oh tu me le files ton jeu de données ?')

        da_kidmap = da_kidmap.sel(lat=latslice,
                        lon=lonslice,
                        time=kwargs.get('date',None))
        
        # kwargs latslice lonslice date
        randid = da_kidmap%max_ID # add more ? ici c'est modulo l'ID (qui va de 00 à 09) au moins c rapide
        plot = randid.plot(transform = crs_0,
                            cmap = cmap_ID,
                            norm = norm_ID,  
                            add_colorbar = False,alpha=0.6,
                            zorder=5)

def plot_background(date,background='tcwv',ds_ivt=None,ds_tcwv=None,**kwargs) :
    if background == 'tcwv' : 
        if type(ds_tcwv) == type(None) :
            ds_tcwv = cf.open_timeslice_ERA5(date,'tcwv',longitude=lonslice,latitude=latslice,
                                         **cf.ERA5_variables['tcwv'])

        ds_tcwv = cf.to_180_ds(ds_tcwv,flag_to_180=flag_to_180)

        if kwargs.get('contour_tcwv', False) :
            ds_tcwv.tcwv.plot.contour(ax=ax,transform=crs_0,
    							 levels=[20,48],
                                 colors=['orange','red'],linestyles='-')
            handles = [Patch(facecolor='orange',label='20$kg.m^{-2}$'),
            		   Patch(facecolor='red',   label='50$kg.m^{-2}$')]
            ax.legend(handles=handles,loc='upper right')

        ds_tcwv.tcwv.plot(ax=ax,
            transform = crs_0,
                        norm = cf.norm_tcwv,
                        cmap = 'coolwarm',
                        cbar_ax=cax,
                        cbar_kwargs = dict(shrink=0.5,
                                        extend='max'))
        #contour = ds_tcwv.tcwv.plot.contour(ax=ax,transform=crs_0,
    	#									levels=[48],
		#									colors='darkorchid')
        cbar = ax.collections[0].colorbar
        cbar.set_ticks([0,20,50])
        cbar.ax.tick_params(labelsize=9) 
        cbar.set_label(f'tcwv\n({ds_tcwv.tcwv.units})',size=9)

    elif background == 'ivt' :
        if type(ds_ivt) == type(None) : 
            ds_ivt = cf.open_timeslice_ERA5(date,'ivt',longitude=lonslice,latitude=latslice,
                                        #flag_to_180=flag_to_180,
                                        **cf.ERA5_variables['ivt'])
            
        ds_ivt = cf.to_180_ds(ds_ivt,flag_to_180=flag_to_180)

        ds_ivt.ivt.plot(transform = crs_0,
                        norm = norm_ivt,
                        cmap = 'coolwarm',
                        cbar_ax=cax,
                        cbar_kwargs = dict(shrink=0.5,
                                        extend='max'))
        
        cbar = ax.collections[0].colorbar
        cbar.set_ticks([0,250,500])
        cbar.ax.tick_params(labelsize=9) 
        cbar.set_label(f'ivt\n({ds_ivt.ivt.units})',size=9)
        
        if kwargs.get('contour_ivt',False) :
            contour = ds_ivt.ivt.plot.contour(ax=ax,transform=crs_0,
    													  levels=[250],
													      colors='darkorchid')
            cbar.add_lines(contour)

def plot_surface_wind(date,**kwargs) :
    if kwargs.get('surface_wind',True) :
        # Coarsen wind data, especially for a large domain
        step = 5
        if len(lonslice) >= 60*4 : # 60° longitude
            step *= 2

        # -- Open wind dataset if not already opened
        ds_wind = kwargs.get('ds_wind',None)
        if type(ds_wind) == type(None) :
            ufile = cf.open_timeslice_ERA5(date,'u10',**cf.ERA5_variables['u10'],
                                            longitude=lonslice,latitude=latslice) #glob.glob(path_ERA5_025+f'hourly/AN_SF/{year}/u10.{year}{month}.*.nc')[0]
            vfile = cf.open_timeslice_ERA5(date,'v10',**cf.ERA5_variables['v10'],
                                            longitude=lonslice,latitude=latslice)#glob.glob(path_ERA5_025+f'hourly/AN_SF/{year}/v10.{year}{month}.*.nc')[0]
            ds_wind = xr.merge([ufile,vfile])

        # -- Switch longitude system
        ds_wind = cf.to_180_ds(ds_wind,flag_to_180=flag_to_180)

        # -- Plot wind
        quiver = ds_wind.sel(latitude=ds_wind.latitude[::step],
                    longitude=ds_wind.longitude[::step]).plot.quiver(ax=ax,
                                            transform=crs_0,
                                            x="longitude",
                                            y="latitude",
                                            u="u10",
                                            v="v10",
                                            color='dimgrey',
                                            headaxislength=1,headlength=2,
                                            add_guide=False)

        cax.quiverkey(quiver,left+h_pad,bottom2,5,r'$5m.s^{-1}$',labelpos='E',coordinates='axes',
                        fontproperties={'size':10},zorder=18)

def plot_geopt(date,**kwargs) :
    if kwargs.get('contour_geopt',True) :
        level = 850
        # NOTE todo :
        # add legend 
        # choose level

        ds_geopt = kwargs.get('ds_geopt',None)
        if type(ds_geopt) == type(None) :
            #print('Geopotential required but no dataset was provided. Opening')
            ds_geopt = cf.open_timeslice_ERA5(date,'geopt',**cf.ERA5_variables['geopt'],
                                                longitude=lonslice,latitude=latslice)

        ds_geopt = cf.to_180_ds(ds_geopt,flag_to_180=flag_to_180)

        contour = ds_geopt.geopt.sel(#latitude=latslice,
        	        #longitude=lonslice,
                    level=level).plot.contour(ax=ax,transform=crs_0,linewidths=0.8,
                                            colors='k',zorder=4)
        # ajouter un locator pour les contours,
        # ex locator=plt.LogLocator()
        # je peux récupérer la légende correspondante avec contour.legend_elements() 
        # 
        ax.clabel(contour, contour.levels,inline=1, fmt=fmt,fontsize=5,zorder=4)

def plot_ascendance(date,**kwargs) :
    if kwargs.get('ascendance',True) :
        lowlev    = slice(850,950)
        midlev    = slice(500,500)
        lev_w = kwargs.get('lev_w','low')
        lev_slice = lowlev if lev_w == 'low' else midlev
        quantile  = 0.2
        # quantile par rapport à ? toute la carte ? mmmmh 
        # ou alors prendre un seul absolu ....???????

        omega = kwargs.get('omega',None)
        if type(omega) == type(None) :
            omega = cf.open_timeslice_ERA5(date,'w',latitude=latslice,longitude=lonslice,
                            **cf.ERA5_variables['w'])
        omega = cf.to_180_ds(omega,flag_to_180=flag_to_180)

        omega = omega.w.sel(level=lev_slice).mean(dim='level')
        ascendance = omega.where(omega < 0)
        forte_ascendance = ascendance.where(ascendance < ascendance.quantile(quantile))

        with plt.rc_context({'hatch.color': 'cyan'}) : # couleur des points
            forte_ascendance.plot.contourf(ax=ax,transform=crs_0,
                                        colors="none", # pour ne pas avoir de couleur de fond

                                        hatches=['......'], # type de hatch. plus de `.` pour une densité plus élevée de points
                                        add_colorbar=False,
                                        zorder=15) # pour que ce soit affiché en dernier  

def plot_IMERG(date,**kwargs) :
    if kwargs.get('imerg',False) :
        thres = 0.1
        # quantile par rapport à ? toute la carte ? mmmmh 
        # ou alors prendre un seul absolu ....???????

        ds_imerg = kwargs.get('ds_imerg',None)
        if type(ds_imerg) == type(None) :
            ds_imerg = cf.open_timeslice_IMERG(date,latitude=latslice,longitude=lonslice).squeeze()

        ds_imerg = cf.to_180_ds(ds_imerg,flag_to_180=flag_to_180)
        ds_imerg = ds_imerg.where(ds_imerg.rain_rate > thres)

        plot = ds_imerg.rain_rate.plot(ax=ax,transform=crs_0,
                                    cmap = 'turbo',
                                    norm = Normalize(0.1,20),
                                    cbar_kwargs = dict(shrink=0.5,
                                        extend='max'),
                                    cbar_ax=cax2,
                                    zorder=17) # pour que ce soit affiché en dernier  

        #cbar = ax.collections[-1].colorbar
        cbar = plot.colorbar
        cbar.set_ticks([0,10,20])
        cbar.ax.tick_params(labelsize=9) 
        cbar.set_label(f'rain rate\n({ds_imerg.rain_rate.units})',size=9)
# ----------------------------------------------
#%%                Snapshots
# ----------------------------------------------

def plot_snapshot(date, 
            area = None, #cf.global_area, 
            latN=None,latS=None,
            lonW=None,lonE=None,
            divergence = False, lev_div = 'low',
            plot_transect = False,
            plot_edges = False,
            low_thetav = None, umax = None, vmax = None,
            test = False, save=True,
            **kwargs) :
    '''
    Function to plot a snapshot of atmospheric rivers
    
    Parameters :
    ----------
    date    : str. YYYY-MM-DDTHH. Date of the snapshot to be plotted
    ds_tcwv : xr.DataSet containing total column water vapor (TCWV) field
    ds_AR   : xr.DataSet containing atmospheric river information
    area    : object of class routine_basemap.area_of_studyc, delimiting the zone to plot
        Default to `global_area`
    projection : cartopy.crs (ccrs) object. Projection for the map
        Default to ccrs.PlateCarree()
    background_tcwv : bool. Whether to plot TCWV as a background
        Default to `True`
    contour : bool. Whether to add contours of TCWV
        Default to `False`
    surface_wind : bool. Whether to add wind arrows
        Default to `True`
    test : bool. Whether the plot is a test.
        Default to `False`
    save : bool. Whether to save the plot.
        Default to `True`

    Plot
    -------
    Plot a snapshot of AR
    '''
    # ----------------------------------------
    # -- Select area of interest
    # ----------------------------------------
    global lonslice,latslice,crs_0,flag_to_180
    global cax,ax,left,h_pad,bottom,bottom2
    global ID
    ID = kwargs.get('ID',None)

    # -- Longitudes : 
    flag_to_180=kwargs.get('flag_to_180',False)
    if type(lonW) == type(None) and type(lonslice) == type(None):
        #print("lonW not given ; Assuming that lonE is also not given but that an area is given")
        lonW = 0 ; lonE = 360-0.25 #area.lonmin ; lonE = area.lonmax
    flag_to_180 = True if lonW%360 >= lonE%360 else False

    # -- Whether to center the plot on the Pacific or on the Atlantic
    center_at_180 = True if ((lonW%360 <= 180) and (lonE%360 >= 180)) else False
    print('center plot at 180 ? ', center_at_180)

    # -- Switch to [-180,180] for the coordinate longitude
    # which enables to plot the map without discontinuity at 0°E
    # Flag to know whether this translation should be applied to all datasets : 
    print('switch data to [-180,180] ? ', flag_to_180)
    lonW = cf.to_180(lonW,flag_to_180=flag_to_180) ; lonE = cf.to_180(lonE,flag_to_180=flag_to_180)

    latslice,lonslice = kwargs.get('latslice',None), kwargs.get('lonslice',None)
    if type(latslice) == type(None) :
        hor_res = 0.25
        latslice = np.arange(latN,latS-hor_res,-hor_res)
        lonslice = np.arange(lonW,lonE +((-1)**flag_to_180)*hor_res,((-1)**flag_to_180)*hor_res)

    # Coordinate system to use to create the ax :
    #crs_ax = ccrs.PlateCarree(central_longitude=180*center_at_180)
    crs_ax = ccrs.Orthographic(central_longitude=lonslice.mean(), #ATTENTION AU -180
                               central_latitude=latslice.mean()) # ou abs().min() ?
    # Coordinate system to use at any other time
    # (yes, even when the plot is centered on 180°E !)  (a so-called "vanilla PlateCarree")
    crs_0 = ccrs.PlateCarree(central_longitude=0) # (= default central longitude)

    lonslice = lonslice % 360 # In order to easily preselect data when opening files
    ratio = len(latslice)/len(lonslice)

    # ------------------------------------------------
    print('computing image for date',date)
    # ------------------------------------------------
    # -- Initiate figure
    if ratio < 1 :
        fig  = plt.figure(figsize = (8,8*ratio))
    else :
        fig  = plt.figure(figsize = (8/ratio,8))

    ax = plt.axes(projection=crs_ax)

    # -- Add axis for colorbar
    h_pad  = 0.02
    v_pad  = 0.05
    bottom = 0
    left   = 1 + h_pad
    width  = 0.01
    height = 0.4
    cax = ax.inset_axes([left, bottom, width, height])
    position = cax.get_position()
    bottom3 = 1-height

    if kwargs.get('imerg',True) :
        global cax2
        cax2 = ax.inset_axes([left, bottom3, width, height])
        position = cax2.get_position()

    bottom2 = 0.45

    # ----------------
    # -- Background
    plot_background(date,**kwargs)   

    # ----------------     
    # -- Plot ARs
    plot_ARs(date,**kwargs)

    # ----------------
    # -- Wind
    plot_surface_wind(date,**kwargs)

    # ----------------
    # -- Geopotential
    plot_geopt(date,**kwargs)

    # ----------------
    # -- Horizontal divergence 
    if divergence :
        lowlev = slice(850,1000) # hPa = divergence de basse couche
        midlev = slice(400,600) # c'est beaucoup peut-être - cf transects ? 
        lev_slice = lowlev if lev_div == 'low' else midlev

        div = cf.open_timeslice_ERA5(date,'d',level='AN_PL',resolution ='4xdaily')

        div = to_180_ds(div)
        div = div.sel(latitude = latslice,
                      longitude = lonslice,
                      level = lev_slice)
        div = div.d.mean(dim='level')
        
        quantile = 0.5
        divergence = div.where(div > 0)
        forte_divergence = divergence.where(divergence > divergence.quantile(quantile))
        convergence = div.where(div < 0)
        forte_convergence = convergence.where(convergence < convergence.quantile(quantile))

        # hatch ? ou contour ? 
        # ou alors contour + hatch lorsque "significatif"
        # (par rapport à ? moyenne de la carte à ce pas de temps +- écart type ? )
        # on verra si c'est trop moche !
        with plt.rc_context({'hatch.color': 'magenta'}) :
            forte_divergence.plot.contourf(ax=ax,transform=crs_0,
                                    colors="none", # pour ne pas avoir de couleur de fond
                                    hatches=['////'], # type de hatch. plus de `.` pour une densité plus élevée de points
                                    add_colorbar=False,
                                    zorder=7)
            
        with plt.rc_context({'hatch.color': 'cyan'}) :
            forte_convergence.plot.contourf(ax=ax,transform=crs_0,
                                    colors="none",
                                    hatches=["\\\\\\\\"],
                                    add_colorbar=False,
                                    zorder=8)

    # ----------------
    # -- Ascendance :
    plot_ascendance(date,**kwargs)


    plot_IMERG(date,**kwargs)
    # ----------------
    # -- Transect :
    if (ID != None) and (plot_transect == True) :
        if type(kwargs.get('transect',None)) == type(None) :
            A = kwargs.get('A',None)

            transect = Transect(ID,date,A)
            transect.get_transect_info()
        else :
            transect = kwargs.get('transect',None)

        anchor = transect.anchor
        ends = transect.start,transect.end

        ax.plot(to_180(anchor[lon]),anchor[lat],color='orange',marker='+',
            transform=crs_0,
            zorder=30)
        ax.plot(to_180(np.array(ends).T[lon]),np.array(ends).T[lat],
            color='orange',marker='+',
            transform=crs_0,
            zorder=30)
        
        if kwargs.get('legend_transect',True) : 
            # Indiquer le texte = extrémités de transect
            # dans l'hémisp
            offset = 1 * (-1)**(anchor[0] < 0) # in unit degrees ; negative if southern hemisphere
            ax.text(to_180(transect.start[lon] - offset), transect.start[lat] + offset,'A',
                    color = 'orange',
                    transform = crs_0,
                    zorder=20)
            ax.text(to_180(transect.end[lon]   + offset), transect.end[lat]   - offset ,'B',
                    color = 'orange',
                    transform = crs_0,
                    zorder=20)
        
    if type(kwargs.get('transect2',None)) != type(None) :
        transect2 = kwargs.get('transect2',None) 
        anchor = transect2.anchor #.get_anchor_of_transect2(ID,A,date)
        ends = transect2.start,transect2.end #ends_of_transect2(ID,A,date,len_transect2=5)

        ax.plot(to_180(anchor[lon]),anchor[lat],color='orange',marker='+',
            transform=crs_0,
            zorder=30)
        ax.plot(to_180(np.array(ends).T[lon]),np.array(ends).T[lat],
            color='orange',marker='+',
            transform=crs_0,
            zorder=30)
        
        if kwargs.get('legend_transect',True) :
            # Indiquer le texte = extrémités de transect
            # dans l'hémisp
            offset = 1 * (-1)**(anchor[0] < 0) # in unit degrees ; negative if southern hemisphere
            ax.text(to_180(transect2.start[lon] - offset), transect2.start[lat] + offset,'C',
                    color = 'orange',
                    transform = crs_0,
                    zorder=20)
            ax.text(to_180(transect2.end[lon]   + offset), transect2.end[lat]   - offset ,'D',
                    color = 'orange',
                    transform = crs_0,
                    zorder=20)
            
    if type(kwargs.get('transect3',None)) != type(None) :
        transect3 = kwargs.get('transect3',None) 
        anchor = transect3.anchor #.get_anchor_of_transect3(ID,A,date)
        ends = transect3.start,transect3.end #ends_of_transect3(ID,A,date,len_transect3=5)

        ax.plot(to_180(anchor[lon]),anchor[lat],color='orange',marker='+',
            transform=crs_0,
            zorder=30)
        ax.plot(to_180(np.array(ends).T[lon]),np.array(ends).T[lat],
            color='orange',marker='+',
            transform=crs_0,
            zorder=30)
        
        if kwargs.get('legend_transect',True) :
            # Indiquer le texte = extrémités de transect
            # dans l'hémisp
            offset = 1 * (-1)**(anchor[0] < 0) # in unit degrees ; negative if southern hemisphere
            ax.text(to_180(transect3.start[lon] - offset), transect3.start[lat] + offset,'C',
                    color = 'orange',
                    transform = crs_0,
                    zorder=20)
            ax.text(to_180(transect3.end[lon]   + offset), transect3.end[lat]   - offset ,'D',
                    color = 'orange',
                    transform = crs_0,
                    zorder=20)

    # ----------------
    # -- Edges :
    if (ID != None) and (plot_edges == True) : 
        # if type(mask_AR) == type(None) :
        #     ID = 202202270005
        #     AR = AtmosphericRiver(ID)
        #     mask_AR = AR.get_mask_AR().sel(time=date)
        # if 'time' in mask_AR.dims : 
        #     mask_AR = mask_AR.sel(time=date)
        AR = kwargs.get('AR',None)
        if type(AR) == type(None) : 
            AR = AtmosphericRiver(ID)
            AR.get_mask(out=False)
            AR.get_latlon_for_plot(out=False)
        if type(low_thetav) == type(None) :
            low_thetav = AR.get_thetav(timeslice=date)
        elif 'time' in low_thetav.dims :
            low_thetav = low_thetav.sel(time=date)

        # if type(umax) == type(None) : 
        #     umax,vmax = get_uv_at_maxflux(ID,timeslice=date)
        # elif 'time' in umax.dims :
        #     umax = umax.sel(time=date)
        #     vmax = vmax.sel(time=date)
        #if type(ivt) == type(None) : 
        ivt = AR.get_ivt(timeslice=date,vector=True)
        ivt = [ivt[0].values,ivt[1].values]

        if True :
            # edge_flux   = gaxes.find_edge_at_timestep(ID,[umax,vmax],
            #                             mask_AR=mask_AR,
            #                             show=False,
            #                             compute_grad=False,**edge_detection_params['qflux'])
            #IVT_u = xr.open_dataset(glob.glob('/data/elegall/AR/IPART/uflux_globe_2022.nc')[0])
            #IVT_v = xr.open_dataset(glob.glob('/data/elegall/AR/IPART/vflux_globe_2022.nc')[0])
            #np_ivt = [IVT_u.uflux.sel(latitude=mask_AR.latitude,longitude=mask_AR.longitude,
            #             time=mask_AR.time).values,
            #       IVT_v.vflux.sel(latitude=mask_AR.latitude,longitude=mask_AR.longitude,
            #             time=mask_AR.time).values]
            
            #params = {**gaxes.edge_detection_params['ivt']}
            # edge_ivt = gaxes.find_edge_at_timestep(AR,params,
            #                                        ivt,
            #                                        date,edge_data='IVT')

            edge_ivt = gaxes.get_axis(AR,date,np_data=ivt,edge_data='ivt')
            # edge_thetav = gaxes.find_edge_at_timestep(ID,low_thetav,
            #                                 show=False,
            #                             **edge_detection_params['low_thetav'])
            # params={**gaxes.edge_detection_params['lowthetav']}
            # edge_thetav = gaxes.find_edge_at_timestep(AR,params,
            #                                           low_thetav.values,
            #                                           date,
            #                                           edge_data='lowthetav')
            edge_thetav = gaxes.get_axis(AR,date,np_data=low_thetav,edge_data='low_thetav')

            color_interp = ['orangered','blue'] # Attention, il va y avoir conflit de couleurs
            for iedge,edge in enumerate([edge_ivt,edge_thetav]) :
                ax.scatter(to_180(edge.border_lon),edge.border_lat,
                        transform = crs_0,
                        lw = 3,
                        marker = '+',
                        s=0.5,
                        color=color_interp[iedge],zorder=30)
        else :
            print('Most likely no edge could be detected at this timestep.\nor something went wrong (:')

    # -----------------------------------------
    # -- Shape map
    # -----------------------------------------
    ax.coastlines(linewidth=0.5)
    ax.add_feature(cft.LAND,alpha=0.5,zorder=18)

    gl = ax.gridlines(crs=crs_0, linewidth=1, color='black', alpha=0.4, linestyle=':', draw_labels=True)
    gl.top_labels   = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 12}
    gl.ylabel_style = {'size': 12}

    # -----------------------------------------
    # -- Shape plot
    # -----------------------------------------
    if type(date) == np.datetime64 :
        date = str(date)
    
    title = kwargs.get('title',' ')
    if len(title) <= 1 :  
        title = f'{date[:13]}'
        if type(ID) != type(None) :
            title += f" - {ID}"
    ax.set_title(title)

    fig.align_ylabels()
    fig.tight_layout()

    # -- Pass figure to next instance, when it is required
    if kwargs.get('intermediate_plot',False) :
        return fig
    
    # -- Save
    if save :
        folder = kwargs.get('folder','snapshots/')
        os.system(f"mkdir -p {cf.path_results + folder}")
        loc = str(ID) if (ID != None) else area.shortname
        filename = 'snapshot.' + loc +'.'+date + '.png'
        fig.savefig(cf.path_results + folder+filename)

    if not test :
        plt.close()

# ----------------------------------------------

#%%                Occurrences
# ----------------------------------------------

def plot_AR_object_occurrence(timerange,ds_AR,
            area = None,#cf.global_area, 
            projection = ccrs.PlateCarree(),
            test = False, save=True,
            **kwargs) :
    '''
    'Object' following Rutz?? 
    '''

    ds_AR = ds_AR.sel(lat=slice(area.latmax,area.latmin),
                   lon=slice(area.lonmin,area.lonmax),
                   time=timerange)
    firstdate = np.datetime_as_string(ds_AR.time.isel(time=0))[:np.datetime_as_string(ds_AR.time.isel(time=0)).find(':')]
    lastdate  = np.datetime_as_string(ds_AR.time.isel(time=-1))[:np.datetime_as_string(ds_AR.time.isel(time=-1)).find(':')]
    
    print('computing AR occurrence bewteen dates',firstdate,'and',lastdate)
    
    fig  = plt.figure(figsize = (8,8*area.ratio)) 
    ax   = plt.axes(projection=projection)




    (ds_AR.kidmap/ds_AR.kidmap).sum(dim='time').plot(cmap = 'gist_earth_r',
                                                     cbar_kwargs = {'shrink':0.7,label:'Occurrences\n(# of timesteps)'})

    # Shape :
    ax.coastlines()
    gl = ax.gridlines(crs=projection, linewidth=1, color='black', alpha=0.4, linestyle=':', draw_labels=True)
    gl.top_labels   = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 13}
    gl.ylabel_style = {'size': 13}

    # Ajouter les rectangles
    
    # Title
    firstdatetitle = datetime.strptime(firstdate[:10],'%Y-%m-%d').strftime('%d/%m/%Y')
    lastdatetitle  = datetime.strptime(lastdate[:10],'%Y-%m-%d').strftime('%d/%m/%Y')
    title = f'ARs tracked by tARget, using ERA5\n{firstdatetitle} - {lastdatetitle}'
    ax.set_title(title)
    #shapefig(fig,None)
    fig.align_ylabels()
    #fig.tight_layout()
    
    if save :
        folder = kwargs.get('folder','')
        filename = 'occurence.' + area.shortname +'.'+ firstdate +'.'+ lastdate + '.png'
        savefig(fig, filename, outpath = path_results + folder,**kwargs)

    if not test :
        plt.close()


# ----------------------------------------------
#%%                Animations
# ----------------------------------------------
# cf ipynb

# ----------------------------------------------
#%%                Main
# ----------------------------------------------

if __name__ == '__main__' :
    test = False
    timerange = slice(1994,2023)
    ds = xr.open_mfdataset(path_tARget_db + 'globalARcatalog_ERA5_1940-2023_v4.0.nc')
    plot_AR_object_occurrence(timerange,ds,test=test,draft=True)
