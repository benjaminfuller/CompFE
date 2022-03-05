import json
import hmac
import cProfile
import multiprocessing
import numpy as np
import random
import string
import time
from hashlib import sha512


class FuzzyExtractor:

    def __init__(self, hash=sha512, selection_method="Uniform"):
        self.hash = hash
        self.selection_method=selection_method

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

    #TODO write this
    def sample_sixia(self, size, biometric_len, number_samples=1, confidence=None):
        if confidence is None:
            print("Can't run Smart sampling without confidence, calling uniform")
            return self.sample_uniform(size, biometric_len, number_samples, confidence)
        #TODO write

    def gen(self, bits, locker_size=43, lockers=10000, confidence=None):
        length = self.hash().digest_size
        key_len = int(length/2)
        pad_len = int(length - length/2)
        r = self.generate_sample(size=key_len)
        zeros = bytearray([0 for x in range(pad_len)])
        check = zeros + r
        seeds = self.generate_sample(length=lockers, size=16)


        p = []
        positions = None
        if self.selection_method == "Uniform":
            positions = self.sample_uniform(locker_size, biometric_len=len(bits), number_samples=lockers, confidence=confidence)
        if self.selection_method == "Smart":
            positions = self.sample_sixia(locker_size, biometric_len=len(bits), number_samples=lockers, confidence=confidence)
        for x in range(lockers):
            v_i = np.array([bits[y] for y in positions[x]])
            seed = seeds[x]
            h = bytearray(hmac.new(seed, v_i, self.hash).digest())
            c_i = self.xor(check, h)
            p.append((c_i, positions[x], seed))
        return r, p

    def confidence_range(self, confidence, bits):
        indeces = []
        for x in range(len(confidence['reals'])):
            r = confidence['reals'][x]
            if(not (r > confidence['positive_start'] and r < confidence['positive_end']) or (r < confidence['negative_start'] and r > confidence['negative_end'])):
                indeces.append(x)
        return np.delete(bits, indeces)

    def rep(self, bits, p, num_processes=1):
        finished = multiprocessing.Array('b', False)
        split = np.array_split(p, num_processes)
        finished = multiprocessing.Manager().list(
            [None for x in range(num_processes)])
        processes = []
        for x in range(num_processes):
            p = multiprocessing.Process(
                target=self.rep_process, args=(bits, split[x], finished, x))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
        if any(finished):
            print("Rep succeeded")
            return next(item for item in finished if item is not None)
        print("Rep failed")
        return None

    def rep_process(self, bits, p, finished, process_id):
        counter = 0
   #     print("Rep processing with "+str(process_id))
        for c_i, positions, seed in p:
            v_i = np.array([bits[x] for x in positions])
            h = bytearray(hmac.new(seed, v_i, self.hash).digest())
            res = self.xor(c_i, h)
            keyLen = int(len(res)/2)
            if self.check_result(res):
                finished[process_id] = res[keyLen:]
                return
            counter += 1
            if counter == 1000:
  #              print(str(process_id)+" resetting counter")
                if(not any(finished)):
                    counter = 0
                else:
                    return

    def check_result(self, res):
        padLen = int(len(res)-len(res)/2)
        return all(v == 0 for v in res[:padLen])

    def xor(self, b1, b2):
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
