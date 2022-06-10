import time
import math
from joblib import Parallel, delayed
import os
import glob
import re
import random
from multiprocessing import Pool
import numpy as np
#np.random.seed(1337) # for reproducibility`


# %matplotlib notebook


subsample_classes = 50
subsample_list = [65,70,75]
num_lockers = 500000


numbers = re.compile(r'(\d+)')
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
# Assumptions: Github Bots are bad
def sample_uniform(size, biometric_len, number_samples=1, confidence=None):
    if confidence is None:
        pick_range = range(0, biometric_len - 1)
    else:
        exit(1)

    randGen = random.SystemRandom()
    return np.array([randGen.sample(pick_range, size) for x in range(number_samples)])

# Should return a numpy array of python arrays each chosen according to the algorithm
#   written by Sixia and Alex that uses confidence information to pick better subsets
# Assumptions: the confidence array is a list of probabilities with length equal to 
#   the length of the feature vector  relating to the probability that that bit
#   agrees with the biometric. In the original algorithm, rather than searching for an 
#   error free subset, they searched for an subset that was only ones and thus did not
#   have to consider agreement with another bit string (thus the probability was for 
#   each index being 1 not being in agreement).
def sample_sixia(size, biometric_len, number_samples=1, confidence=None, alpha_param=0.75):
    if confidence is None:
        print("Can't run Smart sampling without confidence, calling uniform")
        return sample_uniform(size, biometric_len, number_samples, confidence)

    sample_array = []
    new_confidence = [x ** alpha_param for x in confidence]  # Is this the most efficient way?
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
    
def gen(template,positions):
    ret_value = []
    for x in range(positions.shape[0]):
        v_i = template[positions[x]]
        ret_value.append(v_i)
    return ret_value


    
cwd = os.getcwd()


folder_list = sorted(glob.glob(cwd + "/iris_right_all_dense_0.205_57-75_1024_folders/*"),key=numericalSort)
CLASSES = len(folder_list)
print ("Folders: ",len(folder_list))
print ("Sampling " + str(subsample_classes) + " classes")


num_classes = random.sample(range(CLASSES), subsample_classes)


print ("Reading templates")
templates = []
for x in range(len(num_classes)):
    template_temp = []
    template_list = glob.glob(folder_list[num_classes[x]] + "/*")
    for y in range(len(template_list)):
        ret_template = np.array(read_fvector(template_list[y]))
        template_temp.append(ret_template)
    templates.append(template_temp)
    
for k in range(len(subsample_list)):
    print ("Generating positions")
    positions = sample_uniform(subsample_list[k],1024,num_lockers)    


    import multiprocessing as mp

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


    all_tpr = []
    reps_done = 0
    print ("Starting gen and rep for ", str(subsample_list[k]), num_lockers)
    for x in range(len(templates)):
        templateNum = x

#         gen_start = time.time()

        gen_template = np.array(gen( np.array(templates[templateNum][0]),np.array(positions)))

#         gen_end = time.time()

        #print ("Gen time: " ,gen_end-gen_start)


        person_tpr = []
        rep_start = time.time()

        for y in range(1,len(templates[templateNum])):
            person_tpr.append( rep(templates[templateNum][y],positions,gen_template,32) )
        rep_end = time.time()
        print ("Rep time: " ,rep_end-rep_start)

        # print (person_tpr,sum(person_tpr))
        reps_done += len(person_tpr)
        all_tpr.extend(  person_tpr   )
        print("TPR : ", str(sum(all_tpr)/len(all_tpr)) , ",Average time per rep: ",str(  (rep_end-rep_start)/len(person_tpr)  ),",Reps done: ",reps_done)
    print ("Subsample size", str(subsample_list[k]), "TPR : ", str(sum(all_tpr)/len(all_tpr)) ,",Reps done: ",reps_done)








