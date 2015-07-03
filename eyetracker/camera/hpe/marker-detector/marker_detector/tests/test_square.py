'''
Created on 2010-06-23

@author: Macias
'''
import unittest
import cv
from utils import show
from square import Square
from marker_detector import SquareDetector


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_decode(self):
        a= Square.SQ_SIZE
        b = a*(Square.GRID_SIZE+3)
        rect = [(a,a),(b,a),(b,b),(a,b)]
        m_d = SquareDetector(Square.generate(1),0)
        for i in range(32):
            img = Square.generate(i)
            sq = Square(i,m_d)
            m_d.gray_img=img
            a,b = sq._decode_rect(rect)
            self.assertTrue((sq.TOP_LEFT,i)==(a,b),"Wrong %d: (%d,%d)"%(i,a,b))
            cv.Transpose(img, img)
            cv.Flip(img)
            a,b = sq._decode_rect(rect)
            self.assertTrue((sq.BOT_LEFT,i)==(a,b),"Wrong %d: (%d,%d)"%(i,a,b))
            cv.Transpose(img, img)
            cv.Flip(img)
            a,b = sq._decode_rect(rect)
            self.assertTrue((sq.BOT_RIGHT,i)==(a,b),"Wrong %d: (%d,%d)"%(i,a,b))
            cv.Transpose(img, img)
            cv.Flip(img)
            a,b = sq._decode_rect(rect)
            self.assertTrue((sq.TOP_RIGHT,i)==(a,b),"Wrong %d: (%d,%d)"%(i,a,b))
        m_d.flip_H=True
        for i in range(32):
            img = Square.generate(i)
            sq = Square(i,m_d)
            m_d.gray_img=img
            cv.Flip(img,img,1)
            _,b = sq._decode_rect(rect)
            self.assertTrue(i==b,"Wrong Flip %d: (%d)"%(i,b))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_generate']
    unittest.main()