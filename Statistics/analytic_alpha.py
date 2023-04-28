import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import csv
from math import pow

p_same=[]
k_list =[1,2,3,4,5,60,65,70,75,80,85,90,95,100]

with open('../PythonImpl/dense_0.205_57-75.txt', newline='') as csvfile:
    confidence_info = csv.reader(csvfile, delimiter=' ', quotechar='|')
    
    for row in confidence_info:
        if len(row)>7:
            p_same.append(1-float(row[6]))

for k in k_list:
#    print(k)
#    print(p_same)
#    exit(1)
    best_alpha=0
    expected_subsets=0
    for alpha in range(5):
        gamma_denom=0
        sum_p_alpha1= 0
        sum_p_2alpha1=0
        sum_p_alpha=0
        e_m=0
        for p_i in p_same:
            sum_p_alpha1+= pow(p_i, alpha+1)
            sum_p_2alpha1+=pow(p_i, 2*alpha+1)
            sum_p_alpha +=pow(p_i, alpha)
        gamma = sum_p_alpha1/(sum_p_2alpha1*sum_p_2alpha1)
        e_m=sum_p_alpha1/sum_p_alpha
        expected_subsets=8/(pow(e_m,k))
        if gamma < 1/(18*k*k):
            best_alpha=alpha
        else:
            break
    print("For subsets of size "+str(k)+" analytic alpha is "+str(best_alpha)+" expected subsets "+str(expected_subsets))
    print("Probability of failure "+str(9*k*k*gamma))





