# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 10:48:37 2017

@author: murri101
"""

import itertools, ast, json

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
        for row in itertools.islice(csvFile, 1, None):
            values = list(row.strip('\n').split("\t"))
            for i, value in enumerate(values):
                nValue = ast.literal_eval(value)
                values[i] = nValue
                wholeLine = dict(zip(fieldnames, values[0]))
            cursor.append({k: wholeLine[k] for k in ('"newuniqueid"','"life"','"period"', '"health"', 
                                                   '"enjoymentbalance"','"accountbalance"','"healthinvestment"',
                                                   '"enjoymentinvestment"','"flat"','"social.life"','"social.health"',
                                                   '"retirement"','"periods"','"amountharvested"')})
    return cursor

def constructLifetime(data):
    life = []
    for i in data:
        life.append([i['"newuniqueid"'],i['"life"'],[[i['"period"'],
                    i['"health"'],i['"accountbalance"']-i['"healthinvestment"']-i['"enjoymentinvestment"']],i['"enjoymentbalance"']],
                    i['"flat"'],i['"social.life"'],i['"social.health"'],i['"retirement"'],i['"periods"'],i['"amountharvested"']])
    return life

def writeout(data, name):
    outfile = '{}_inFile.txt'.format(name)
    with open(outfile,'w') as outfile:
        json.dump(data, outfile)


f= 'experimentaldata_Session1-47_2016-05-09.csv'
formattedOutput= constructLifetime(writeCursor(f, getFieldnames(f)))
formattedOutput.sort(key=lambda x: (x[0],x[1],x[2]))
shortRound = [formattedOutput[j:j+9] for j in xrange(0,len(formattedOutput),9) if formattedOutput[j][7] == 9 if formattedOutput[j][3]==1 if formattedOutput[j][4]==0 if formattedOutput[j][5]==0 if formattedOutput[j][6]==0]
longRound = [formattedOutput[j:j+18] for j in xrange(0,len(formattedOutput),18) if formattedOutput[j][7] == 18 if formattedOutput[j][3]==1 if formattedOutput[j][4]==0 if formattedOutput[j][5]==0 if formattedOutput[j][6]==0]
groupedOutput = shortRound + longRound

shortRoundOut = [x[j][:3] for x in shortRound for j in xrange(len(x))]
longRoundOut = [x[j][:3] for x in longRound for j in xrange(len(x))]
writeout(shortRoundOut, 'NineRound')
writeout(longRoundOut, 'EighteenRound')

print len(groupedOutput)
print
print groupedOutput[0]