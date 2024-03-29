import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import csv

tar=[]
ent=[]
alpha=[]
subset_dict={}
alpha_dict={}
ent_levels=[30, 35,40,45,50,55,60,65,70,75]
tar_levels=[.1,.2,.3,.4,.5,.6,.7,.8,.9]
ent_best_params_dict={}
tar_best_params_dict={}

for ent in ent_levels:
    ent_best_params_dict[ent] = (0,0,0)
for tar in tar_levels:
    tar_best_params_dict[tar] = (0,0,0)
   

with open('ent_tar_new.txt', newline='') as csvfile:
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
                    
                               
print(ent_best_params_dict)

print(tar_best_params_dict)
