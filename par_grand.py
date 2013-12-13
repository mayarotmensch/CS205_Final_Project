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
            return [newincumb], True  #returning a an integer solution
        else:
            return [newincumb,(bound, copy.deepcopy(constraints), decisionvar)], False  # not integer solution, append new child node 
    return [newincumb], False # either infeasible or bound is worse than incumbenttotal


#################################################


def master_grand(comm):
    status = MPI.Status()
    size = comm.Get_size()    
    workerq = set(xrange(1,size)) #set of all workers
    queue = Queue.PriorityQueue() #construct  of jobs que
    constraints = {} #a dictionary that we will populate with the constraints on fractional variables

    varvals, bound, decisionvar, statuslp = LP(constraints)# run the first LP on Master so we can start populating queue.
                                                            # we run this on master to avoid communication costs.

    if decisionvar == None: # will be true if either we found an integer solution or problem is infeasible. either way, we're done.
        for k in range(1,comm.Get_size()):# kill slaves
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
            if bound <= incumbenttotal:# if bound <= incumbenttotal, we can only get worse results so we prune the branch.
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


#def slave_grand(comm,TIME_COMM_SLAVE, TIME_ALL_SLAVE):  ## The commented code is this function is code we switched
                                                         ## in and out to to allow for more indepth timing.
def slave_grand(comm):
    status = MPI.Status()
    rank = comm.Get_rank()

    while True:
        #slave_start_time = MPI.Wtime() #start timing entire slave function
        #start_comm_slave0 = MPI.Wtime() #start timing communication
        data = comm.recv(source= 0, tag=MPI.ANY_TAG, status=status)
        #stop_comm_slave0 = MPI.Wtime() #stop timing communication
        #communication0 = stop_comm_slave0-start_comm_slave0

        if status.tag == KILL_TAG:  #if get kill tage --> die
	       return

        incumbenttotal, constraints, decisionvartobranch = data #unpack received data
        to_add = [] #list of nodes to pursue in next iteration.
        newincumb = None 
        
        res0, isValid0 = children(constraints, incumbenttotal, decisionvartobranch, newincumb, 1) #calculate first child node
        newincumb = res0[0] #update incumb
        
        res1, isValid1 = children(constraints, incumbenttotal, decisionvartobranch, newincumb, 0) #calculate second child node
        
        
        newincumb = res1[0] #update incumb

        if len(res0)>1: #if first child produces granchildren nodes--> pursue
            bound, constraints, decisionvartobranch = res0[1]

            res00, isValid0 = children(constraints, incumbenttotal, decisionvartobranch, newincumb, 1) #calculate first grandchild
            newincumb = res00[0]            
            if len(res00)>1:
                to_add.append(res00[1]) #append future nodes to pursue


            res01, isValid1 = children(constraints, incumbenttotal, decisionvartobranch, newincumb, 0) #calculate second grandchild
            newincumb = res01[0]            
            if len(res01)>1:
                to_add.append(res01[1]) #append future nodes to pursue

        if len(res1)>1: #if second child produces granchildren nodes--> pursue
            bound, constraints, decisionvartobranch = res1[1]

            res10, isValid0 = children(constraints, incumbenttotal, decisionvartobranch, newincumb, 1) #calculate third grandchild
            newincumb = res10[0]            
            if len(res10)>1:
                to_add.append(res10[1]) #append future nodes to pursue

            
            res11, isValid1 = children(constraints, incumbenttotal, decisionvartobranch, newincumb, 0) #calculate fourth grandchild
            newincumb = res11[0]            
            if len(res11)>1:
                to_add.append(res11[1]) #append future nodes to pursue

        #sendbacktomaster
        to_send_slave= (newincumb, to_add)
        #start_comm_slave1 = MPI.Wtime()#start time
        comm.send(to_send_slave, dest=0, tag=rank) #send information back to master
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
        #start = MPI.Wtime()#start time
        solution = master(comm)
        print "Heck yes", solution
        #stop = MPI.Wtime() 
        print "overall time", stop-start
    else:
        slave(comm)
'''

