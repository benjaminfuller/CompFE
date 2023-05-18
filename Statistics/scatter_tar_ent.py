import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import csv

tar=[]
ent=[]
alpha=[]
subset_dict={}
alpha_dict={}

with open('ent_tar.txt', newline='') as csvfile:
    tar_rates = csv.reader(csvfile, delimiter='\t', quotechar='|')
    next(tar_rates)
    for row in tar_rates:
        if len(row)>3:
            subset_size = int(row[0])
            alpha = int(row[1])
            if subset_size in subset_dict:
                ent, tar = subset_dict[subset_size]
            else:
                ent=[]
                tar=[]
                subset_dict[subset_size]=(ent,tar)
            ent.append(float(row[2]))
            tar.append(float(row[3]))
            if alpha in alpha_dict:
                ent, tar = alpha_dict[alpha]
            else:
                ent=[]
                tar=[]
                alpha_dict[alpha]=(ent,tar)
            ent.append(float(row[2]))
            tar.append(float(row[3]))
                               
#for key in subset_dict:
#    ent, tar = subset_dict[key]
#    plt.scatter(ent, tar, alpha=0.5, label="Subset Size = "+str(key))

for key in alpha_dict:
    if key in [0,10,20,30]:
        ent, tar = alpha_dict[key]
        plt.scatter(ent, tar, alpha=0.5, label="Alpha = "+str(key))
    
plt.xlabel("Minimum of Entropy of across 10 subsets")
plt.legend()
plt.ylabel("True Accept Rate")
plt.title("Entropy and TAR across subset sizes and alpha parameters")
plt.show()