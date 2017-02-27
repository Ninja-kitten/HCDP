# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 11:34:15 2017

@author: murri101
"""

import json
from pprint import pprint

def readInfile(data_file):
    with open(data_file) as f:    
        data = json.load(f)
    return [data[j:j+9] for j in xrange(0,len(data),9)][:100]
    
data = 'NineRound_inFile.txt'
out = readInfile(data)
for i in out:
   pprint(i[0][2][1])