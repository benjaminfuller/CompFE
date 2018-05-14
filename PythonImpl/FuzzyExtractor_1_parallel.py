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

    def __init__(self, hash=sha512):
        self.hash = hash

    def gen_config(self, real, bits, config):
        with open(config, "r") as f:
            c = json.load(f)
        c['confidence']['reals']=real
        return self.gen(bits, c['locker_size'], c['lockers'], c['confidence'])

    def gen(self, bits, locker_size=43, lockers=1000000, confidence=None):
        length = self.hash().digest_size
        r = self.generate_sample(size=length/2)
        zeros = bytearray([0 for x in range(length/2)])
        check = zeros + r
        seeds = self.generate_sample(length=lockers, size=16)
        if confidence is None:
            pick_range = xrange(0, len(bits)-1)
        else:
            pick_range = self.confidence_range(confidence, list(xrange(0, len(bits)-1)))
            print(len(pick_range))
            if(len(pick_range) < 1024):
                return "Confidence range too small"
        positions = np.array([random.SystemRandom().sample(pick_range, locker_size) for x in range(lockers)])
        print(positions)
        p = []
        for x in range(lockers):
            v_i = np.array([bits[y] for y in positions[x]])
            seed = seeds[x]
            h = bytearray(hmac.new(seed, v_i, self.hash).digest())
            c_i = self.xor(check , h)
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
        finished = multiprocessing.Manager().list([None for x in range(num_processes)])
        processes = []
        for x in range(num_processes):
            p = multiprocessing.Process(target=self.rep_process, args=(bits, split[x], finished, x))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
        if(any(finished)):
            return next(item for item in finished if item is not None)
        return None

    def rep_process(self, bits, p, finished, process_id):
        counter = 0
        for c_i, positions, seed in p:
            v_i = np.array([bits[x] for x in positions])
            h = bytearray(hmac.new(seed, v_i, self.hash).digest())
            res = self.xor(c_i, h)
            if(self.check_result(res)):
                finished[process_id] = res[len(res)/2:]
                return
            counter += 1
            if(counter == 1000):
                if(not any(finished)):
                    counter = 0
                else:
                    return




    def check_result(self, res):
        return all(v == 0 for v in res[:len(res)/2])

    def xor(self, b1, b2):
        return bytearray([x ^ y for x,y in zip(b1, b2)])

    def generate_sample(self, length=0, size=32):
        if(length == 0):
            return bytearray([random.SystemRandom().randint(0, 255) for x in range(size)])
        else:
            samples = []
            for x in range(length):
                samples.append(bytearray([random.SystemRandom().randint(0, 255) for x in range(size)]))
            return samples

def read(path):
    with open(path, 'r') as f:
	return json.load(f)

if __name__ == '__main__':
    f1 = read("test_files/test.bin")
    f2 = read("test_files/diff.bin")
    fe = FuzzyExtractor()
    r, p = fe.gen_config(f1, "./fe.config")
    #cProfile.run("fe.gen(f1, lockers=1000)", sort='cumtime')
    #cProfile.run("fe.rep(f2, p)", sort="cumtime")

