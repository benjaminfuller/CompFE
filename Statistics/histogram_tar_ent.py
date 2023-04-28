import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import csv

subset_size=[]
tar=[]
ent=[]
alpha=[]

with open('ent_tar.txt', newline='') as csvfile:
    tar_rates = csv.reader(csvfile, delimiter='\t', quotechar='|')
    next(tar_rates)
    for row in tar_rates:
        if len(row)>3:
            subset_size.append(int(row[0]))
            alpha.append(int(row[1]))
            ent.append(float(row[2]))
            tar.append(float(row[3]))
                               

plt.scatter(ent, tar, alpha=0.5)
plt.xlabel("Minimum of Entropy of across 10 subsets")
plt.ylabel("True Accept Rate")
plt.title("Entropy and TAR across subset sizes and alpha parameters")
plt.show()
