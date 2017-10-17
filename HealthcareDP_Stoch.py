# -*- coding: utf-8 -*-
"""
Created on Mon Oct 03 13:30:42 2016

@author: John

When running the Program make sure that the input file is in the same directory as the program.
"""

import csv
import collections
import time
import json
import numpy as np

import DegenerationStrategy as degen
import HarvestStrategy as harvest
import LifeEnjoymentStrategy as le
import RegenerationStrategy as regen


DPState = collections.namedtuple('DPState', 'period, health, cash')
Investment = collections.namedtuple('Investment', 'healthExpenditure, lifeExpenditure, cashRemaining')

class HealthCareDP():
    #Init function. Declares global variables and parameters as well as caches.
    def __init__(self, state, numRounds, regenStrat, enjoymentStrat, degenStrat, harvestStrat, stochHitChance, stochHitSize):
        self.start = state
        self.regenStrat = regenStrat
        self.enjoymentStrat = enjoymentStrat
        self.degenStrat = degenStrat
        self.harvestStrat = harvestStrat
        self.numRounds = numRounds
        self.cache = {}
        self.EnumCache = {}
        self.StratCache = {}
        self.stochHitChance = stochHitChance
        self.stochHitSize = stochHitSize
        #[1,69,79]

    def HealthDegeneration(self, currentHealth, currentRound):
        return max(self.degenStrat.HealthDegeneration(currentHealth, currentRound),0)
    
    #Parameters: gamma, sigma, r
    def HealthRegained(self, investment):
        return max(self.regenStrat.HealthRegained(investment),0)

    #Paramaters: alpha, beta, mu
    def LifeEnjoyment(self, investment, currentHealth):
        return self.enjoymentStrat.LifeEnjoyment(investment, currentHealth)
        
    #Transition function. Moves from state X -> X', before investments.
    def Transition(self, state):
        nextPeriod = state.period + 1
        return DPState(nextPeriod,
                       self.degenStrat.HealthDegeneration(state.health, nextPeriod),
                       state.cash + self.harvestStrat.HarvestAmount(state.health))
    
    #Investment function. Simulates the investment phase for state X'
    def Invest(self, state, investment):
        endHealth = min(100, state.health + self.regenStrat.HealthRegained(investment.healthExpenditure))
        return (DPState(state.period,
                        endHealth,
                        investment[2]),
                self.enjoymentStrat.LifeEnjoyment(investment.lifeExpenditure, endHealth))
    
    #InvestmentEnum and StateEnum together generate every possible state that can be transitioned to from the provided state
    #StateEnum takes in every potential division of the available cash and calls Invest to generate every potential state
    #that can be achieved from the current state.
    def StateEnum(self, state):
        investments = self.InvestmentEnum(state.cash)
        allStateEnjoyments = []
        for investment in investments:
            newStateEnjoyment = self.Invest(state, investment)
            if newStateEnjoyment not in allStateEnjoyments:
                allStateEnjoyments.append(newStateEnjoyment)
        return allStateEnjoyments
        
    #InvestmentEnum generates every potential division of the available cash for StateEnum use.
    def InvestmentEnum(self, cash):
        potentialStates = []
        prev =-1
        if str(cash) not in self.EnumCache:
            for healthExpenditure in range(cash+1):
                hr = self.regenStrat.HealthRegained(healthExpenditure)
                if not hr == prev:
                    prev = hr
                    for lifeExpenditure in range(max(cash-healthExpenditure-20, 0), cash+1-healthExpenditure):
                        potentialStates.append(Investment(healthExpenditure, lifeExpenditure, cash-healthExpenditure-lifeExpenditure))
            self.EnumCache[str(cash)] = potentialStates
        return self.EnumCache[str(cash)]
    
    #Solve function calls itself recursively to enumerate every potential state of the environment. Once a state is seen it is
    #cached. The cache is checked before any state is evaluated to make sure that it has not been seen before.
    def Solve(self, currentState):
        try:
            newState = self.Transition(currentState[0])
            hitState = DPState(newState[0],max(newState[1]-self.stochHitSize,0),newState[2])
        except AttributeError:
            newState = self.Transition(currentState)
            hitState = DPState(newState[0],max(newState[1]-self.stochHitSize,0),newState[2])
        if newState.period > self.numRounds or newState.health <= 0:
            return (newState, 0,0)
        elif newState in self.cache:
            return self.cache[newState]
        else: 
            stateEnjoyments= self.StateEnum(newState)
            hitStateEnjoyments = self.StateEnum(hitState)
            highestReturn = DPState(0, 0, -1)
            hitStateHighestReturn = DPState(0, 0, -1)
            for (state, enjoyment) in stateEnjoyments:
                future = self.Solve(state)[2]
                totalValue = enjoyment + future
                if totalValue > highestReturn[1]:
                    highestReturn = (state, totalValue, round(enjoyment,1))
            for (state, enjoyment) in hitStateEnjoyments:
                future = self.Solve(state)[2]
                totalValue = enjoyment + future
                if totalValue > hitStateHighestReturn[1]:
                    hitStateHighestReturn = (state, totalValue, round(enjoyment,1))
            self.cache[newState] = (highestReturn, hitStateHighestReturn, (1-self.stochHitChance)*highestReturn[1] 
                + self.stochHitChance* hitStateHighestReturn[1])
        return (highestReturn, hitStateHighestReturn, (1-self.stochHitChance)*highestReturn[1] 
                + self.stochHitChance* hitStateHighestReturn[1])
    
    #Calls the solve function iteratively on the max returned state. This recreates the optimal path through the tree from
    #Whatever start state is provided all the way to completion. Note than in the returned strategy, the LE earned each round
    #is the difference between each period. The number shown is the remaining LE in the game that can be earned.    
    def FindStrat(self, state):
        cur = state
        strategy=[]
        for i in range(int(self.numRounds)):
            try:
                cur = self.Solve(cur[0][0])
            except:
                cur = self.Solve(cur)
            strategy.append(cur)
        return strategy
    
    def AnalyzeStrat(self, strategy, ID, life, outfile):
        alternate = []
        losses = []
        for i in strategy[:-1]:
            alternate.append(self.Solve(i[0]))
        for i in range(len(strategy[:-2])):
            losses.append(((alternate[i+1][1]+(strategy[i+1][1]-strategy[i+2][1]))-alternate[i][1])/float(alternate[0][1]))
        
        output = []
        for i in range(len(alternate)-1):
            output.append([alternate[i], strategy[i+1][0], (alternate[i+1][1]+(strategy[i+1][1]-strategy[i+2][1])), losses[i], np.cumsum(losses[:i+1])[i],strategy[i],(strategy[i][1]-strategy[i+1][1])])    
        with open(outfile,'a+',newline='') as f:
            fieldnames = ['ID','Lifetime','Period','Optimal Health','Optimal Cash on Hand', 'Remaining Max',
                          'Optimal Earnings This Period','Realized Health','Realized Cash on Hand','Current LE',
                          'Earned This Period','Remaining Available','% Loss','Accumulated Loss']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            for row in output:
               writer.writerow({'ID':ID,'Lifetime':life,'Period':row[0][0][0],'Optimal Health':row[0][0][1],'Optimal Cash on Hand':row[0][0][2], 'Remaining Max':int(row[0][1]),
              'Optimal Earnings This Period':row[0][2],'Realized Health':row[5][0][1],'Realized Cash on Hand':row[5][0][2],
              'Current LE':row[5][1],'Earned This Period':row[6],'Remaining Available':int(row[2]),'% Loss':'%.3f'%row[3],'Accumulated Loss':'%.3f'%row[4]})

