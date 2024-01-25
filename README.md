# CompFE
Computational Fuzzy Extractors
 

Copyright 2024  Sohaib Ahmad, Luke Demarest, Benjamin Fuller, and Sailesh Simhadri

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Files:
* bh_iris.ipynb Trains feature extractor
* PythonImpl/FuzzyExtractor.py legacy implementation of Canetti et al. fuzzy extractor sample-then-lock from https://eprint.iacr.org/2014/243
* PythonImpl/RPISetDifference.py implementation of set difference construction from https://eprint.iacr.org/2016/1100
* Statistics folder is used to understand quality of zeta sampling algorithm.
* subsets contains selected subsets for mid and high security parameters.
* `GenerateSubsets.py` is a file that generates selected subsets and can be used as follows: `python3 GenerateSubsetsNewFE.py [subset size] ['simple' or 'complex'] [alpha] [number of subsets] [output file name]` and will be looking for a feature vector folder (which should be provided by the user) with each class having a folder and each vector having a file with a distinct filename that begins with the class name and a confidence file where each index has a line documenting the agreement with inter and intra class comparisons. Optionally, you may manually exclude indices from the complex confidence selection by providing indices in the bad_list variable. (Modification to `read_complex_conf` will be necessary to match your file structure and folder structure.)
* `TarTest.py` is the test that calculates the entropy of a sample of your subsets and should be used as follows" `python3 EntropyTest.py [subset size or entropy threshold] [number of subsets] [subsets filename]` which takes as input the selected subsets from `GenerateSubsets.py`. See above for modifications.
* `EntropyTest.py` is the test that calculates the TAR for your subsets and should be used as follows: `python3 EntropyTest.py [subset size] [number of subsets] [subsets filename] [subsets to test] [starting index]`. See above for modifications. Note this can take a very long time even parallelized which is why we offer a starting index. 
