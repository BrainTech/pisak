'''
Created on Mar 30, 2010

@author: user
'''

import cv;
import time
import cProfile
import sys
sys.path.insert(0, '..')

from marker_detector import SquareDetector
from image_providers import *
from utils import *
from square import Square
from vectors import *
import debug as db


CAM = 1
def main():
    if CAM == 0:
        provider = MovieImageProvider('../resources/Video5.avi', 0, 0)
    else:
        provider = CamImageProvider(0, '../resources/Video5.avi')
    db.start_at(provider, 110)
    img, imgtime = provider.update_image()
    print(img, imgtime, time.time())
    db.pr([img]);
    sd = SquareDetector(img)  # ,imgtime,1, False )
    for i in [0, 30]:
        sd.add_marker(Square(i))

    # win='Result'
    # canny='Canny'
    # tmp='Temp'
    # cv.NamedWindow(win)
    # cv.NamedWindow(tmp)
    # cv.MoveWindow(win,0,0)
    # cv.MoveWindow(tmp,650,0)
    ti = 0.01
    while True:
        k = cv.WaitKey(1)
        if k == 27:
            break
        elif k == 2424832:
            step = -1
        elif k == 32:
            cv.WaitKey(delay=0)
            step = 1
        else:
            step = 1;
        start = time.time()
        img, imgtime = provider.update_image()
        if img is None:
            break
        if provider.index == 112:
            pass
        sq = sd.find_markers(img, imgtime)
        sd.draw_markers(img)
        sd.putText("Frame: %d %.3f FPS" % (provider.index, (1 / ti)), (0, 15), (0, 0, 0))
        cv.ShowImage('test', sd.draw_img)
        db.show([img, sd.draw_img, sd.bw_img], 'main', 0, 10)
        ti = time.time() - start
        cv.WaitKey(1)

# main()

if __name__ == '__main__':
    # print cProfile.run('main()')
    main()
