import json
import hmac
import cProfile
import numpy as np
import random
import string
import time
from hashlib import sha512


def RPIGen(w, hash=sha512):
    omega = []
    c = []
    length = hash().digest_size
    for wi in w:
        xi = generate_random(length/2)
        seed = generate_random(16)
        zeros = bytearray([0 for x in range(length/2)])
        lock = bytearray(hmac.new(seed, wi, hash).digest())
        ci = xor(lock, (zeros+xi))
        c.append((ci, seed))
        omega.append(xi)
    return c, omega


def RPIRep(w, c, hash=sha512):
    length = hash().digest_size
    n = s = len(w)
    omega = []
    for i in range(s):
        for j in range(n):
            cj, seed = c[j]
            h = bytearray(hmac.new(seed, w[i], hash).digest())
            xi = xor(cj, h)
            res = check_result(xi)
            if(not res and j == (n-1)):
                omega.append(generate_random(length/2))
            elif(not res and j != (n-1)):
                continue
            else:
                c.pop(j)
                n -= 1
                omega.append(xi[len(xi)/2:])
                break
    return omega


def xor(b1, b2):
    return bytearray([x ^ y for x, y in zip(b1, b2)])


def generate_random(length):
    return bytearray([random.SystemRandom().randint(0, 255) for x in range(length)])


def check_result(res):
    return all(v == 0 for v in res[:len(res)/2])


if __name__ == '__main__':
    w = ["1", "0", "1", "0", "1", "0"]
    r = ["1", "0", "1", "0", "1", "0"]
    c, omega = gen(w)
    omega2 = rep(r, c)
    print(omega)
    print(omega2)
