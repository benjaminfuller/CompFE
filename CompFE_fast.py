from curses import pair_content
import time
import math
from turtle import pos, position
from unittest.loader import VALID_MODULE_NAME
from joblib import Parallel, delayed
import os
import sys
import glob
import re
import random
from multiprocessing import Pool
import numpy as np
import multiprocessing as mp
import matplotlib.pyplot as plt
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

def sample_uniform_entropy_threshold(size, biometric_len, number_samples, confidence, threshold):
    if confidence is None:
        print("No confidence file given, cannot estimate entropy. Defaulting to set size subset uniform sampling.")
        return sample_uniform(size, biometric_len, number_samples, confidence=None)
    
    sample_array=[]
    for _ in range(number_samples):
        sampled_indicies = []
        current_confidence_estimation_total = 0
        while(current_confidence_estimation_total < threshold):
            selected_indices = random.choices(range(len(confidence)),k=int(np.ceil(threshold - current_confidence_estimation_total)))
            for index in selected_indices:
                if index not in sampled_indicies:
                    current_confidence_estimation_total = current_confidence_estimation_total + binary_entropy(2 * confidence[index][1] * (1 - confidence[index][1]))
                    sampled_indicies.append(index)
        sample_array.append(sampled_indicies)
    return sample_array

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

def gen(template,positions):
    ret_value = []
    for x in range(positions.shape[0]):
        v_i = template[positions[x]]
        ret_value.append(v_i)
    return ret_value

def sample_sixia(size, biometric_len, number_samples, confidence, alpha_param):
    bad_list = [28, 200, 503, 754]
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

def sample_sixia_entropy_threshold(size, biometric_len, number_samples, confidence, alpha_param, threshold):
    if confidence is None:
        print("No confidence file given, cannot estimate entropy. Defaulting to set size subset uniform sampling.")
        return sample_uniform(size, biometric_len, number_samples, confidence=None)
    
    for pair in confidence:
        print(pair)
    new_confidence = [pair[0] ** alpha_param for pair in confidence]
    total_confidence = sum(new_confidence)
    new_confidence = [item / total_confidence for item in new_confidence]
    sample_array = []
    for _ in range(number_samples):
        sampled_indicies = []
        current_confidence_estimation_total = 0
        while(current_confidence_estimation_total < threshold):
            # print("Current Confidence Sum:", current_confidence_estimation_total)
            # print("Current Gap:",int(np.ceil(threshold - current_confidence_estimation_total)))
            selected_indices = random.choices(range(len(new_confidence)), weights=new_confidence,k=int(np.ceil(threshold - current_confidence_estimation_total)))
            # print("Size of sampled set:", len(selected_indices))
            for index in selected_indices:
                if index not in sampled_indicies:
                    # print("----")
                    # print("index:", index)
                    # print("Unlike mean:",confidence[index][1])
                    # print("Two samples difference:",binary_entropy(2 * confidence[index][1] * (1 - confidence[index][1])))
                    # print("binary entropy of unlike mean:",binary_entropy(confidence[index][1]))
                    # print("binary entropy of binary entropy of unlike mean:",binary_entropy(binary_entropy(confidence[index][1])))
                    # print("----")
                    current_confidence_estimation_total = current_confidence_estimation_total + binary_entropy(2 * confidence[index][1] * (1 - confidence[index][1]))
                    # current_confidence_estimation_total = current_confidence_estimation_total + binary_entropy(confidence[index][1])
                    # sampled_indicies.append([index,binary_entropy(confidence[index][1])])
                    sampled_indicies.append([index,binary_entropy(2 * confidence[index][1] * (1 - confidence[index][1]))])
        sample_array.append(sampled_indicies)
    return sample_array


# Current Working Project
def sample_sixia_with_entropy(size, biometric_len, number_samples, confidence, alpha_param):
    bad_list = [28, 200, 503, 754]
    if confidence is None:
        print("Can't run Smart sampling without confidence, calling uniform")
        return sample_uniform(size, biometric_len, number_samples, confidence)

    sample_array = []
    new_confidence = [pair[0] ** (alpha_param / binary_entropy(pair[1])) for pair in confidence]

    for set_selection_iter in range(number_samples):
        sample_indices = random.choices(range(len(new_confidence)), weights=new_confidence, k=size)
        sample_indices = [index for index in sample_indices if index not in bad_list]
        dedup_indices = list(set(sample_indices))
        loop_count = 1
        while len(dedup_indices) < size:
            new_index = random.choices(range(len(new_confidence)), weights=new_confidence, k=max(1,size - len(dedup_indices)))
            [dedup_indices.append(n) for n in new_index if n not in dedup_indices and n not in bad_list]
            loop_count = loop_count +1
            if loop_count == 1000000:
                print("Smart sampling failed to find a non-duplicating subset")
                exit(1)
        sample_array.append(dedup_indices)
    return np.array(sample_array)

