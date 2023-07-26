import json
import hmac
import cProfile
import multiprocessing
import numpy as np
import random
import string
import time
from hashlib import sha512
from joblib import Parallel, delayed


class FuzzyExtractor:

    def __init__(self, positions, hash=sha512, selection_method="Uniform", ):
        self.hash = hash
        self.selection_method=selection_method
        self.positions=positions

    #TODO Haven't converted this to Python3.  Current implementation doesn't require
    # confidence information so we'll leave it alone for now
    def gen_config(self, real, bits, config):
        with open(config, "r") as f:
            c = json.load(f)
        c['confidence']['reals'] = real
        return self.gen(bits, c['locker_size'], c['lockers'], c['confidence'])

    def sample_uniform(self, size, biometric_len, number_samples=1, confidence=None):
        if confidence is None:
            pick_range = range(0, biometric_len-1)
        else:
            pick_range = self.confidence_range(
            confidence, list(range(0, biometric_len-1)))

            #print(len(pick_range))
            if(len(pick_range) < 1024):
                return "Confidence range too small"

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
    def sample_sixia(self, size, biometric_len, number_samples=1, confidence=None, alpha_param=0.75):
        if confidence is None:
            print("Can't run Smart sampling without confidence, calling uniform")
            return self.sample_uniform(size, biometric_len, number_samples, confidence)

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

    def gen(self, bits, locker_size=43, lockers=10000, confidence=None):
        length = self.hash().digest_size
        key_len = int(length/2)
        pad_len = int(length - length/2)
        r = self.generate_sample(size=key_len)
        zeros = bytearray([0 for x in range(pad_len)])
        check = zeros + r
        seeds = self.generate_sample(length=lockers, size=16)


        p = []
        encrypted_lockers = []
        positions = None
        if self.positions is None:
            if self.selection_method == "Uniform":
                self.positions = self.sample_uniform(locker_size, biometric_len=len(bits), number_samples=lockers, confidence=confidence)
            if self.selection_method == "Smart":
                self.positions = self.sample_sixia(locker_size, biometric_len=len(bits), number_samples=lockers, confidence=confidence)
        if len(self.positions) < lockers:
            raise Exception("Not enough subsets provided")
        for x in range(lockers):
            v_i = np.array([bits[y] for y in self.positions[x]])
            seed = seeds[x]
            h = bytearray(hmac.new(bytearray(b'11111'), v_i, self.hash).digest())
            encrypted_lockers.append(FuzzyExtractor.xor(check, h))
        return r, encrypted_lockers, seeds

    def confidence_range(self, confidence, bits):
        indeces = []
        for x in range(len(confidence['reals'])):
            r = confidence['reals'][x]
            if(not (r > confidence['positive_start'] and r < confidence['positive_end']) or (r < confidence['negative_start'] and r > confidence['negative_end'])):
                indeces.append(x)
        return np.delete(bits, indeces)

    def rep(self, bits, encrypted_lockers, seeds, num_processes=1):
        split_lockers = np.array_split(encrypted_lockers, num_processes)
        split_seeds = np.array_split(seeds, num_processes)
        split_positions = np.array_split(self.positions, num_processes)
        processes = []
        found_match = Parallel(n_jobs=num_processes)(delayed(FuzzyExtractor.rep_process)
                                                   (bits, split_lockers[i], split_seeds[i], split_positions[i], self.hash, i)
                                                   for i in range(num_processes))
        return found_match[0]

    @staticmethod
    def rep_process(bits, lockers, seeds, positions, hash, process_id):
        for i in range(len(lockers)):
            v_i = np.array([bits[x] for x in positions[i]])
            h = bytearray(hmac.new(bytearray(b'11111'), v_i, hash).digest())
            res = FuzzyExtractor.xor(lockers[i], h)
            if FuzzyExtractor.check_result(res):
                return i
        return -1


    @staticmethod
    def check_result(res):
        padLen = int(len(res)-len(res)/2)
        return all(v == 0 for v in res[:padLen])

    @staticmethod
    def xor(b1, b2):
        return bytearray([x ^ y for x, y in zip(b1, b2)])

    def generate_sample(self, length=0, size=32):
        if(length == 0):
            return bytearray([random.SystemRandom().randint(0, 255) for x in range(int(size))])
        else:
            samples = []
            for x in range(length):
                samples.append(
                    bytearray([random.SystemRandom().randint(0, 255) for x in range(int(size))]))
            return samples


def read(path):
    with open(path, 'r') as f:
        return json.load(f)


if __name__ == '__main__':
    f1 = read("tests/test_files/test.bin")
    f2 = read("tests/test_files/same.bin")
    f3 = read("tests/test_files/diff.bin")
    fe = FuzzyExtractor()
    r, p = fe.gen(f1, locker_size=25, lockers=10000, confidence=None)
    print("Testing rep with same value")
    fe.rep(f1, p, num_processes=6)
    print("Testing rep with value from same biometric")
    fe.rep(f2, p, num_processes=6)
    print("Testing rep with value from different biometric")
    fe.rep(f3, p)
    #cProfile.run("fe.gen(f1, lockers=1000)", sort='cumtime')
    #cProfile.run("fe.rep(f2, p)", sort="cumtime")
