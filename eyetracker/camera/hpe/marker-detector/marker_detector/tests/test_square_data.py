'''
Created on 13-08-2010

@author: Macias
'''
from image_provider import CamImageProvider, MovieImageProvider
from square import Square
from marker_detector import SquareDetector
import math
import cv
from vectors import vector, length
import debug
import cProfile
def main():
    ip= CamImageProvider(0, "../resources/testdata.avi")
    #ip = MovieImageProvider("../resources/testdata.avi",0,0)
    sq = Square(0)
    img,imgtime = ip.getImage(1)
    m_d = SquareDetector(img, imgtime, 2, 0)
    m_d.add_marker(sq)
    angle_min = math.pi
    angle_max = 0
    angle_diff_min = 100
    angle_diff_max = 0
    prop_min  = 40
    prop_max = 0
    rot_max = 0
    debug.start_at(ip, 0)
    while cv.WaitKey(1)<>27:
        img,imgtime = ip.getImage(1)
        if img is None:
            return
#        tmpimg = cv.CloneImage(draw_img)
#        tmpimg2 = cv.CloneImage(draw_img)
#        gray2 = cv.CloneImage(gray)
#        gray3 = cv.CloneImage(gray)
#        tmp = cv.CloneImage(gray)
#        mask = cv.CloneImage(gray)
#        mask2=cv.CloneImage(gray)
#        cv.Set(mask2,1)
#        cv.CvtColor(draw_img, gray, cv.CV_BGR2GRAY)
#        cv.CvtColor(draw_img, tmpimg, cv.CV_BGR2HSV)
#        cv.SetImageCOI(tmpimg, 1)
#        cv.Copy(tmpimg, gray)
#        print cv.MinMaxLoc(gray)
#        cv.ShowImage("gray", gray)
        if debug.is_time():
            pass
        m_d.find_markers(img,imgtime,True)
        mar = m_d.markers[0]
        points = mar.points
        m_d.draw_markers(m_d.draw_img)
        debug.show([m_d.draw_img],"main",1,1)
        #debug.show_images()
        if len(points)<>4 or cv.WaitKey(50)<>32: 
            continue
        a = length(vector(points[0],points[1]))
        b = length(vector(points[1],points[2]))
        c = length(vector(points[2],points[3]))
        d = length(vector(points[3],points[0]))
        if a>c:
            a,c = c,a
        if b>d:
            b,d = d,b
        if c == 0.0:
            print mar
        else:
            print "sides a/c:", a/c
            if a/c > prop_max: prop_max = a/c
            if a/c < prop_min: prop_min = a/c
        if d==0.0:
            print mar
        else:
            print "sides b/d", b/d
            if b/d > prop_max: prop_max = b/d
            if b/d < prop_min: prop_min = b/d
        for cor in mar.corners:
            if cor.angle < angle_min:angle_min = cor.angle
            if cor.angle > angle_max:angle_max = cor.angle
            if cor.rotation > rot_max: rot_max = cor.rotation
        a,b,c,d = [c.angle for c in mar.corners]
        if a>c:
            a,c=c,a
        if b>d:
            b,d=d,b
        if a/c > angle_diff_max: angle_diff_max=a/c
        if a/c< angle_diff_min: angle_diff_min = a/c
        print "angle diff a/c", a/c
        if b/d > angle_diff_max: angle_diff_max=b/d
        if b/d< angle_diff_min: angle_diff_min = b/d
        print "angle diff b/d", b/d
                
    print "angle_min", angle_min
    print "angle_max", angle_max
    print "prop_min", prop_min
    print "prop_max", prop_max
    print "rot_max",rot_max
    print "angle_diff_min", angle_diff_min
    print "angle_diff_max",angle_diff_max
    
if __name__=="__main__":
    print cProfile.run("main()")
    #main()
    
    