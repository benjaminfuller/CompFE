import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import csv
import sys



def tar_ent_process(filename):
    tar = []
    ent = []
    alpha = []
    subset_dict = {}
    alpha_dict = {}
    with open(filename, newline='') as csvfile:
        tar_rates = csv.reader(csvfile, delimiter='\t', quotechar='|')
        next(tar_rates)
        for row in tar_rates:
            if len(row)>3:
                subset_size = int(row[0])
                alpha = float(row[1])
                ent.append(float(row[2]))
                tar.append(float(row[3]))
                # if subset_size in subset_dict:
                #     ent, tar = subset_dict[subset_size]
                # else:
                #     ent=[]
                #     tar=[]
                #     subset_dict[subset_size]=(ent,tar)
                # if float(row[2])!=0:
                #     ent.append(float(row[2]))
                #     tar.append(float(row[3]))
                #     if alpha in alpha_dict:
                #         ent, tar = alpha_dict[alpha]
                #     else:
                #         ent=[]
                #         tar=[]
                #         alpha_dict[alpha]=(ent,tar)
                #     ent.append(float(row[2]))
                #     tar.append(float(row[3]))
                #     print(ent)
    return (ent, tar)
                               
#for key in subset_dict:
#    ent, tar = subset_dict[key]
#    plt.scatter(ent, tar, alpha=0.5, label="Subset Size = "+str(key))


(ent_hetero, tar_hetero) = tar_ent_process("ent_tar.txt")
(ent_hetero_u, tar_hetero_u) = tar_ent_process("ent_tar_uniform.txt")
(ent_ang, tar_ang) = tar_ent_process("ent_tar_angular.txt")
(ent_ang_u, tar_ang_u) = tar_ent_process("ent_tar_angular_uniform.txt")

plt.scatter(ent_hetero, tar_hetero, alpha=0.5, label="Heterogeneous Feature Extractor, Zeta")
plt.scatter(ent_ang, tar_ang, alpha=0.4, label="Angular Feature Extractor, Zeta")
plt.scatter(ent_hetero_u, tar_hetero_u, alpha=0.8, label="Heterogeneous Feature Extractor, Uniform")
plt.scatter(ent_ang_u, tar_ang_u, alpha=0.8, label="Angular Feature Extractor, Uniform")
#plt.scatter(ent_all_new, tar_all_new, alpha=0.5, label="New")
#    else:
#        plt.scatter(ent, tar, alpha=0.5, label="New")
            
plt.xlabel("Minimum of Entropy of across 10 subsets")
plt.legend()
plt.ylabel("True Accept Rate")
plt.title("Entropy and TAR for different mechanisms")
plt.show()
