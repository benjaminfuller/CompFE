import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import csv
from math import pow

p_same=[]
k_list =[60,65,70,75,80,85,90,95,100]

with open('../PythonImpl/dense_0.205_57-75.txt', newline='') as csvfile:
    confidence_info = csv.reader(csvfile, delimiter=' ', quotechar='|')
    
    for row in confidence_info:
        if len(row)>7:
            p_same.append(1-float(row[6]))

for k in k_list:
    print(k)
#    print(p_same)
#    exit(1)
    best_alpha=0
    for alpha in range(5):
        gamma_denom=0
        sum_p_alpha1= 0
        sum_p_2alpha1=0
        for p_i in p_same:
            sum_p_alpha1+= pow(p_i, alpha+1)
            sum_p_2alpha1+=pow(p_i, 2*alpha+1)
        gamma = sum_p_alpha1/(sum_p_2alpha1*sum_p_2alpha1)
        if gamma < 1/(18*k*k):
            best_alpha=alpha
        else:
            break
    print("For subsets of size "+str(k)+" analytic alpha is "+str(best_alpha))





