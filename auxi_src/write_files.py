#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author : elegall

This module contains functions and variables to open properly ERA5 and IMERG files.
"""

# ----------------------------------------------
#         Check files
# ----------------------------------------------
import sys
import glob
import xarray as xr

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


# write

# merge