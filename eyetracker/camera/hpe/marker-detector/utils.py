#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on 2010-06-17

@author: Macias
'''

from cv2 import cv
from vectors import det

win = None

def standarize_contours(conts):
    '''
    first point of new contours will be in left upper corner. Contour will be
    oriented clockwise
    @param conts: list of points
    '''
    min = (1000000, 1000000)
    min_i = -1;
    for i, p in enumerate(conts):
        if p < min:
            min = p
            min_i = i
    conts = conts[min_i:] + conts[:min_i]
    if det(conts[-1], conts[0], conts[1]) < 0:
        conts = [conts[0]] + list(reversed(conts[1:]))
    return conts


def rgb2gray(img, grayscale):
    '''
    convert img to grayscale
    @param img: image to convert
    @param grayscale: target
    '''
    # cv.CvtColor(img,self.img,cv.CV_RGB2HLS)
    cv.CvtColor(img, grayscale, cv.CV_RGB2GRAY)
    return
    cv.SetImageCOI(img, 2)
    cv.Copy(img, grayscale)
    cv.SetImageCOI(img, 0)


def get_equation(p1, p2):
    (a, b) = p1
    (c, d) = p2
    if c == a: return None
    x = (d - b) / float(c - a)
    y = b - a * x
    return x, y

def correct_rectangle(rect, img_size=(10000, 10000)):
    '''
    Check if rectangle fits into img and correct it accordingly
    @param rect: (x,y,wx,wy) - start point and width and height
    @param img_size: maximum coordinates of rectangle
    '''
    (x, y, wx, wy) = rect
    (x, y, wx, wy) = (int(round(x)), int(round(y)), int(round(wx)), int(round(wy)))
    (w, h) = img_size
    if x >= w or y >= h:return None
    if (x < 0):
        wx += x
        x = 0
    if (y < 0):
        wy += y
        y = 0
    if wx < 3:wx = 3
    if wy < 3:wy = 3
    if x + wx > w: wx = w - x;
    if y + wy > h: wy = h - y;
    if (wx < 3 or wy < 3): return None
    return (x, y, wx, wy)

def get_config(name, version, **kwargs):
    class Struct:
        def __init__(self, dict):
            self.__dict__.update(dict)
    Struct.__name__ = name
    return Struct(kwargs)
