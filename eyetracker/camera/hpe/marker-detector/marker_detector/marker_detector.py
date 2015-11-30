'''
Created on 2010-03-20

@author: Macias
'''

import cv
import time

from square import Square
from utils import rgb2gray, correct_rectangle
from marker import Marker
import debug as db
import marker

class SquareDetector(object):
    xml_init_fields = ('max_scale', 'flip_H')
    def __init__(self, img=None, **kwargs):
        self.init(img, **kwargs)

    def __repr__(self):
        return "SqureDetector (max_scale: " + str(self.max_scale) + " flip_h: " + str(self.flip_H)

    def init(self, img, time_first=0, max_scale=0, flip_H=False, size=(640, 480), depth=8, channels=3):
        if img is not None:
            size, depth, channels, time_first = cv.GetSize(img), img.depth, img.nChannels, time_first
        self.imgs = imgs = []
        self.gray_imgs = gray_imgs = []
        self.tmp_imgs = tmp_imgs = []
        self.canny_imgs = canny_imgs = []
        self.bw_imgs = bw_imgs = []
        self.draw_imgs = draw_imgs = []
        db.m_d = self
        self.size, depth, channels, self.last = size, depth, channels, time_first
        wx, wy = self.size
        def image(wx, wy, d, c):
            return cv.CreateImage((wx, wy), d, c)
        for _ in range(max_scale + 1):
            for l in [imgs, draw_imgs]:
                l.append(image(wx, wy, depth, channels))
            for l in [tmp_imgs, canny_imgs, bw_imgs, gray_imgs]:
                l.append(image(wx, wy, 8, 1))
            wx, wy = wx / 2, wy / 2
        self.scaled_images = zip(imgs, draw_imgs, tmp_imgs, canny_imgs, bw_imgs, gray_imgs)
        self.max_scale = max_scale
        self.font = cv.InitFont(cv.CV_FONT_HERSHEY_COMPLEX_SMALL, 0.7, 0.7)
        self.markers = {}
        self.processedRects = []
        self.time = 0
        self.not_found = []
        self.flip_H = flip_H
        self.scale_factor = 1
        self.set_scale(0)

    def set_scale(self, scale):
        self.img, self.draw_img, self.tmp_img, \
        self.canny_img, self.bw_img, self.gray_img = self.scaled_images[scale]
        self.scale = scale
        self.size = cv.GetSize(self.img)
        self.scale_factor = 1 << scale


    def to_scale(self, img):
        '''
        makes images smaller when needed. It is using PyrDown
        @param img: image to resize
        '''
        for i in range(1, self.max_scale + 1):
            cv.PyrDown(self.imgs[i - 1], self.imgs[i])

    def preprocess(self, img, imgtime):
        '''
        set up for next image
        @param img: image to detect
        @param imgtime: time of the image
        '''
        self.set_ROI(None)
#        if self.flip_H: cv.Flip(img, self.imgs[0], 1)
#        else:
        cv.Copy(img, self.imgs[0]);
#        cv.Smooth(img, self.imgs[0],cv.CV_GAUSSIAN,5)

        self.to_scale(img)
        for scale in range(self.max_scale + 1):
            self.set_scale(scale)
            if self.img.nChannels == 1:
                cv.Copy(self.img, self.gray_img)
            else:
                rgb2gray(self.img, self.gray_img)
            cv.Copy(self.img, self.draw_img)
        self.time = imgtime

    def add_marker(self, marker):
        '''
        From now detector will be looking for this marker
        @param marker: Marker
        '''
        self.markers[marker.identifier] = marker
        marker.m_d = self

    def remove_marker(self, marker_ident):
        self.markers.pop(marker_ident, None)


    def check_recognized(self, mark, conts, i):
        '''
        Checks if marker recognizes conts.
        @param mark: marker
        @param conts: contours
        @param i: index we are checking
        '''
        a = mark.check_contours(conts, self.scale_factor)
        if a is True: return mark
        elif a is False: return None
        ident, hint = a
        if self.markers.has_key(ident):
            m = self.markers[ident]
            if m.check_conts_with_hint(conts, (ident, hint), self.scale_factor): return m
            print "Check_recognized Warning. Marker", m, "should recognize", a
        for m in self.not_found[i + 1:]:
            if m.check_conts_with_hint(conts, (ident, hint), self.scale_factor): return m
        return None

    def test_contours(self, conts, depth=0):
        '''
        checks if conts or his sons are valid markers
        @param conts: conts to check
        @param depth: int, how deep we are - even means white
        '''
        current = conts
        ans = False
        while current:
            if self.test_contours(current.v_next(), depth + 1):
                ans = True
            elif depth % 2 == 0:
