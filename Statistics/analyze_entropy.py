import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
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
with open("entropyinventory.pkl","rb") as file_handle:
    list_of_ent = pickle.load(file_handle)
    print(len(list_of_ent))


n, bins, patches = plt.hist(list_of_ent, bins=20, color="Blue",alpha=0.5)



print(np.quantile(list_of_ent, [0,0.25,0.5,0.75,1]))
print(np.mean(list_of_ent))
print(average_min_entropy(list_of_ent[:10]))
print(average_min_entropy(list_of_ent[:100]))
print(average_min_entropy(list_of_ent[:1000]))
print(average_min_entropy(list_of_ent[:10000]))
print(average_min_entropy(list_of_ent[:100000]))
print(average_min_entropy(list_of_ent))

list_of_ent.sort()
print("Sorted statistics")
print(average_min_entropy(list_of_ent[100000:]))
exit(1)

plt.xlabel("Entropy of Subset")
plt.ylabel("Frequency")
plt.title("Histogram of Subset Entropy for alpha=10 and Subset Size=95")
plt.show()
    
    
