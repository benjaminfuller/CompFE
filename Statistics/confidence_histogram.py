import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import csv

p_same=[]
p_diff=[]
with open('../PythonImpl/dense_0.205_57-75.txt', newline='') as csvfile:
    confidence_info = csv.reader(csvfile, delimiter=' ', quotechar='|')
    
    for row in confidence_info:
        if len(row)>7:
            p_same.append(float(row[6]))
            p_diff.append(float(row[7]))

#print(p_same)
#bins=[.05,.075,.1,.125,.15,.175,.2,.225.25,.30,.35,.4,.45,.5,.55,.60]
n, bins, patches = plt.hist([p_same,p_diff], bins=20, color=["Blue","Red"],alpha=0.5)
plt.xlabel("Error Rate")
plt.ylabel("Frequency")
plt.title("Histogram of Error Rates of Individual Features")
plt.legend(["Same Biometric", "Different Biometrics"])
plt.show()

