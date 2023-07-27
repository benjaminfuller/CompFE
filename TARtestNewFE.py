import math
import time
from multiprocessing.dummy import freeze_support

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
from hashlib import sha512
from statistics import variance

from PythonImpl.FuzzyExtractor_1_parallel import FuzzyExtractor


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

    
def entropy(templates, ground_truth, selection_method,size_or_threshold,num_jobs=4,positions=[],start=0):
    if len(positions) != 0:
        runs = len(positions)
    else: 
        runs = 10
    
    entropy_list = []
    for r in range(start,runs):
        if len(positions) == 0:
            if selection_method == 'complex':
                print("Using Complex Sixia Sampling")
                positions = sample_sixia_with_entropy(size_or_threshold,1024,1,confidence,alpha_param)    
            else: 
                print("Using Simple Sixia Sampling")
                positions = sample_sixia(size_or_threshold,1024,1,confidence,alpha_param)  

        print("Subsampling Templates")
        subsampled_templates = subsample(templates,positions[r:r+1])
        print(len(subsampled_templates), len(subsampled_templates[0]))
        print("Finished Subsampling")
        blue = []
        red = []
        i = 0
        print("Using",num_jobs,"cores for Entropy")
        number_jobs = num_jobs

        print("Splitting templates and Ground Truths")
        templates_split = np.array(np.array_split(subsampled_templates, number_jobs),dtype=object)
        ground_truth_split = np.array(np.array_split(ground_truth, number_jobs),dtype=object)
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
        degrees_freedom = (u*(1-u))/np.var(red)
        print("Adding to list")

        entropy = degrees_freedom * binary_entropy(u)

        entropy_list.append(2**(-1 * entropy))
        print(u,np.var(red))
        print ("Entropy Run #",r," Entropy:",entropy,"Mean of unlike dist:",u, "Mean of like:", np.mean(blue))

        # plt.hist(red, bins=20)
        # plt.show()
        # plt.hist(blue, bins=20)
        # plt.show()
        
    exp_ent = np.mean(entropy_list)
    avg_ent = -1 * math.log(exp_ent, 2)
    print ("Average Entropy", avg_ent)
    return avg_ent,entropy_list




################################################################################
#                    EXECUTION SCRIPT                                          #
################################################################################

# Command Line Usage:
# python3 CompFE_fast.py [subset size or entropy threshold] [number of subsets] [filename for positions] 
if __name__ == '__main__':
    freeze_support()

    do_cryptography=1
    print(sys.argv)
    size_or_threshold = int(sys.argv[1]) # Subset size
    num_lockers = int(sys.argv[2]) # number of subsets sampled
    filename = sys.argv[3]
    numbers = re.compile(r'(\d+)')
    cwd = os.getcwd()
    num_cpus = 2*mp.cpu_count()
    folder_list = sorted(glob.glob(cwd + "/iris_best-entropy/*"),key=numericalSort)
    CLASSES = len(folder_list)
    print ("Folders: ",len(folder_list))
    num_classes = range(len(folder_list))

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

    print("Length of templates "+str(len(templates)))

    all_tpr = []
    all_matches = []
    reps_done = 0

    with open("subsets/" + filename + ".pkl", 'rb') as f:
        positions = pickle.load(f)
        f.close()

    print("Finished reading positions")

    print ("Starting gen and rep for Subset size",str(size_or_threshold),"and", str(num_lockers),"subsets")
    gen_time=[]
    rep_time=[]
    for x in range(min(len(templates),40)):
        templateNum = x
        if templates[templateNum] is None or len(templates[templateNum]) < 2:
            continue

        matches = []
        hamming_distance = []
        if do_cryptography == 0:
            gen_start=time.time()
            gen_template = np.array(gen( np.array(templates[templateNum][0]),np.array(positions)))
            gen_end=time.time()
            print("Finished Gen")
            gen_time.append(gen_end-gen_start)
            person_tpr = []
            print("Starting Rep")
            rep_start = time.time()

            for y in range(1,min(len(templates[templateNum]),11)):
                hdist = np.count_nonzero([templates[templateNum][y][i]!=templates[templateNum][0][i] for i in range(len(templates[templateNum][0]))])
                hamming_distance.append(hdist)
                temp_matches = rep(templates[templateNum][y], positions, gen_template,2*num_cpus)
                matches.extend(temp_matches)
                person_tpr.append(temp_matches != [])
            rep_end = time.time()
            rep_time.append(rep_end-rep_start)
        else:
            gen_start = time.time()
            fuzzext = FuzzyExtractor(positions=np.array(positions))
            (r, encrypted_lockers, seeds) = fuzzext.gen(templates[templateNum][0], locker_size=size_or_threshold, lockers=num_lockers)
            gen_end = time.time()
            gen_time.append(gen_end-gen_start)
            person_tpr = []
            for y in range(1,min(len(templates[templateNum]), 11)):
                hdist = np.count_nonzero([templates[templateNum][y][i]!=templates[templateNum][0][i] for i in range(len(templates[templateNum][0]))])
                hamming_distance.append(hdist)
                rep_start = time.time()
                temp_matches = fuzzext.rep(templates[templateNum][y], encrypted_lockers, seeds, num_processes=1)
                rep_end = time.time()
                rep_time.append(rep_end-rep_start)
                person_tpr.append(temp_matches!=-1)
                matches.append(temp_matches)

        reps_done += len(person_tpr)

        all_tpr.extend(person_tpr)
        all_matches.extend(matches)
        print(matches)
        print ("TPR :", str(sum(person_tpr)/len(person_tpr)),"| Reps done:", reps_done,"| Avg Hamming:",str(sum(hamming_distance)/len(hamming_distance)), flush=True)
    print ("Subsample size:", str(size_or_threshold), "| TPR :", str(sum(all_tpr)/len(all_tpr)) ,"| Reps done:",reps_done)
    print("Generate time:",str(sum(gen_time)/len(gen_time)), " Gen variance:",str(variance(gen_time)))
    print("Rep time:", str(sum(rep_time)/len(rep_time)), "Rep variance:", str(variance(rep_time)))
    # print ("Matched Indicies over TPR:", set(all_matches), "With lockers: ", num_lockers)

    print("Finished TAR test")