#            else:
                # this is white object with no markers inside
                for i, marker in enumerate(self.not_found):
                    m = self.check_recognized(marker, current, i)
                    if m is not None:  # these contours belong to marker
                        if m not in self.not_found:
                            print "Error! Marker ", m, "was found twice! (test contours,line111)"
                        else:
                            self.not_found.remove(m)
                        ans = True
                        break
            current = current.h_next()
        return ans

    def draw_markers(self, image):
        '''
        Draw markers
        @param image:
        '''
        colors = [(128, 0, 0), (0, 128, 0), (0, 0, 128), (255, 0, 0)]
        for rect in self.markers.itervalues():
            if rect.is_found():
                rect.draw(image, colors, self.font)

    def threshold(self):
        for x in range(0, self.size[0], 30):
            for y in range(0, self.size[1], 30):
                cv.SetImageROI(self.gray_img, (x, y, 30, 30))
                cv.SetImageROI(self.bw_img, (x, y, 30, 30))
                cv.Threshold(self.gray_img, self.bw_img, 127, 255, cv.CV_THRESH_OTSU)
        cv.ResetImageROI(self.gray_img)
        cv.ResetImageROI(self.bw_img)

    def find_new_markers(self, do_canny=True):
        '''
        Find markers totally without taking their previous position into
        consideration
        @param do_canny: perform edge recognition
        '''
        for scale in range(self.max_scale, -1, -1):
            if len(self.not_found) == 0: return
            self.set_scale(scale)
            if do_canny: cv.Canny(self.gray_img, self.bw_img, 100, 300)
            cv.Copy(self.bw_img, self.tmp_img)
            self.tmp_img[1, 1] = 255
            cont = cv.FindContours(self.tmp_img, cv.CreateMemStorage(), cv.CV_RETR_TREE)
            db.DrawContours(self.canny_img, cont, (255, 255, 255), (128, 128, 128), 10)
#            db.show([self.canny_img,self.tmp_img,self.bw_img], 'show', 0, 1)
#            cv.ShowImage("name", self.canny_img)
#            cv.ShowImage("name1", self.tmp_img)
            self.set_scale(0)
            self.scale_factor = 1 << scale
            self.test_contours(cont)
            #markers= filter(lambda sq:sq.check_square(self.img,self.gray_img),rects)

        return self.markers



    def set_ROI(self, rect=None):
        '''
        Sets Roi of images to rect
        @param rect: (x,y,wx,wy)
        '''
        for img in self.scaled_images[self.scale]:
            if rect is None:
                cv.ResetImageROI(img)
            else:
                cv.SetImageROI(img, rect)


    def find_old_markers(self):
        '''
        Find markers using their previous position
        '''
        #print "find old"
        self.borders = []
        for scale in range(0, -1, -1):
            self.set_scale(scale)
            for mar in self.not_found:
                if mar.find_corners():
                    self.not_found.remove(mar)
        return

        if len(self.not_found) == 0: return
        # if there are some undetected markers, try to find them again. This
        # time bw_img has more accurate tresholding, so maybe we will find them
        if len(self.borders) == 0: return
        (x, y, wx, wy) = cv.BoundingRect(self.borders)
        cv.ResetImageROI(self.img)
        rect = correct_rectangle((x - wx / 2, y - wy / 2, wx * 1.5, wy * 1.5),
                                self.size)
        # self.set_ROI(rect)
        #self.find_new_markers(do_canny=False)
        #self.set_ROI(None)

    def putText(self, text, point, color=(0, 0, 255)):
        '''
        Draws text on self.image
        @param text:
        @param point:
        @param color:
        '''
        cv.ResetImageROI(self.img)
        cv.PutText(self.img, str(text), point, self.font, color)

    def find_markers(self, img, imgtime, find_old=True):
        '''
        Return a list containing detected(or predicted) markers
        @param img: img where to look
        @param imgtime: time where image was obtained
        @param find_old: True when we want to perform finding old markers
        '''
        self.preprocess(img, imgtime)
        self.not_found = list(self.markers.itervalues())
        self.find_new_markers()
        if find_old: self.find_old_markers()
        self.set_ROI(None)
        return filter(lambda x: x.is_found(), self.markers.itervalues())

    def scale_up(self, point_or_vec):
        return point_or_vec[0] * self.scale_factor, point_or_vec[1] * self.scale_factor

    def scale_down(self, point_or_vec):
        return point_or_vec[0] / self.scale_factor, point_or_vec[1] / self.scale_factor

if __name__ == "__main__":
#    img = cv.LoadImage("img.jpg")
#    im = ImageProvider(["img.jpg"])
    from image_providers.cam_image_provider import CamImageProvider
    i_p = CamImageProvider(0, p_width=1920, p_height=1080)
    m = Square(0)
    img = i_p.next()
    m_d = SquareDetector(img)
    m_d.add_marker(m)
    db.m_d = m_d
    while cv.WaitKey(1) != 27:
        img, t = i_p.getNext()
        print m_d.find_markers(img, t), t
        m_d.draw_markers(img)
        cv.ShowImage("markers", img)

#    m_d.find_markers(img, 0)
