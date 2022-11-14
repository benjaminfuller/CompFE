import csv
from statistics import mean, median
import numpy as np
import math
import matplotlib.pyplot as plt

def binary_entropy(val):
    return -(val) * math.log2(val) - (1 - val) * (math.log2(1-val))

## 70 size subset ##
entropys = []
exp = []
cum_avg_min_ent = []
mins70 = []
medians70 = []
means70 = []
with open("70.txt","r") as f:
    lines = f.readlines()
    for line in lines:
        line = line.split()
        if line[0] == "Entropy" and line[1] == "Run":
            degrees_freedom = float(line[5])
            reported_mean = float(line[10])
            print(degrees_freedom, reported_mean, binary_entropy(reported_mean))
            entropys.append(degrees_freedom * binary_entropy(reported_mean))
            exp.append(2 ** (-1 * entropys[-1]))
            exp_avg = np.mean(exp)
            mins70.append(min(entropys))
            medians70.append(median(entropys))
            means70.append(mean(entropys))
            logavg = -1 * math.log2(exp_avg)
            cum_avg_min_ent.append(logavg)
    f.close()
entropy70 = entropys
cum_ent_70 = cum_avg_min_ent


## 95 size subset ##
entropys = []
exp = []
cum_avg_min_ent = []
mins95 = []
medians95 = []
means95 = []
with open("95.txt","r") as f:
    lines = f.readlines()
    for line in lines:
        line = line.split()
        if line[0] == "Entropy" and line[1] == "Run":
            degrees_freedom = float(line[5])
            reported_mean = float(line[10])
            entropys.append(degrees_freedom * binary_entropy(reported_mean))
            exp.append(2 ** (-1 * entropys[-1]))
            exp_avg = np.mean(exp)
            mins95.append(min(entropys))
            medians95.append(median(entropys))
            means95.append(mean(entropys))
            logavg = -1 * math.log2(exp_avg)
            cum_avg_min_ent.append(logavg)
    f.close()
entropy95 = entropys
cum_ent_95 = cum_avg_min_ent

x_vals70 = range(len(entropy70))
x_vals95 = range(len(entropy95))

plt.plot(x_vals70, cum_ent_70)
plt.plot(x_vals70, mins70)
plt.plot(x_vals70, means70)
plt.plot(x_vals70, medians70)
plt.plot(x_vals95, cum_ent_95, '-')
plt.plot(x_vals95, means95, '-')
plt.plot(x_vals95, mins95, '-')
plt.plot(x_vals95, medians95, '-')
plt.semilogx()
plt.show()
print(max(entropy95),max(entropy70))

print("Average Entropy for 95:",cum_ent_95[-1],"with ", len(entropy95), "runs.\nAverage Entropy for 70:", cum_ent_70[-1], "with ", len(entropy70), "runs.")