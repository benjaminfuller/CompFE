from FuzzyExtractor_1_parallel import FuzzyExtractor
import cProfile
import json
import unittest


class TestFuzzyExtractor(unittest.TestCase):

    def setUp(self):
        self.fe = FuzzyExtractor()

    def read(self, path):
        with open(path, 'r') as f:
            res = json.load(f)
            res = ''.join([str(x) for x in res])
            return res

    def test_same(self):
        f1 = self.read("test_files/test.bin")
        r, p = self.fe.gen(f1, lockers=100000)
        res = self.fe.rep(f1, p)
        self.assertEqual(r, res)

    def test_same_eye(self):
        f1 = self.read("test_files/test.bin")
        f2 = self.read("test_files/same.bin")
        r, p = self.fe.gen(f1, lockers=100000)
        res = self.fe.rep(f2, p)
        self.assertEqual(r, res)

    def test_diff(self):
        f1 = self.read("test_files/test.bin")
        f2 = self.read("test_files/diff.bin")
        r, p = self.fe.gen(f1, lockers=100000)
        res = self.fe.rep(f2, p)
        self.assertIsNone(res)


if __name__ == '__main__':
    unittest.main()
    #suite = unittest.TestLoader().discover('.')
    # def runtests():
    #    unittest.TextTestRunner().run(suite)
    # cProfile.run('runtests()',sort='cumtime')
