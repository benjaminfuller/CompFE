import math
import time
from joblib import Parallel, delayed
import os
import sys
import glob
import re
import random
from matplotlib import pyplot as plt
import numpy as np
import multiprocessing as mp
import pickle
#np.random.seed(1337) # for reproducibility`

################################################################################
#                      FUNCTION DEFINITIONS                                    #
################################################################################

def numericalSort(value):
    parts = numbers.split(value)
    parts[1::2] = map(int, parts[1::2])
    return parts

# Returns a numpy array of python arrays each chosen randomly with size number_samples
def sample_uniform(size, biometric_len, number_samples=1, confidence=None):
    pick_range = range(0, biometric_len - 1)
    randGen = random.SystemRandom()
    return np.array([randGen.sample(pick_range, size) for x in range(number_samples)])

def binary_entropy(val):
    return -(val) * math.log2(val) - (1 - val) * (math.log2(1-val))

def read_complex_conf(filepath):
        bad_list = [28, 200, 503, 754]
        with open(filepath, 'r') as f:
            confidence = []
            lines = f.readlines()
            for line in lines:
                numbers = line[42:].strip()
                numbers_list = numbers.split(' ')
                predictability = (1 - float(numbers_list[2]))
                entropy = float(numbers_list[3])
                pair = [predictability, entropy]
                # print(numbers_list, "numbers list")
                if int(numbers_list[0]) in bad_list:
                    confidence.append([0,0.000000000000001])
                else:
                    confidence.append(pair)
            return confidence, bad_list


def sample_sixia(size, biometric_len, number_samples, confidence, alpha_param):
    if confidence is None:
        print("Can't run Smart sampling without confidence, calling uniform")
        return sample_uniform(size, biometric_len, number_samples, confidence)

    sample_array = []
    new_confidence = [pair[0] ** alpha_param for pair in confidence]
    
    for set_selection_iter in range(number_samples):
        sample_indices = random.choices(range(len(new_confidence)), weights=new_confidence, k=size)
        dedup_indices = list(set(sample_indices))
        loop_count = 1
        while len(dedup_indices) < size:
            new_index = random.choices(range(len(new_confidence)), weights=new_confidence, k=1)
            sample_indices = dedup_indices
            sample_indices.extend(new_index)
            dedup_indices = []
            [dedup_indices.append(n) for n in sample_indices if n not in dedup_indices and n not in bad_list]
            loop_count = loop_count +1
            if loop_count == 1000000:
                print("Smart sampling failed to find a non-duplicating subset")
                exit(1)
        sample_array.append(dedup_indices)
    return np.array(sample_array)

def sample_sixia_with_entropy(size, biometric_len, number_samples, confidence, alpha_param):
    if confidence is None:
        print("Can't run Smart sampling without confidence, calling uniform")
        return sample_uniform(size, biometric_len, number_samples, confidence)

    sample_array = []
    new_confidence = [pair[0] ** (alpha_param / binary_entropy(pair[1])) for pair in confidence]

    for set_selection_iter in range(number_samples):
        sample_indices = random.choices(range(len(new_confidence)), weights=new_confidence, k=size)
        dedup_indices = list(set(sample_indices))
        loop_count = 1
        while len(dedup_indices) < size:
            new_index = random.choices(range(len(new_confidence)), weights=new_confidence, k=max(1,size - len(dedup_indices)))
            [dedup_indices.append(n) for n in new_index if n not in dedup_indices]
            loop_count = loop_count +1
            if loop_count == 1000000:
                print("Smart sampling failed to find a non-duplicating subset")
                exit(1)
        sample_array.append(dedup_indices)
    return np.array(sample_array)

################################################################################
#                    EXECUTION SCRIPT                                          #
################################################################################

# Command Line Usage:
# python3 GenerateSubsetsNewFE.py [subset size] ['simple' or 'complex'] [alpha] [number of subsets] [output file name]

size_or_threshold = int(sys.argv[1]) # Subset size
selection_method = sys.argv[2] # 'complex' or 'simple'
alpha_param = int(sys.argv[3]) # Confidence Weight Parameter
num_lockers = int(sys.argv[4]) # number of subsets sampled
outputfilename = sys.argv[5] + str(size_or_threshold) +  str(selection_method) + str(alpha_param) + str(num_lockers) #output file name
numbers = re.compile(r'(\d+)')
cwd = os.getcwd()
num_cpus = mp.cpu_count()
folder_list = sorted(glob.glob(cwd + "/CompFE/iris_right_all_dense_0.205_57-75_1024_folders/*"),key=numericalSort)
print (cwd)
print ("Folders: ",len(folder_list))
num_classes = range(len(folder_list))

print("Reading Confidence")
confidence, bad_list = read_complex_conf(cwd + "/CompFE/PythonImpl/AuxiliaryFiles/ConfidenceInfo.txt")

if selection_method == 'complex':
    print("Generating Subsets Using Complex Sixia Sampling")
    positions = sample_sixia_with_entropy(size_or_threshold,1024,num_lockers,confidence,alpha_param)     
elif selection_method == 'simple':
    print("Generating Subsets Using Simple Sixia Sampling")
    positions = sample_sixia(size_or_threshold,1024,num_lockers,confidence,alpha_param)

with open(outputfilename + ".pkl",'wb') as f: 
    f.write(pickle.dumps(positions))
    f.close()

print("Generated " + str(len(positions)) + " subsets of length " + str(len(positions[0])))
print("Finished Generating Subsets")

