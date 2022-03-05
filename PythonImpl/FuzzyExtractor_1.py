import json
import hmac
import cProfile
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
        c['confidence']['reals'] = real
        return self.gen(bits, c['locker_size'], c['lockers'], c['confidence'])

    def parse_config(self, config, real):
        with open(config, "r") as f:
            c = json.load(f)
        c['confidence']['reals'] = real
        return c['confidence']

    def gen(self, bits, locker_size=43, lockers=1000000, confidence=None):
        start = time.time()
        length = self.hash().digest_size

        rand_len = int(length/2)
        pad_len = length-rand_len
        r = self.generate_sample(size=rand_len)
        zeros = bytearray([0 for x in range(pad_len)])
        check = zeros + r
        seeds = self.generate_sample(length=lockers, size=16)
        if confidence is None:
            pick_range = range(0, len(bits)-1)
        else:
            pick_range = self.confidence_range(
                confidence, list(range(0, len(bits)-1)))
            print(len(pick_range))
            if(len(pick_range) < 1024):
                return "Confidence range too small"
        positions = np.array([random.SystemRandom().sample(
            pick_range, locker_size) for x in range(lockers)])
        p = []
        for x in range(lockers):
            v_i = np.array([bits[y] for y in positions[x]])
            seed = seeds[x]
            h = bytearray(hmac.new(seed, v_i, self.hash).digest())
            c_i = self.xor(check, h)
            p.append((c_i, positions[x], seed))
        print(time.time() - start, "gen")
        return r, p

    def confidence_range(self, confidence, bits):
        indeces = []
        for x in range(len(confidence['reals'])):
            r = confidence['reals'][x]
            if(not (r > confidence['positive_start'] and r < confidence['positive_end']) or (r < confidence['negative_start'] and r > confidence['negative_end'])):
                indeces.append(x)
        return np.delete(bits, indeces)

    def rep(self, bits, p):
        start = time.time()
        count = 0
        for c_i, positions, seed in p:
            v_i = np.array([bits[x] for x in positions])
            h = bytearray(hmac.new(seed, v_i, self.hash).digest())
            res = self.xor(c_i, h)
            if(self.check_result(res)):
                print("In repo found a match on iteration "+str(count))
                print(time.time() - start, "rep")
                key_len = int(len(res)/2)
                return res[key_len:]
            count += 1
        print(time.time() - start, "rep")
        return None

    def check_result(self, res):
        pad_len = int(len(res)-len(res)/2)
        return all(v == 0 for v in res[:pad_len])

    def xor(self, b1, b2):
        return bytearray([x ^ y for x, y in zip(b1, b2)])

    def generate_sample(self, length=0, size=32):
#        print("Length "+str(length)+", Size: "+str(size))
        randGen = random.SystemRandom()
        if(length == 0):
            return bytearray([randGen.randint(0, 255) for x in range(int(size))])
        else:
            samples = []
            for x in range(length):
                samples.append(
                    bytearray([randGen.randint(0, 255) for x in range(int(size))]))
            return samples


def read(path):
    with open(path, 'r') as f:
        return json.load(f)


def readFloatofFilter(path, filter):
    with open(path, "r") as f:
        data = json.load(f)
    return np.array(data[filter])


if __name__ == '__main__':
    fe = FuzzyExtractor()
#    f1 = read("0060043821zBmaHa5hx_code.bin")
#    fl = readFloatofFilter(
#        "/Iris/IrisCorpus/ND_merge/output/conv_vals/0060043821zBmaHa5hx_floats.json", 4)
#    r, p = fe.gen_config(fl, f1, "example.config")
    f1 = read("tests/test_files/test.bin")
    f2 = read("tests/test_files/diff.bin")
    fe = FuzzyExtractor()
    r, p = fe.gen(f1, lockers=10000)
    fe.rep(f1, p)
    fe.rep(f2, p)
    #cProfile.run("fe.gen(f1, lockers=1000)", sort='cumtime')
    #cProfile.run("fe.rep(f2, p)", sort="cumtime")
