from pulp import *
import random
from math import *
from mpi4py import MPI
import Queue
from knapLP2 import LP
import copy



KILL_TAG = 1
WORK_TAG = 0

####################################
'''
The children function takes in:
constraints: dictionary of inherited constraints from former problem
incumbenttotal: the best incumbenttotal result that we last received from the master
decisionvartobranch: the fractional variable on which we will branch
newincumb: the best incumbenttotal and incumbentlist result that is most up to date on the slave
const_number: binary variable. determines whether we set fractional variable to 0 or 1.

Output:
[newincumb]
True/False to tell us whether the result is an integer solution or not.

'''
def children(constraints, incumbenttotal, decisionvartobranch, newincumb, const_number):
    if decisionvartobranch != None:
        constraints[decisionvartobranch] = const_number
    varvals, bound, decisionvar, statuslp = LP(constraints)
    if statuslp != 'Infeasible' and bound > incumbenttotal: #true if result both feasible as well as better than last incumbenttotal
        if decisionvar == None:  #if integer solution   
            if newincumb == None:	# if we don't have a value for newincumb yet
                newincumb = bound, varvals 
            elif bound > newincumb[0]:  # if our new value is better than the current new incumb
                newincumb = bound, varvals
            return [newincumb], True #we get an integer solution
        else:
            return [newincumb,(bound, copy.deepcopy(constraints), decisionvar)], False  # not integer solution, append new child
    return [newincumb], False  # either infeasible or bound is worse than incumbenttotal



####################################
'''
A recursive function that traverses a tree depth first, in each branching choosing the more promising node
until it either finds an integer solution or reaches an infeasible configuration.
'''

def depth_first(to_add, incumbenttotal, (bound, constraints, decisionvartobranch)):
    newincumb = None
    incumbentlist = None

    res0, isValid0 = children(constraints, incumbenttotal, decisionvartobranch, newincumb, 1) #calculate first child node
    newincumb = res0[0] #update newincumb

    res1, isValid1 = children( constraints, incumbenttotal, decisionvartobranch, newincumb, 0) #calculate second child node

 
    
    if len(res0)>1 and len(res1)>1: #true is both nodes produce more future nodes to pursue.
        #both res0 and res1 are in the form: [newincumb,(bound, copy.deepcopy(constraints), decisionvar)] OR
        if res0[1][0] < res1[1][0]:
            
            #append other
            to_add.append(res0[1])      

            #run more promising branch
            newincumb = depth_first(to_add, incumbenttotal ,res1[1])
            
        else:
            #append other
            to_add.append(res1[1])

            #run more promising branch 
            newincumb = depth_first(to_add, incumbenttotal, res0[1])

    # res1 is either infeasible or an integer result.
    elif len(res0)>1: 
        #if res1 is a valid solution
        if isValid1:
            to_add.append(res0[1])
            newincumb = res1[0]
        else:
            newincumb = depth_first(to_add, incumbenttotal,res0[1])

    elif len(res1)>1:
        #if res1 is a valid solution
        if isValid0:
            to_add.append(res1[1])
            newincumb = res0[0]
        else:
            newincumb = depth_first(to_add, incumbenttotal,res1[1])

    elif isValid0 and isValid1: #finds both valud solutions
        if res0[0][0] > res1[0][0]: # compare new incumbents from both paths
            newincumb = res0[0]
        else:
            newincumb = res1[0]
    
    return newincumb
    '''
    if newincumb !=None:
        incumbenttotal, incumbentlist = newincumb
        #print "newtotal", incumbenttotal
    #return newincumb
    if incumbentlist != None:
        #print "newtotal@@@@@", incumbenttotal    
        return incumbenttotal, incumbentlist
    else:
        return None
        
    '''




#################################################3

