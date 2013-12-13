from pulp import *
import numpy as np
import random
from math import *
from mpi4py import MPI
import Queue
from knapLP2 import LP
import copy


KILL_TAG = 1
WORK_TAG = 0

def master_base(comm):
    status = MPI.Status()
    size = comm.Get_size()    
    workerq = set(xrange(1,size)) #set of all workers
    queue = Queue.PriorityQueue() #construct  of jobs que
    constraints = {} #a dictionary that we will populate with the constraints on fractional variables

    varvals, bound, decisionvar, statuslp = LP(constraints) # run the first LP on Master so we can start populating queue.
                                                            # we run this on master to avoid communication costs.
    
    if decisionvar == None: # will be true if either we found an integer solution or problem is infeasible. either way, we're done.
        for k in range(1,comm.Get_size()): # kill slaves
            comm.send('die, peasant!', dest=k, tag=KILL_TAG)
        return bound, varvals #return the solution found

    #prepare information to send to slaves
    info = (bound, constraints,decisionvar)
    queue.put((1.0/info[0], info))
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
            to_send = (constraints, incumbenttotal, decisionvar)      
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


#def slave_base(comm, TIME_COMM_SLAVE, TIME_ALL_SLAVE): ## The commented code is this function is code we switched
                                                   ## in and out to to allow for more indepth timing.
def slave_base(comm):
    
    status = MPI.Status()
    rank = comm.Get_rank()

    while True:
        #slave_start_time = MPI.Wtime() #start timing entire slave function
        #start_comm_slave0 = MPI.Wtime() #start timing communication 
        data = comm.recv(source= 0, tag=MPI.ANY_TAG, status=status)
        #stop_comm_slave0 = MPI.Wtime() #stop timing communication 
        #communication0 = stop_comm_slave0-start_comm_slave0
 
        if status.tag == KILL_TAG: #if get kill tage --> die
	       return

        constraints, incumbenttotal, decisionvartobranch = data #unpack received data
        to_add = [] #list of nodes to pursue in next iteration.
        newincumb = None 


        # branch on fractional decision variable
        constraints[decisionvartobranch] = 1
        varvals, bound, decisionvar, statuslp = LP(constraints)
        if statuslp != 'Infeasible' and bound > incumbenttotal:
            if decisionvar == None:    # will be true if either we found an integer solution or problem is infeasible
                newincumb = bound, varvals
            else:
                to_add.append((bound, copy.deepcopy(constraints), decisionvar)) #add node to list


        constraints[decisionvartobranch] = 0
        varvals, bound, decisionvar, statuslp = LP(constraints)
        if statuslp != 'Infeasible' and bound > incumbenttotal:
            if decisionvar == None: #this is same as isValidSoln
                if newincumb == None: # will be true if either we found an integer solution or problem is infeasible	        
                    newincumb = bound, varvals
                elif bound > newincumb[0]: #check against solution we get on first processed node
                    newincumb = bound, varvals
            else:
                to_add.append((bound, copy.deepcopy(constraints), decisionvar))#add node to list

        #sendbacktomaster
        to_send_slave= (newincumb, to_add)
        #start_comm_slave1 = MPI.Wtime() #start timing communication 
        comm.send(to_send_slave, dest=0, tag=rank)
        #stop_comm_slave1 = MPI.Wtime()  #start timing communication 
        #communication1 = stop_comm_slave1 - start_comm_slave1
        #TIME_COMM_SLAVE.append((communication0+communication1))
        
        
        #slave_stop_time = MPI.Wtime() #start timing entire slave function
        #TIME_ALL_SLAVE.append(slave_stop_time-slave_start_time - (communication0+communication1)) #calculate total computation time


'''
if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    
    # global information should be:
    # capacity
    # values
    # weights
    
   
    if comm.Get_rank() == 0:
        #start1 = MPI.Wtime()#start time
        solution = master(comm)
        print "Heck yes", solution
        #stop1 = MPI.Wtime() 
        #print "overall time", stop1-start1
    else:
        slave(comm, TIME_COMM_SLAVE)


    print TIME_COMM_SLAVE, "RANK", comm.Get_rank()
'''
