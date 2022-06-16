import time
import math
from joblib import Parallel, delayed
import os
import sys
import glob
import re
import random
from multiprocessing import Pool
import numpy as np
import multiprocessing as mp
#np.random.seed(1337) # for reproducibility`

################################################################################
#                      FUNCTION DEFINITIONS                                    #
################################################################################

def numericalSort(value):
    parts = numbers.split(value)
    parts[1::2] = map(int, parts[1::2])
    return parts

def read_fvector(filePath):
    with open(filePath) as f:
        for line in f.readlines():
            temp_str = np.fromstring(line, sep=",")
            return [int(x) for x in temp_str]

# Returns a numpy array of python arrays each chosen randomly with size number_samples
def sample_uniform(size, biometric_len, number_samples=1, confidence=None):
    pick_range = range(0, biometric_len - 1)
    randGen = random.SystemRandom()
    return np.array([randGen.sample(pick_range, size) for x in range(number_samples)])

def binary_entropy(val):
    return -(val) * math.log2(val) - (1 - val) * (math.log(1-val))

def read_complex_conf(filepath):
        with open(filepath, 'r') as f:
            confidence = []
            lines = f.readlines()
            for line in lines:
                numbers = line[42:].strip()
                numbers_list = numbers.split(' ')
                predictability = (1 - float(numbers_list[2]))
                entropy = binary_entropy(float(numbers_list[3]))
                pair = [predictability, entropy]
                confidence.append(pair)
            return confidence

def gen(template,positions):
    ret_value = []
    for x in range(positions.shape[0]):
        v_i = template[positions[x]]
        ret_value.append(v_i)
    return ret_value

def sample_sixia(size, biometric_len, number_samples, confidence, alpha_param):
    if confidence is None:
        print("Can't run Smart sampling without confidence, calling uniform")
        return sample_uniform(size, biometric_len, number_samples, confidence)

    sample_array = []
    new_confidence = [pair[0] for pair in confidence]
    iter_total_prob = sum(new_confidence)
    new_confidence = [x / iter_total_prob for x in new_confidence]
    for set_selection_iter in range(number_samples):
        sample_indices = random.choices(range(len(new_confidence)), weights=new_confidence, k=size)
        dedup_indices = list(set(sample_indices))
        loop_count = 1
        while len(dedup_indices) < size:
            new_index = random.choices(range(len(new_confidence)), weights=new_confidence, k=1)
            sample_indices = dedup_indices
            sample_indices.extend(new_index)
            dedup_indices = []
            [dedup_indices.append(n) for n in sample_indices if n not in dedup_indices]
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
    new_confidence = [pair[0] ** (alpha_param / pair[1]) for pair in confidence]
    iter_total_prob = sum(new_confidence)
    new_confidence = [x / iter_total_prob for x in new_confidence]
    for set_selection_iter in range(number_samples):
        sample_indices = random.choices(range(len(new_confidence)), weights=new_confidence, k=size)
        dedup_indices = list(set(sample_indices))
        loop_count = 1
        while len(dedup_indices) < size:
            new_index = random.choices(range(len(new_confidence)), weights=new_confidence, k=1)
            sample_indices = dedup_indices
            sample_indices.extend(new_index)
            dedup_indices = []
            [dedup_indices.append(n) for n in sample_indices if n not in dedup_indices]
            loop_count = loop_count +1
            if loop_count == 1000000:
                print("Smart sampling failed to find a non-duplicating subset")
                exit(1)
        sample_array.append(dedup_indices)
    return np.array(sample_array)

def rep_helperr2(template, positions, gen_template):
    i = 0
    for x in range(positions.shape[0]):
        v_i = template[positions[x]]
        if np.array_equal(v_i ,gen_template[i]):
            return 1
        i = i + 1
    return 0

def rep(template, positions, gen_template, num_jobs=32):
    i = 0
    number_jobs = num_jobs

    positions_split = np.array_split (positions, number_jobs)
    gen_template_split = np.array_split(gen_template, number_jobs)

    found_match = Parallel(n_jobs=number_jobs)(delayed(rep_helperr2)
                                                (template, positions_split[i], gen_template_split[i])
                                                for i in range(number_jobs))
    for match in found_match:
        if match == 1:
            return 1
    return 0

def subsample(templates,positions):
    subsampled_array = []
    for x in range(templates.shape[0]):
        subsampled_array.append(templates[x][positions])
    return np.array(subsampled_array)




def entropy_helper(template,template_split,gt, gt_split):
    i = 0
    blue_list = []
    red_list = []
    for x in range(template.shape[0]):
        for y in range(template_split.shape[0]):
            if(gt[x][0] < gt_split[y][0]):
                continue
            dis = np.count_nonzero(template[x]!=template_split[y])
            dis = dis/template[x].shape[1]
	#Just a stupid hack
            if (dis == 0):
                continue
            if(gt[x][0] == gt_split[y][0]):
                blue_list.append(dis)
            else:
                red_list.append(dis)

    return blue_list,red_list

    
