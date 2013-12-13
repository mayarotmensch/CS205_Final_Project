from pulp import *
import numpy as np
import random
from math import *
import time


#seed = np.random.randint(0,100000)
seed=43445
np.random.seed(seed)
# VALUE = np.random.randint(1,15,250)
# WEIGHT = np.random.randint(1,15,250)
# CAPACITY = 1000 #10 


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
    
    #print "Constraints:", CONST.items()
    for i,n in CONST.items():
        #print "i",i,n
        prob += X[i] == n

    #print prob

    status = prob.solve()
    statusmessage = LpStatus[status]
    #print statusmessage

    '''
    # use this to return object 
    return prob.variables()
    '''

    #use to return simple list of values:
    variables = []
    var = None
    for i in ITEMS:
        v = value(X[i])
        if (v != 1.0 and v !=0.0):
            var = i
    #for v in prob.variables():
    #    if (v.varValue != 1.0 and v.varValue !=0.0):
    #        print v.varValue
    #        #print v
    #        var = int(str(v)[2:]) 
    #    print 'asd', v
       	variables.append(v)

    """     Returns:
            - list of variable values,
            - vaalue of objective function
            - decision variable with fractional value (doesn't deal with multiple fractional values yet)"""
    #print type(var)
    #print '~', variables, value(prob.objective), var, statusmessage
    return variables, value(prob.objective), var, statusmessage

 
if __name__ == '__main__':
    #input:
    #VALUE = [7, 5, 3, 2, 2]
    #WEIGHT = [7, 5, 3, 2, 2]
    #CAPACITY = 10 
    #CONST = {1:0,2:1}
    #either 1 or 0 depending on branching
    #BSTATUS = 0

    #run function
    pr.generate_problem(25)
    start = time.time()  
    for ii in range(0,100):
        result = LP({})
    end = time.time()    
    print result
    print (end-start)/100.0



    '''
    #use if you choose to use first return statement (with object)
    for v in something:
       	print v.varValue
    '''
    

