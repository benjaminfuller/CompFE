import time
import math
from joblib import Parallel, delayed
import os
import glob
import re
import random
from multiprocessing import Pool
import numpy as np
np.random.seed(1337) # for reproducibility`


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
        pick_range = self.confidence_range(
            confidence, list(range(0, biometric_len - 1)))

        # print(len(pick_range))
        if (len(pick_range) < 1024):
            return "Confidence range too small"

    randGen = random.SystemRandom()
    return np.array([randGen.sample(pick_range, size) for x in range(number_samples)])

    
    
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
    	print ("TPR : ", str(sum(all_tpr)/len(all_tpr)) , ",Average time per rep: ",str(  (rep_end-rep_start)/len(person_tpr)  ),",Reps done: ",reps_done)
    print ("Subsample size", str(subsample_list[k]), "TPR : ", str(sum(all_tpr)/len(all_tpr)) ,",Reps done: ",reps_done)