def master_dff(comm):
    status = MPI.Status()
    size = comm.Get_size() 
    workerq = set(xrange(1,size) ) #set of all workers
    queue = Queue.PriorityQueue() #construct  of jobs que
    constraints = {} #a dictionary that we will populate with the constraints on fractional variables

    varvals, bound, decisionvar, statuslp = LP(constraints) # run the first LP on Master so we can start populating queue.
                                                            # we run this on master to avoid communication costs.

    to_add = []
    incumbenttotal = 0.0
    newincumb = depth_first(to_add, incumbenttotal, (0, constraints, None))

    if decisionvar == None: # will be true if either we found an integer solution or problem is infeasible. either way, we're done.
        for k in range(1,comm.Get_size()): # kill slaves
            comm.send('die, peasant!', dest=k, tag=KILL_TAG)
        return bound, varvals #return the solution found

    #prepare information to send to slaves
    info = (bound, constraints,decisionvar)
    queue.put((1.0/info[0],info))
    incumbenttotal = 0
    incumbentlist = []

    
    # While we still have work to assign or while of the slaves is still doing work
    while not queue.empty() or len(workerq) < (size-1): 

        # While we still have work to assign and have free workers -->assign work.
        while not queue.empty() and len(workerq) > 0:   
         
            next = queue.get()
            _,(bound, constraints, decisionvar) = next
            if bound <= incumbenttotal: # if bound <= incumbenttotal, we can only get worse results so we prune the branch.
                continue
            #send relevant information to slave
            to_send = (incumbenttotal, constraints, decisionvar)
            comm.send(to_send, dest=workerq.pop(), tag=WORK_TAG)
           
        if len(workerq) < (size-1): #while there are still slaves that haven't return. prepare to receive.
            newincumb, to_add = comm.recv(source= MPI.ANY_SOURCE, tag = MPI.ANY_TAG , status=status)
            workerq.add(status.source) #add free slave to worker queue

            if newincumb !=None: #if we found a better newincumb, update
                incumbenttotal, incumbentlist = newincumb

            for item in to_add: #add new nodes to queue
                queue.put((1.0/item[0],item))

    for k in range(1,comm.Get_size()): #at the end of branching, kill slaves
        comm.send('die, peasant!', dest=k, tag=KILL_TAG)


    #return solution
    return incumbenttotal, incumbentlist
    
######################################################
#def slave_dff(comm,TIME_COMM_SLAVE, TIME_ALL_SLAVE):  ## The commented code is this function is code we switched
                                                         ## in and out to to allow for more indepth timing.

def slave_dff(comm):
    status = MPI.Status()
    rank = comm.Get_rank()

    while True:
        #slave_start_time = MPI.Wtime()
        #start_comm_slave0 = MPI.Wtime()#start time
        data = comm.recv(source= 0, tag=MPI.ANY_TAG, status=status)
        #stop_comm_slave0 = MPI.Wtime()#start time
        #communication0 = stop_comm_slave0-start_comm_slave0

        if status.tag == KILL_TAG:
	       return

        incumbenttotal, constraints, decisionvartobranch = data
        to_add = []

        newincumb = None
        res0, isValid0 = children(constraints, incumbenttotal, decisionvartobranch, newincumb, 1) #***********
        newincumb = res0[0]
        if len(res0)>1:
            to_add.append(res0[1]) 
        res1, isValid1 = children(constraints, incumbenttotal, decisionvartobranch, newincumb, 0)
        newincumb = res1[0]
        if len(res1)>1:
            to_add.append(res1[1]) 
            
        #sendbacktomaster
        to_send_slave= (newincumb, to_add)
        #start_comm_slave1 = MPI.Wtime()#start time
        comm.send(to_send_slave, dest=0, tag=rank)
        #stop_comm_slave1 = MPI.Wtime()#stop time
        #communication1 = stop_comm_slave1 - start_comm_slave1
        #TIME_COMM_SLAVE.append((communication0+communication1))
        
        #slave_stop_time = MPI.Wtime()
        #TIME_ALL_SLAVE.append(slave_stop_time-slave_start_time - (communication0+communication1))

'''
if __name__ == '__main__':
    comm = MPI.COMM_WORLD

    # global information should be:
    # capacity
    # values
    # weights
    
   
    if comm.Get_rank() == 0:
        start = MPI.Wtime()#start time
        solution = master(comm)
        print "Heck yes", solution
        stop = MPI.Wtime() 
        print "overall time", stop-start
    else:
        slave(comm)
'''