def entropy(templates, ground_truth, selection_method,subsample_list,num_jobs=32):
    
    runs = 10
    entropy_list = []
    for r in range(runs):
        if selection_method == 'complex':
            print("Using Complex Sixia Sampling")
            positions = sample_sixia_with_entropy(subsample_list[k],1024,num_lockers,confidence,alphas[k])    
        else: 
            print("Using Simple Sixia Sampling")
        positions = sample_sixia(subsample_list[k],1024,1,confidence,alphas[k])  

        subsampled_templates = subsample(templates,positions)
        blue = []
        red = []
        i = 0
        number_jobs = num_jobs

        templates_split = np.array(np.array_split(subsampled_templates, number_jobs))
        ground_truth_split = np.array(np.array_split(ground_truth, number_jobs))




        found_match = Parallel(n_jobs=number_jobs)(delayed(entropy_helper)
                                                   (subsampled_templates,templates_split[i],ground_truth,ground_truth_split[i])
                                                   for i in range(number_jobs))
        for x in range(len(found_match)):
                blue.extend(found_match[x][0])
                red.extend(found_match[x][1])


        u = np.mean(red)
        entropy = (u*(1-u))/np.var(red)
        entropy_list.append(2**(-1 * entropy))
        print ("Entropy Run# ",r," Entropy ",entropy," Mean of unlike dist ",u)
        
    exp_ent = np.mean(entropy_list)
    avg_ent = -1 * math.log(exp_ent, 2)
    print ("Average Entropy", avg_ent)
    return avg_ent,entropy_list




################################################################################
#                    EXECUTION SCRIPT                                          #
################################################################################

# Command Line Usage:
# python3 CompFE_fast.py [number of classes] [subset size] ['simple' or 'complex'] [alpha] [number of subsets]

subsample_classes = int(sys.argv[1])
subsample_list = [int(sys.argv[2])]
selection_method = sys.argv[3]
alphas = [float(sys.argv[4])]
num_lockers = int(sys.argv[5])
numbers = re.compile(r'(\d+)')
cwd = os.getcwd()
folder_list = sorted(glob.glob(cwd + "/iris_right_all_dense_0.205_57-75_1024_folders/*"),key=numericalSort)
print (cwd)
CLASSES = len(folder_list)
print ("Folders: ",len(folder_list))
print ("Sampling " + str(subsample_classes) + " classes")

num_classes = random.sample(range(CLASSES), subsample_classes)

print("Reading Confidence")
confidence = read_complex_conf(cwd + "/PythonImpl/AuxiliaryFiles/ConfidenceInfo.txt")

print ("Reading templates")
templates = []
ground_truth = []

for x in range(len(num_classes)):
    template_temp = []
    ground_truth_temp = []

    template_list = glob.glob(folder_list[num_classes[x]] + "/*")
    for y in range(len(template_list)):
        ret_template = np.array(read_fvector(template_list[y]))
        template_temp.append(ret_template)
        ground_truth_temp.append([x,y])

    templates.append(template_temp)
    ground_truth.extend(ground_truth_temp)

for k in range(len(subsample_list)):
    print ("Generating positions")
    # positions = sample_uniform(subsample_list[k],1024,num_lockers)    
    if selection_method == 'complex':
        print("Using Complex Sixia Sampling")
        positions = sample_sixia_with_entropy(subsample_list[k],1024,num_lockers,confidence,alphas[k])    
    else: 
        print("Using Simple Sixia Sampling")
        positions = sample_sixia(subsample_list[k],1024,num_lockers,confidence,alphas[k])  
    all_tpr = []
    reps_done = 0
    print ("Starting gen and rep for", str(subsample_list[k]), num_lockers)
    for x in range(len(templates)):
        templateNum = x

        gen_template = np.array(gen( np.array(templates[templateNum][0]),np.array(positions)))

        
        person_tpr = []
        rep_start = time.time()
        for y in range(1,len(templates[templateNum])):
            person_tpr.append(rep(templates[templateNum][y], positions, gen_template,4))
        rep_end = time.time()
        print ("Rep time:" ,rep_end-rep_start)

    #    print (person_tpr,sum(person_tpr))
        reps_done += len(person_tpr)

        all_tpr.extend( person_tpr)
        print ("TPR :", str(sum(all_tpr)/len(all_tpr)), "| Average time per rep:", str((rep_end-rep_start)/len(person_tpr)  ),"| Reps done:", reps_done)
    print ("Subsample size:", str(subsample_list[k]), "| TPR :", str(sum(all_tpr)/len(all_tpr)) ,"| Reps done:",reps_done)



'''
	Entropy Calculation
'''

templates = np.array([item for sublist in templates for item in sublist ])
ground_truth = np.array(ground_truth)
entropy,entropy_list = entropy(templates,ground_truth,selection_method,subsample_list)
