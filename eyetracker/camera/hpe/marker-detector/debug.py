'''
Created on 2010-07-01

@author: Macias
'''
import cv
from vectors import scale

forbidden_lables = []
class dummy(object):
    index = 0
prov = dummy()
start_index = 0
font = cv.InitFont(cv.CV_FONT_HERSHEY_COMPLEX_SMALL, 0.7, 0.7)

DEBUG = False

def pr(args=[], label='print'):
    if not DEBUG: return
    if prov.index < start_index:return
    if label in forbidden_lables: return
    str = label + ":"
    for a in args:
        str += repr(a) + " "
    print str

def db_break(name="break"):
    if prov.index >= start_index:
        pass

def Circle(img, center, radius, color):
    if not DEBUG: return
    cv.Circle(img, center, radius, color)

def PolyLine(img, polys, is_closed, color, text=None, scale_f=1):
    if not DEBUG: return
    if scale_f != 1:
        polys[0] = map(lambda p:scale(p, scale_f), polys[0])
    polys[0] = [(int(p[0]), int(p[1])) for p in polys[0]]
    cv.PolyLine(img, polys, is_closed, color)
    if text is not None:
        polys = polys[0]
        x, y = reduce(lambda (x, y), (w, z):(x + w, y + z), polys, (0, 0))
        cv.PutText(img, text, (x / len(polys), y / len(polys)), font, (0, 255, 255))

def DrawContours(img, contour, external_color, hole_color, max_level):
    if not DEBUG: return
    cv.Zero(img)
    cv.DrawContours(img, contour, external_color, hole_color, max_level)
