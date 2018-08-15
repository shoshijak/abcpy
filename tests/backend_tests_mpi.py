import unittest
from mpi4py import MPI
from abcpy.backends import BackendMPI,BackendMPITestHelper
from tests.backend_tests import BackendTests


def setUpModule():
    '''
    If an exception is raised in a setUpModule then none of 
    the tests in the module will be run. 
    
    This is useful because the slaves run in a while loop on initialization
    only responding to the master's commands and will never execute anything else.

    On termination of master, the slaves call quit() that raises a SystemExit(). 
    Because of the behaviour of setUpModule, it will not run any unit tests
    for the slave and we now only need to write unit-tests from the master's 
    point of view. 
    '''
    global rank,backend_mpi
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    backend_mpi = BackendMPI()

class MPIBackendTests(BackendTests, unittest.TestCase):
    def setUp(self):
        self.backends = [backend_mpi]
    
    def test_parallelize(self):
        data = [0]*backend_mpi.size
        pds = backend_mpi.parallelize(data)
        pds_map = backend_mpi.map(lambda x: x + MPI.COMM_WORLD.Get_rank(), pds)
        res = backend_mpi.collect(pds_map)

        for master_index in backend_mpi.master_node_ranks:
            self.assertTrue(master_index not in res,"Node in master_node_ranks performed map.")


    def test_pds_delete(self):

        def check_if_exists(x):
            obj = BackendMPITestHelper()
            return obj.check_pds(x)

        data = [1,2,3,4,5]
        pds = backend_mpi.parallelize(data)

        #Check if the pds we just created exists in all the slaves(+master)

        id_check_pds = backend_mpi.parallelize([pds.pds_id]*5)
        pds_check_result = backend_mpi.map(check_if_exists, id_check_pds)
        self.assertTrue(False not in backend_mpi.collect(pds_check_result),"PDS was not created")

        #Delete the PDS on master and try again
        del pds
        pds_check_result = backend_mpi.map(check_if_exists,id_check_pds)

        self.assertTrue(True not in backend_mpi.collect(pds_check_result),"PDS was not deleted")


    def test_bds_delete(self):
        
        def check_if_exists(x):
            obj = BackendMPITestHelper()
            return obj.check_bds(x)

        data = [1,2,3,4,5]
        bds = backend_mpi.broadcast(data)

        #Check if the pds we just created exists in all the slaves(+master)
        id_check_bds = backend_mpi.parallelize([bds.bds_id]*5)
        bds_check_result = backend_mpi.map(check_if_exists, id_check_bds)
        self.assertTrue(False not in backend_mpi.collect(bds_check_result),"BDS was not created")

        #Delete the PDS on master and try again
        del bds
        bds_check_result = backend_mpi.map(check_if_exists,id_check_bds)
        self.assertTrue(True not in backend_mpi.collect(bds_check_result),"BDS was not deleted")


    def test_function_pickle(self):
        def square(x):
            return x**2

        class staticfunctest:
            @staticmethod 
            def square(x):
                return x**2

        class nonstaticfunctest:
            def square(self,x):
                return x**2

        data = [1,2,3,4,5]
        expected_result = [1,4,9,16,25]
        pds = backend_mpi.parallelize(data)


        pds_map1 = backend_mpi.map(square,pds)
        pds_res1 = backend_mpi.collect(pds_map1)
        self.assertTrue(pds_res1==expected_result,"Failed pickle test for general function")


        pds_map2 = backend_mpi.map(lambda x:x**2,pds)
        pds_res2 = backend_mpi.collect(pds_map2)
        self.assertTrue(pds_res2==expected_result,"Failed pickle test for lambda function")


        pds_map3 = backend_mpi.map(staticfunctest.square,pds)
        pds_res3 = backend_mpi.collect(pds_map3)
        self.assertTrue(pds_res3==expected_result,"Failed pickle test for static function")


        obj = nonstaticfunctest()
        pds_map4 = backend_mpi.map(obj.square ,pds)
        pds_res4 = backend_mpi.collect(pds_map4)
        self.assertTrue(pds_res4==expected_result,"Failed pickle test for non-static function")
