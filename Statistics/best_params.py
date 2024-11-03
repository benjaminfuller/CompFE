import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import csv

tar=[]
ent=[]
alpha=[]
subset_dict={}
alpha_dict={}
ent_levels=[20, 25, 30, 35, 40, 42, 44, 46, 48, 50, 52, 54, 56]
tar_levels=[.05, .1,.15, .2,.3,.4,.5,.6,.7,.8,.9]
ent_best_params_dict={}
tar_best_params_dict={}

for ent in ent_levels:
    ent_best_params_dict[ent] = (0,0,0)
for tar in tar_levels:
    tar_best_params_dict[tar] = (0,0,0)
   

with open('ent_tar.txt', newline='') as csvfile:
    tar_rates = csv.reader(csvfile, delimiter='\t', quotechar='|')
    next(tar_rates)
    for row in tar_rates:
        if len(row)>3:
            subset_size = int(row[0])
            alpha = float(row[1])
            ent = float(row[2])
            tar = float(row[3])

            for entropy in ent_levels:
                if ent>= entropy:
                    best_tar, best_alpha, best_subset_size = ent_best_params_dict[entropy]
                    if tar > best_tar:
                        ent_best_params_dict[entropy] = (tar, alpha, subset_size)

            for tarate in tar_levels:
                if tar>=tarate:
                    best_ent, best_alpha, best_subset_size = tar_best_params_dict[tarate]
                    if ent> best_ent:
                        tar_best_params_dict[tarate] = (ent, alpha, subset_size)
                    
for ent_level in ent_best_params_dict:
    tar, alpha, subset = ent_best_params_dict[ent_level]
    if tar==0:
        continue
    if alpha>0:
        print("$\\ge $", ent_level,"&",subset,"&",alpha,"&",round(tar,2))
    else:
        print("$\\ge $", ent_level,"&",subset,"&",round(tar,2))

print()
for tar_level in tar_best_params_dict:
    ent, alpha, subset= tar_best_params_dict[tar_level]
    if ent==0:
        continue
    if alpha>0:
        print("$\\ge $", tar_level,"&",subset,"&",alpha,"&",round(ent,0))
    else:
        print("$\\ge $", tar_level,"&",subset,"&",round(ent,0))

