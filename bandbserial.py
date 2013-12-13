import Queue
from knapLP2 import LP
#from knapLP import LP
import copy
import time

# This function processes the child from a given set of constraints,
# it adds grandchildren to the queue and updates incumbents as needed
def process_node(queue, incumbenttotal, incumbentlist, constraints):
    constraints = copy.deepcopy(constraints)
    varvals, bound, decisionvar, status = LP(constraints)
    if status == 'Infeasible':
        return incumbenttotal, incumbentlist
    if bound > incumbenttotal:
        if decisionvar == None:
            incumbenttotal, incumbentlist = bound, varvals
        else:
            queue.put((bound, constraints, decisionvar))
    return incumbenttotal, incumbentlist


# This actually handles the dolving of the problem. It is generic to whatever
# problem is defined around LP. It assumes decision variables are binary
# and must be forced to either 0 or 1
def serial_solve():
    queue = Queue.Queue()
    
    # run the initial problem
    constraints = {}
    varvals, bound, decisionvar, status = LP(constraints)

    # return solution if found trivially
    if decisionvar == None:
        return bound, varvals
    
    queue.put((bound, constraints, decisionvar))

    incumbenttotal = 0
    incumbentlist = []

    # go through queue, processing as long as there are nodes to process
    # note that processing can and will add to the queue as a side effect
    while not queue.empty():
        #print 'still going SER'
        bound, constraints, decisionvar = queue.get()
        # This is the key bounding. Algorithm doesn't pursue guaranteed unfruitful branches
        if bound <= incumbenttotal:            
            continue

        constraints[decisionvar] = 1
        incumbenttotal, incumbentlist = process_node(queue, incumbenttotal, incumbentlist, constraints)

        constraints[decisionvar] = 0
        incumbenttotal, incumbentlist = process_node(queue, incumbenttotal, incumbentlist, constraints)

    #THE SOLUTION:
    return incumbenttotal, incumbentlist


if __name__ == '__main__':
    start = time.time()    
    ftotal,flist= serial_solve()
    stop = time.time()
    print 'ser time', stop-start
    print ftotal
    print flist

    




