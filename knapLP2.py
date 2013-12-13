from pulp import *
import numpy as np
import random
from math import *
import time


seed=43445
np.random.seed(seed)


class problem:
    def generate_problem(self,size):
        self.VALUE = np.random.randint(1,15,size)
        self.WEIGHT = np.random.randint(1,15,size)
        self.CAPACITY = int(size*4)

pr = problem()

def LP(CONST): 
    
    ## Sets ##
    ITEMS = range(len(pr.VALUE))

    ## Paremeters ##
    WEIGHTS = {k:v for k,v in enumerate(pr.WEIGHT)}
    VALUES = {k:v for k,v in enumerate(pr.VALUE)}
    ITEMS = range(len(pr.VALUE))
 
    ## Decision Variables ##
   
    X = LpVariable.dicts("X", ITEMS, 0, 1)


    #--------------- The Problem ------------------#

    prob = LpProblem("Knapsack", LpMaximize)


    prob += lpSum(VALUES[i]*X[i] for i in ITEMS)

    prob += lpSum(WEIGHTS[i]*X[i] for i in ITEMS) <= pr.CAPACITY

    for i in ITEMS: #(not sure this is needed. but helps with percision error)
	    prob += X[i] >=0

    #add constraints according to branching
    
    for i,n in CONST.items():
        prob += X[i] == n


    status = prob.solve()
    statusmessage = LpStatus[status]
    #print statusmessage


    #use to return simple list of values:
    variables = []
    var = None
    for i in ITEMS:
        v = value(X[i])
        if (v != 1.0 and v !=0.0):
            var = i
       	variables.append(v)

    """     Returns:
            - list of variable values,
            - vaalue of objective function
            - decision variable with fractional value (doesn't deal with multiple fractional values yet)"""
    return variables, value(prob.objective), var, statusmessage

 
if __name__ == '__main__':

    #run function
    pr.generate_problem(25)
    start = time.time()  
    for ii in range(0,100):
        result = LP({})
    end = time.time()    
    print result
    print (end-start)/100.0



    

