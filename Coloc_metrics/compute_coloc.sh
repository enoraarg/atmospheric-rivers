#!/bin/bash

#SBATCH -o logs/run_%x_A%A_%a.o
#SBATCH -e logs/run_%x_A%A_%a.e
# %x : nom du fichier soumis en sbatch (=ce fichier)
# %j ? job ID incrémenté de task ID (=effective job ID ?)
# %A : job ID (soumission)
# %a : task ID
#SBATCH --partition zen4
#SBATCH --ntasks 2
##SBATCH --cpus-per-task=1
#SBATCH --mem 30g
#SBATCH --time 00:10:00
#SBATCH --array=1-12 # = les 12 mois d'une année

program=coloc_syst.py
path_to_program=/home/elegall/AR/scripts/Coloc_metrics
echo program = $program

month=$SLURM_ARRAY_TASK_ID 
#= à chaque sous-exécution, la tache a un identifiant différent, donné par les arguments de --array
year=2011
basin=NA
thresmode=abs
thres=10
variable=rain_rate
spec=coast
value=area

echo year = $year
echo month = $month
echo basin = $basin
echo variable = $variable
echo spec = $spec
echo thresmode = $thresmode
echo thres = $thres
echo value = $value

#conda init
module purge
module load pangeo-meso/2026.01.21
python $path_to_program/$program --year $year --basin $basin --month $month --delta 31 --thres $thres --thresmode $thresmode --spec $spec --variable $variable --value $value
