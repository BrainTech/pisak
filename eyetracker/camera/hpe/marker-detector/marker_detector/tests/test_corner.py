'''
Created on 2010-06-25

@author: Macias
'''
import unittest
from corner import Corner
from vectors import vector, vectorAngle, length, rotateVec


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_append_candidates(self):
        c = Corner([(0,0),(0,1),(1,1)], 1, (0,0),imgtime=1)
        conts = [(1,1),(2,2),(3,2),(2,3)]
        data=[conts,list(reversed(conts)),\
              list(reversed(conts[2:]+conts[:2])),\
              conts[2:]+conts[:2]]
        cr= (0,0,5,6)
        for i in range(4):            
            result = [] 
            c._append_candidates_from_conts(cr, result, data[i],0)
            self.assertTrue(len(result)==1,result)
            cor = result[0]
            self.assertTrue(cor.p==(2,3) and cor.prev==(3,2),(cor.p,cor.prev))
            
    def test_get_prediction_vector(self):
        points = [(1,5),(3,0),(5,6)]
        v1 = vector(points[1],points[0])
        v2 = vector(points[1],points[2])
        angle = vectorAngle(v1,v2)
        c= Corner(points,1,imgtime=1)
        c1= Corner(points,1,imgtime=1)
        ans= c.get_prediction_vector(True, c1)
        self.assertAlmostEqual(ans[0],v1[0],6)
        self.assertAlmostEqual(ans[1],v1[1],6)
        ans= c.get_prediction_vector(False, c1)
        self.assertAlmostEqual(ans[0],v2[0],6)
        self.assertAlmostEqual(ans[1],v2[1],6)
        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_append_candidates']
    unittest.main()