def sample_sixia_with_entropy_entropy_threshold(size, biometric_len, number_samples, confidence, alpha_param, threshold):
    if confidence is None:
        print("No confidence file given, cannot estimate entropy. Defaulting to set size subset uniform sampling.")
        return sample_uniform(size, biometric_len, number_samples, confidence=None)
    
    new_confidence = [pair[0] ** (alpha_param/(binary_entropy(pair[1]))) for pair in confidence]
    total_confidence = sum(new_confidence)
    new_confidence = [item / total_confidence for item in new_confidence]
    sample_array = []
    for _ in range(number_samples):
        sampled_indicies = []
        current_confidence_estimation_total = 0
        while(current_confidence_estimation_total < threshold):
            # print("Current Confidence Sum:", current_confidence_estimation_total)
            # print("Current Gap:",int(np.ceil(threshold - current_confidence_estimation_total)))
            selected_indices = random.choices(range(len(new_confidence)), weights=new_confidence,k=int(np.ceil(threshold - current_confidence_estimation_total)))
            # print("Size of sampled set:", len(selected_indices))
            for index in selected_indices:
                if index not in sampled_indicies:
                    # print("----")
                    # print("index:", index)
                    # print("Unlike mean:",confidence[index][1])
                    # print("Two samples difference:",binary_entropy(2 * confidence[index][1] * (1 - confidence[index][1])))
                    # print("binary entropy of unlike mean:",binary_entropy(confidence[index][1]))
                    # print("binary entropy of binary entropy of unlike mean:",binary_entropy(binary_entropy(confidence[index][1])))
                    # print("----")
                    current_confidence_estimation_total = current_confidence_estimation_total + binary_entropy(2 * confidence[index][1] * (1 - confidence[index][1]))
                    # current_confidence_estimation_total = current_confidence_estimation_total + binary_entropy(confidence[index][1])
                    # sampled_indicies.append([index,binary_entropy(confidence[index][1])])
                    sampled_indicies.append([index,binary_entropy(2 * confidence[index][1] * (1 - confidence[index][1]))])
        sample_array.append(sampled_indicies)
    return sample_array

def rep_helperr2(template, positions, gen_template,index,num_jobs, sum):
    i = 0
    match_list = []
    for x in range(positions.shape[0]):
        v_i = template[positions[x]]
        if np.array_equal(v_i ,gen_template[i]):
            match_list.append(i + sum)
        i = i + 1
    return match_list

def rep(template, positions, gen_template, num_jobs=32):
    number_jobs = num_jobs
    # print("positions shape" ,positions.shape)
    positions_split = np.array_split (positions, number_jobs)
    # print("",len(positions_split))
    sums = [0]
    sum = 0
    for sublist in positions_split:
            # print(" ",len(sublist))
            sum = sum + len(sublist)
            sums.append(sum)
    gen_template_split = np.array_split(gen_template, number_jobs)

    found_match = Parallel(n_jobs=number_jobs)(delayed(rep_helperr2)
                                                (template, positions_split[i], gen_template_split[i],i,num_jobs,sums[i])
                                                for i in range(number_jobs))
    matches = []
    for match_list in found_match:
        if match_list != []:
            matches.extend(match_list)
    return matches

def subsample(templates,positions):
    print("In subsampling")
    print(templates.shape)
    print(len(positions),len(positions[0]))
    subsampled_array = []
    for x in range(templates.shape[0]):
        # print("Template:", x)
        new_subsample = []
        for list in positions:
            new_subsample = [templates[x][index] for index in list]
            # print("Subsample:",new_subsample)
        subsampled_array.append(new_subsample)
    print("Returning from subsampling")
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
            # dis = dis/template[x].shape[1]
            dis = dis / template.shape[1]
	#Just a stupid hack
            if (dis == 0):
                continue
            if(gt[x][0] == gt_split[y][0]):
                blue_list.append(dis)
            else:
                red_list.append(dis)

    return blue_list,red_list

    
