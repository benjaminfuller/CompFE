import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import sys
import csv
import pickle
import math

def average_min_entropy(list_of_ent):
    average_pred = 0
    for ent in list_of_ent:
        average_pred += 2**(-ent)
    average_pred/=len(list_of_ent)
    return -math.log2(average_pred)

list_of_ent=[]
filename=sys.argv[1]
with open(filename,"rb") as file_handle:
    for line in file_handle: 
        line = line.strip() #or some other preprocessing
        list_of_ent.append(float(line))
#    list_of_ent = pickle.load(file_handle)
    print(len(list_of_ent))


#n, bins, patches = plt.hist(list_of_ent, bins=20, color="Blue",alpha=0.5)



print(np.quantile(list_of_ent, [0,0.20,.4,0.5,0.6,.8,1]))
print("Mean of ent",np.mean(list_of_ent))
print("Avg min 10",average_min_entropy(list_of_ent[:10]))
print(average_min_entropy(list_of_ent[:100]))
print(average_min_entropy(list_of_ent[:1000]))
print(average_min_entropy(list_of_ent[:10000]))
print(average_min_entropy(list_of_ent[:100000]))
print("Overall avg min",average_min_entropy(list_of_ent))

list_of_ent.sort()
print("Sorted statistics")
print(average_min_entropy(list_of_ent[100000:]))
exit(1)

plt.xlabel("Entropy of Subset")
plt.ylabel("Frequency")
plt.title("Histogram of Subset Entropy for alpha=10 and Subset Size=95")
plt.show()
    
    
