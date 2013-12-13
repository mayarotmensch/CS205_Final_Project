from mpi4py import MPI
from knapLP2 import *
from par_set import master_base, slave_base
from par_dff import master_dff, slave_dff
from par_depth import master_depth, slave_depth
from par_grand import master_grand, slave_grand
from bandbserial import serial_solve

if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    sizes = [20, 100, 175]
    #sizes = [250, 320, 400]
    #sizes = [400]
    par_times_grand = []
    par_times_base = []
    par_times_dff = []
    par_times_depth = []
    #ser_times = []
    nsolves = 1



    for size in sizes:
        if rank == 0:
            total_par_time_grand = 0.0
            total_par_time_base = 0.0
            total_par_time_dff = 0.0
            total_par_time_depth = 0.0
            #total_ser_time = 0.0
        for _ in xrange(nsolves):
            pr.generate_problem(size)

##################################### Run for par_grand (grand) #######################################################
            
            if rank == 0:
        
                #par_grand
                #print "Still going Grand"
                par_start_time_grand = MPI.Wtime()
                partotal_grand, parlist_grand = master_grand(comm)
                par_end_time_grand = MPI.Wtime()
                total_par_time_grand += (par_end_time_grand - par_start_time_grand)
                print 'end par', partotal_grand
                
            else:
                slave_grand(comm)
            
            comm.barrier()

##################################### Run for par_set (base) #######################################################

            if rank == 0:
                #print "Still going Base"                
                par_start_time_base = MPI.Wtime()
                partotal_base,parlist_base = master_base(comm)
                par_end_time_base = MPI.Wtime()
                total_par_time_base += (par_end_time_base - par_start_time_base)
                print 'end par', partotal_base
                
            else:
                slave_base(comm)

            comm.barrier()
            #print "----------"
##################################### Run for par_dff (dff) #######################################################

            if rank == 0:
                #print "Still going Dff"                
                par_start_time_dff = MPI.Wtime()
                partotal_dff,parlist_dff = master_dff(comm)
                par_end_time_dff = MPI.Wtime()
                total_par_time_dff += (par_end_time_dff - par_start_time_dff)
                print 'end par', partotal_dff
                
            else:
                slave_dff(comm)

            comm.barrier()

##################################### Run for par_depth (depth) #######################################################

            if rank == 0:
                #print "Still going Depth"               
                par_start_time_depth = MPI.Wtime()
                partotal_depth,parlist_depth = master_depth(comm)
                par_end_time_depth = MPI.Wtime()
                total_par_time_depth += (par_end_time_depth - par_start_time_depth)
                print 'end par', partotal_depth
                
            else:
                slave_depth(comm)

            comm.barrier()

##################################### Run for bandbserial (serial) #######################################################




            #if rank == 0:
                #print 'start ser'
                #ser_start_time = MPI.Wtime()
                #sertotal,serlist = serial_solve()
                #ser_end_time = MPI.Wtime()
                #total_ser_time += (ser_end_time - ser_start_time)
                #print 'end ser', sertotal


       
#################################################################################################

        if rank == 0:
           
            par_times_grand.append(total_par_time_grand/nsolves)
            par_times_base.append(total_par_time_base/nsolves)
            par_times_dff.append(total_par_time_dff/nsolves)
            par_times_depth.append(total_par_time_depth/nsolves)
            #ser_times.append(total_ser_time/nsolves)


        # What happens to the slaves?
        if rank == 0:
            print 'MPI size: %d' % comm.Get_size()
            print 'size', size
            print 'Avg Parallel times for Grand:', par_times_grand
            print 'Avg Parallel times for Base:', par_times_base
            print 'Avg Parallel times for Dff:', par_times_dff
            print 'Avg Parallel times for Depth:', par_times_depth
            #print 'Avg Serial times:', ser_times
            print "***************************** End of Iterations****************************************"
