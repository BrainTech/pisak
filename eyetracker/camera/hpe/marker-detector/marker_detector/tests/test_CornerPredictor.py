'''
Created on 2010-06-14

@author: Macias
'''
import unittest
import cv
import random
from corner_predictor import CornerPredictor
from vectors import *
from corner import Corner
from utils import standarize_contours
import debug as db
class CornerPredictorTest(unittest.TestCase):


    def setUp(self):
        size = 100
        offset = 20
        so = size - offset
        angle = 45
        move = (0, 0)
        scale = 0.5
        center = (size / 2, size / 2)
        time = 1
        points = [(offset, offset), (so, offset), (so, so), (offset, so)]
        img = cv.CreateImage((size, size), 8, 1)
        cv.SetZero(img)
        points = rotate_points(points, center, angle)
        corners = [Corner(points, 0), Corner(points, 1), Corner(points, 2), Corner(points, 3)]
        npoints = rotate_points(points, center, 3)
        npoints = map(lambda x:add((2, 2), int_point(x)), npoints)
        npoints = standarize_contours(npoints)
        ncorners = [Corner(npoints, 0,imgtime=1), Corner(npoints, 1,imgtime=1), Corner(npoints, 2,imgtime=1), Corner(npoints, 3,imgtime=1)]
        for i, cor in enumerate(ncorners):
            cor.compute_change(corners[i])
        
        
        
                
        self.points = npoints
        self.old_corners = corners
        self.corners = ncorners
        self.size = size
        cv.AddS(img, 255, img)
        self.draw_img = img
        self.timg = cv.CloneImage(img)
        self.tmp_img = cv.CloneImage(img)
        pass


    def tearDown(self):
        pass

    def _prepare_corners(self, npoints):
        L = len(npoints)
        ncorners = []
        for i, point in enumerate(npoints):
            prev = vector(point, npoints[(i - 1 + L) % L])
            next = vector(point, npoints[(i + 1) % L])
            #prev= add(point,prev,3.0/random.randint(3,int(length(prev))))
            #next = add(point,next, 3.0/random.randint(3,int(length(next))))
            #prev=(int(prev[0])+random.randint(-1,1),int(prev[1])+random.randint(-1,1))
            #next = (int(next[0]+random.randint(-1,1)),int(next[1])+random.randint(-1,1))
            prev = add(point, prev, 0.3)
            next = add(point, next, 0.3)
            prev = (int(prev[0]), int(prev[1]))
            next = (int(next[0]), int(next[1]))
            
            ncorners.append(Corner([prev, point, next], 1,imgtime=2))
        return ncorners
    
    def _test_improve_corners(self, a, b):
        cv.FillConvexPoly(self.draw_img, self.points, (255, 255, 255))
       # cv.Circle(self.draw_img, (75,30), 20, (0,0,0),4)
        ncorners = self._prepare_corners(self.points)
        CP = CornerPredictor(self.corners, 1, self.draw_img, self.timg,self.tmp_img)
        ncorners[a] = None
        ncorners[b] = None
        corners = CP._improve_corners(ncorners)
        for i in filter(lambda x: (x <> a and x <> b), range(4)):
            ea = r2d(self.corners[i].angle)
            print '-----',ncorners[i].prev,ncorners[i].p, ncorners[i].next, corners[i].prev, corners[i].next 
            na = r2d(ncorners[i].angle)
            ra = r2d(corners[i].angle)
            self.assertTrue(abs(ea - ra) <= abs(ea-na), 'Angle of [%d] not improved: \
                                        expected %f received %f previous %f' % (i, ea, ra, na))
            ea = r2d(self.corners[i].rotation)
            na = r2d(ncorners[i].rotation)
            ra = r2d(corners[i].rotation)
            self.assertTrue(abs(ea - ra) <= abs(ea-na) , 'rotation of [%d] not improved: \
                                        expected %f received %f previous %f' % (i, ea, ra, na))                            
    def test_improve_corners_on_side(self):
        self._test_improve_corners(0, 1)
        self._test_improve_corners(1, 2)
        self._test_improve_corners(2, 3)
        self._test_improve_corners(3, 0)
    def test_improve_corners_accross(self):
        self._test_improve_corners(0, 2)
        self._test_improve_corners(1, 3)
    def test_solve_linear(self):
        v1=[1,0]
        v2=[0,1]
        p1=[2,2]
        p2=[0,0]
        self.assertEqual(solve_linear(v1, v2, p1, p2),(-2,2))
        v1=[0,1]
        v2=[1,0]
        self.assertEqual(solve_linear(v1, v2, p1, p2),(-2,2))
        v1=[3,3]
        v2=[1,0]
        (p,q)=solve_linear(v1, v2, p1, p2)
        self.assertAlmostEqual(p,-2.0/3,6)
        self.assertAlmostEqual(q,0,6)
        (v1,v2,p1,p2)=((5,-3),(1,1),(2,3),(3,0))
        (p,q)=solve_linear(v1, v2, p1, p2)
        self.assertAlmostEqual(p,0.5,6)
        self.assertAlmostEqual(q,1.5,6)
    
    def _predict(self,npoints):
        cv.FillConvexPoly(self.draw_img, npoints, (0,0,0))
        corners = Corner.get_corners(npoints)
        tcorners = list(corners)
        for i,cor in enumerate(corners):
            print cor.p
            if not(0<=cor.p[0]<self.size and 0<=cor.p[1]<self.size):
                tcorners[i]=None
        
        CP = CornerPredictor(self.corners, 1, self.tmp_img, self.timg, self.draw_img)
        print "predicting....",tcorners
        ncorners = CP.predict_corners(tcorners)
        print 'done'
        for i,cor in enumerate(ncorners):
            v=vector(corners[i].p,cor.p)
            print length(v), cor.toString()
            self.assertTrue(length(v)<5,"Wrong prediction!Corner: %d \
            Expected: (%d,%d) received (%d,%d)" \
            %(i,corners[i].p[0],corners[i].p[1],cor.p[0],cor.p[1]))
        print ncorners  

    def test_predictOne(self):
        npoints = map(lambda x: add((40, 0), x), self.points)
        self._predict(npoints)
       
    def test_predict_from_one(self):
        npoints = map(lambda x: add((60, 30), x), self.points)
        self._predict(npoints)
        
    def test_dummy(self):
        pass
    def test_validate_corners(self):
        print self.corners
        print self.old_corners
        ncorners = self._prepare_corners(self.points)
        c= ncorners[0]
        prev = add(c.prev,(2,0))
        p = add(c.p,(1,1))
        next= add(c.next,(2,0))
        ncorners[0] = Corner([prev,p,next],1,imgtime=2)
        ncorners[0].compute_change(self.corners[0])
        res = list(ncorners)
        res[0]=None
        print ncorners
        for i,cor in enumerate(ncorners):
            cor.draw(self.draw_img)
            cor.compute_change(self.corners[i])
        db.show(self.draw_img,"main")
        CP = CornerPredictor(self.corners, 1, self.tmp_img, self.timg, self.draw_img)
        CP.validate_corners(ncorners)
        self.assertEqual(ncorners,res,
                         "First corner is invalid:"+ncorners.__repr__())
def suite():
    tests = [
             #'test_predictOne',
             #'test_solve_linear',
             #'test_predict_from_one',
             'test_validate_corners',
             'test_dummy']
    return unittest.TestSuite(map(CornerPredictorTest,tests))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
    
    #import sys;sys.argv = ['', 'CornerPredictorTest.test_predictOne']
    #unittest.main()
    