def round_down(num, divisor):
    return num - (num%divisor)

def readInFile(data_file, size):
    with open(data_file) as f:    
        data = json.load(f)
    if size == 9:
        return [data[j:j+9] for j in range(0,len(data),9)]
    else:
        return [data[j:j+18] for j in range(0,len(data),18)]
    
def BatchRun(data, startState ,HCDP, outfile):
    with open(outfile,'w+') as f:
        fieldnames = ['ID','Lifetime','Period','Optimal Health','Optimal Cash on Hand', 'Remaining Max',
                      'Optimal Earnings This Period','Realized Health','Realized Cash on Hand','Current LE',
                      'Earned This Period','Remaining Available','% Loss','Accumulated Loss']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        f.close()
    for i in data:
        total = i[-1][2][1]
        pad = [k[2] for k in i]+[[[19,0,0],0]]
        for j in range(len(pad)):
            pad[j][1] = max(pad[-2][1] - pad[j][1],0)
        pad = [[startState,total]]+pad
        pad = [[DPState(val[0][0],val[0][1],val[0][2]),val[1]] for val in pad]
        HCDP.AnalyzeStrat(pad,i[0][0], i[0][1], outfile)

#Main function for file input and initing the program
def main():
    #print "Please enter the parameter filename. File must be in the same directory and name is case sensitive"
    #fileName = sys.argv[1]#
    fileName = input()
    lines = open(fileName, "r")
    params = []

    for i in lines:params.append(str.split(i));
    params = params[10:]
    for i in range(len(params)):
        try:
            params[i] = float(params[i][0])
        except:
            params[i] = json.loads(params[i][0])

    stochHitChance = .2
    stochHitSize = 50

    regenStrat = regen.RegenerationStrategy(params[2],params[3],params[4])
    enjoymentStrat= le.LifeEnjoymentStrategy(params[5],params[6],params[7],params[8])
    degenStrat18 = degen.DegenerationStrategy(7.625, 0.25)
    degenStrat9 = degen.DegenerationStrategy(15,1)
    harvestStrat18 = harvest.HarvestStrategy(46.811/.93622)
    harvestStrat9 = harvest.HarvestStrategy(93.622)
    startState = params[0] = DPState(params[0][0], params[0][1], params[0][2])

    HCDP = HealthCareDP(startState,params[1],regenStrat,enjoymentStrat, degenStrat18, harvestStrat18, stochHitChance, stochHitSize)
          
    start = time.time()
    output = []
    for val in [startState] + HCDP.FindStrat(startState):
        o = HCDP.Solve(val)
        print(o)
        output.append(o)
        print(o)
        
    end = time.time()
    print(end - start)
    
    #BatchRun(readInFile('EighteenRound_inFile.txt', 18)[:20],startState,HCDP, 'EighteenRoundOut.csv')

#    outputfilename = 'output_{}.csv'.format(fileName[:-4])
#    with open(outputfilename,'w+',newline='') as f:
#        fieldnames = ['Round','Health','CashonHand','LERemaining','LEEarned']
#        writer = csv.DictWriter(f, fieldnames=fieldnames)
#        writer.writeheader()
#        for row in output:
#            writer.writerow({'Round':row[0][0],'Health':row[0][1],'CashonHand':row[0][2],'LERemaining':int(row[1]),'LEEarned':int(row[2]) })
main()