def entropy(templates, ground_truth, selection_method,size_or_threshold,num_jobs=4,positions=[]):
    if len(positions) != 0:
        runs = len(positions)
    else: 
        runs = 10
    
    entropy_list = []
    for r in range(runs):
        if len(positions) == 0:
            if selection_method == 'complex':
                print("Using Complex Sixia Sampling")
                positions = sample_sixia_with_entropy(size_or_threshold,1024,1,confidence,alpha_param)    
            else: 
                print("Using Simple Sixia Sampling")
                positions = sample_sixia(size_or_threshold,1024,1,confidence,alpha_param)  

        print("Subsampling Templates")
        subsampled_templates = subsample(templates,positions[r:r+1])
        print("Finished Subsampling")
        blue = []
        red = []
        i = 0
        print("Using",num_jobs,"cores for Entropy")
        number_jobs = num_jobs

        print("Splitting templates and Ground Truths")
        templates_split = np.array(np.array_split(subsampled_templates, number_jobs))
        ground_truth_split = np.array(np.array_split(ground_truth, number_jobs))
        print("Finished Split")

        print("Searching for Matches")
        found_match = Parallel(n_jobs=number_jobs)(delayed(entropy_helper)
                                                   (subsampled_templates,templates_split[i],ground_truth,ground_truth_split[i])
                                                   for i in range(number_jobs))
        
        for x in range(len(found_match)):
                blue.extend(found_match[x][0])
                red.extend(found_match[x][1])

        print("Calculating Statistics")
        u = np.mean(red)
        entropy = (u*(1-u))/np.var(red)
        print("Adding to list")
        entropy_list.append(2**(-1 * entropy))
        print ("Entropy Run #",r," Entropy:",entropy,"Mean of unlike dist:",u)
        
    exp_ent = np.mean(entropy_list)
    avg_ent = -1 * math.log(exp_ent, 2)
    print ("Average Entropy", avg_ent)
    return avg_ent,entropy_list




################################################################################
#                    EXECUTION SCRIPT                                          #
################################################################################

# Command Line Usage:
# python3 CompFE_fast.py [number of classes for TAR test] ['threshold' or 'size'] [subset size or entropy threshold] ['simple' or 'complex'] [alpha] [number of subsets]

subsample_classes = int(sys.argv[1])
stopping_condition = sys.argv[2]
size_or_threshold = int(sys.argv[3])
selection_method = sys.argv[4]
alpha_param = float(sys.argv[5])
num_lockers = int(sys.argv[6])
numbers = re.compile(r'(\d+)')
cwd = os.getcwd()
num_cpus = mp.cpu_count()
folder_list = sorted(glob.glob(cwd + "/CompFE/iris_best-entropy/*"),key=numericalSort)
print (cwd)
CLASSES = len(folder_list)
print ("Folders: ",len(folder_list))
print ("Sampling " + str(subsample_classes) + " classes")

num_classes = random.sample(range(CLASSES), subsample_classes)

print("Reading Confidence")
confidence, bad_list = read_complex_conf(cwd + "/CompFE/PythonImpl/AuxiliaryFiles/ConfidenceInfoNFE.txt")

# positions = sample_sixia_with_entropy_entropy_threshold(0,1024,num_lockers,confidence,alpha_param,size_or_threshold)
# positions = sample_sixia_entropy_threshold(0,1024,num_lockers,confidence,alpha_param,size_or_threshold)
# positions = sample_uniform_entropy_threshold(size_or_threshold,1024,num_lockers,confidence,size_or_threshold)
# print("Number of Subsets",len(positions))
# for subset in positions:
#     subset_sum = 0
#     for pair in subset:
#         subset_sum = subset_sum + pair[1]
#     print("Sum of the subset's marginal entropies",subset_sum)
# print("Subsets",positions)

# values = [len(item) for item in positions]
# plt.hist(x=values, bins='auto', color='#33ffaa')
# plt.xlabel('Lengths of subsets with fixed entropy')
# plt.ylabel('Frequency')
# plt.title("Length of subsets with " + str(size_or_threshold) + " bits of requested entropy")
# plt.show()
# plt.close()

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
print("Finished reading Templates")

