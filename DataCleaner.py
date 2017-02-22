# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 10:48:37 2017

@author: murri101
"""

import itertools, ast

def getFieldnames(csvFile):
    """
    Read the first row and store values in a tuple
    """
    with open(csvFile) as csvfile:
        firstRow = csvfile.readlines(1)
        fieldnames = tuple(firstRow[0].strip('\n').split(","))
    return fieldnames

def writeCursor(csvFile, fieldnames):
    """
    Convert csv rows into an array of dictionaries
    All data types are automatically checked and converted
    """
    cursor = []  # Placeholder for the dictionaries/documents
    with open(csvFile) as csvFile:
        for row in itertools.islice(csvFile, 1, 1000):
            values = list(row.strip('\n').split("\t"))
            for i, value in enumerate(values):
                nValue = ast.literal_eval(value)
                values[i] = nValue
                wholeLine = dict(zip(fieldnames, values[0]))
            cursor.append({k: wholeLine[k] for k in ('"newuniqueid"','"life"','"period"', '"health"', '"enjoymentbalance"','"accountbalance"','"healthinvestment"','"enjoymentinvestment"')})
    return cursor

def constructLifetime(data):
    life = []
    for i in data:
        life.append([i['"newuniqueid"'],i['"life"'],[[i['"period"'],i['"health"'],i['"accountbalance"']-i['"healthinvestment"']-i['"enjoymentinvestment"']],i['"enjoymentbalance"']]])
    return life

f= 'experimentaldata_Session1-47_2016-05-09.csv'
formattedOutput= constructLifetime(writeCursor(f, getFieldnames(f)))
formattedOutput.sort(key=lambda x: (x[0],x[1]))
for i in formattedOutput:
    print i