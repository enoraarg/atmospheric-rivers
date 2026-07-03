#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np

path_job = '/home/elegall/AR/scripts/Coloc_metrics/'
program = 'compute_coloc.sh'
file =  open(path_job+program,'r') 
lines = file.readlines()
ilineyear = np.where([line.startswith('year') for line in lines])[0][0]

ilinebasin = np.where([line.startswith('basin') for line in lines])[0][0]
ilinespec  = np.where([line.startswith('spec') for line in lines])[0][0]
ilinevar  = np.where([line.startswith('variable') for line in lines])[0][0]
ilinethres  = np.where([line.startswith('thres=') for line in lines])[0][0]
ilinethresmode  = np.where([line.startswith('thresmode') for line in lines])[0][0]
ilinevalue  = np.where([line.startswith('value') for line in lines])[0][0]

thresmode='abs' #'quantile'
thres=10 #0.1
variable='rain_rate' #ivt
spec='coast'
value='area'

lines[ilinespec] = f"spec={spec}\n"
lines[ilinevar] = f"variable={variable}\n"
lines[ilinethres] = f"thres={thres}\n"
lines[ilinethresmode] = f"thresmode={thresmode}\n"
lines[ilinevalue] = f"value={value}\n"

delay=0
for basin in ['NA','NP','SA','SP','IO'] :
    lines[ilinebasin] = f"basin={basin}\n"
    #True :
    for newyear in range(2010,2023+1) :
        lines[ilineyear] = f"year='{str(newyear)}'\n"

        with open(path_job + program,'w') as writefile :
            writefile.writelines(lines)

        os.system(f"cd {path_job} ; sbatch --begin=now+{int(delay)}minutes {program}")
        delay+=10 #0.02