if stopping_condition == 'size':
    print ("Generating positions with fixed size")   
    if selection_method == 'complex':
        print("Using Complex Sixia Sampling")
        positions = sample_sixia_with_entropy(size_or_threshold,1024,num_lockers,confidence,alpha_param)    
    else: 
        print("Using Simple Sixia Sampling")
        positions = sample_sixia(size_or_threshold,1024,num_lockers,confidence,alpha_param)  
    all_tpr = []
    all_matches = []
    reps_done = 0
    for subset in positions:
        for index in subset:
            if index in bad_list:
                print("Bad",index,"found")
    print ("Starting gen and rep for alpha", str(alpha_param), "Subset size",str(size_or_threshold),"and", str(num_lockers),"subsets")
    for x in range(len(templates)):
        templateNum = x
        print("Staring gen (single threaded)")
        gen_template = np.array(gen( np.array(templates[templateNum][0]),np.array(positions)))
        print("Finished Gen")
        person_tpr = []
        print("Starting Rep")
        rep_start = time.time()
        matches = []
        for y in range(1,len(templates[templateNum])):
            temp_matches = rep(templates[templateNum][y], positions, gen_template,num_cpus)
            matches.extend(temp_matches)
            person_tpr.append(temp_matches != [])
        rep_end = time.time()
        print("Rep time:" ,rep_end-rep_start)

    #    print (person_tpr,sum(person_tpr))
        reps_done += len(person_tpr)

        all_tpr.extend( person_tpr)
        all_matches.extend(matches)
        print ("TPR :", str(sum(all_tpr)/len(all_tpr)), "| Average time per rep:", str((rep_end-rep_start)/len(person_tpr)  ),"| Reps done:", reps_done, "Subset Indices:", str(matches))
    print ("Subsample size:", str(size_or_threshold), "| TPR :", str(sum(all_tpr)/len(all_tpr)) ,"| Reps done:",reps_done)
    print ("Matched Indicies over TPR:", set(all_matches), "With lockers: ", num_lockers)

    match_dict = {ind : 0 for ind in set(all_matches)}
    for match in all_matches:
        match_dict[match] += 1

    print(match_dict)

    # plt.hist(all_matches, bins=(max(all_matches)+1))
    # plt.show()

# elif stopping_condition is 'threshold':
#     print ("Generating positions with enttopy threshold")   
#     if selection_method is 'complex':
#         print("Using Complex Sixia Sampling")
#         positions = sample_sixia_with_entropy_entropy_threshold(size_or_threshold,1024,num_lockers,confidence,alpha_param,size_or_threshold)    
#     else: 
#         print("Using Simple Sixia Sampling")
#         positions = sample_sixia_with_entropy_entropy_threshold(size_or_threshold,1024,num_lockers,confidence,alpha_param,size_or_threshold)  
#     all_tpr = []
#     reps_done = 0
#     print ("Starting gen and rep for alpha", str(alpha_param), "Entropy threshold",str(size_or_threshold),"and", str(num_lockers),"subsets")
#     for x in range(len(templates)):
#         templateNum = x
#         print("Staring gen (single threaded)")
#         gen_template = np.array(gen( np.array(templates[templateNum][0]),np.array(positions)))
#         print("Finished Gen")
#         person_tpr = []
#         print("Starting Rep")
#         rep_start = time.time()
#         for y in range(1,len(templates[templateNum])):
#             person_tpr.append(rep(templates[templateNum][y], positions, gen_template,num_cpus))
#         rep_end = time.time()
#         print("Rep time:" ,rep_end-rep_start)

#     #    print (person_tpr,sum(person_tpr))
#         reps_done += len(person_tpr)

#         all_tpr.extend( person_tpr)
#         print ("TPR :", str(sum(all_tpr)/len(all_tpr)), "| Average time per rep:", str((rep_end-rep_start)/len(person_tpr)  ),"| Reps done:", reps_done)
#     print ("Subsample size:", str(size_or_threshold), "| TPR :", str(sum(all_tpr)/len(all_tpr)) ,"| Reps done:",reps_done)

# '''
# 	Entropy Calculation
# '''
print("Beginning Entropy Calculation")
templates = np.array([item for sublist in templates for item in sublist ])
print("Shape of Templates:", templates.shape)
ground_truth = np.array(ground_truth)
print("Shape of Ground Truths:",ground_truth.shape)
avg_entropy,entropy_list = entropy(templates,ground_truth,selection_method,size_or_threshold,num_jobs=num_cpus, positions=positions)
print("Finished Entropy Calculation")