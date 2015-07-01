"""
Module gives access to various properties of the device screen and relations
between them. They should be relevant no matter which operating system is
being used. It also contains tools for conversion between different units.
"""
import re
import sys
from sys import platform
from subprocess import Popen, PIPE
from collections import namedtuple

from gi.repository import Gdk


ScreenSizeMM = namedtuple('ScreenSizeMM', 'width height')
ScreenSizePix = namedtuple('ScreenSizePix', 'width height')

_initialized = False

size_pix = None
size_mm = None
SCREEN_DPMM = None
SCREEN_DPI = None

def _initialize():
    global size_pix, size_mm, SCREEN_DPMM, SCREEN_DPI, _initialized
    if _initialized:
        return
    _initialized = True
    if "--debug" in sys.argv:
        size_pix = ScreenSizePix(800, 600)
        SCREEN_DPI = 96.0
        SCREEN_DPMM = SCREEN_DPI / 25.4
        size_mm = ScreenSizeMM(size_pix.width / SCREEN_DPMM, size_pix.height / SCREEN_DPMM)
    else:
        size_pix = ScreenSizePix(Gdk.Screen.width(), Gdk.Screen.height())

        if 'linux' in platform:
            try:
                temp = []
                out = str(Popen('xrandr', stdout=PIPE).stdout.read()).split()
                for mm in out:
                    if 'mm' in mm:
                        mm = re.sub('[^0-9]', '', mm)
                        temp.append(mm)
                        if len(temp) == 2:
                            size_mm = ScreenSizeMM(int(temp[0]), int(temp[1]))
                            break
            except OSError:
                print('No xrandr, falling back to Gdk for screen size in mm.')
                size_mm = ScreenSizeMM(
                    Gdk.Screen.width_mm(),
                    Gdk.Screen.height_mm())
        else:
            print('Apparently not on linux, using Gdk.Screen for mm size.')
            size_mm = ScreenSizeMM(Gdk.Screen.width_mm(), Gdk.Screen.height_mm())

        try:
            SCREEN_DPMM = size_pix.width / size_mm.width
        except ZeroDivisionError:
            print(
                'Issue with xrandr causes screen size to be 0mm, using Gdk.Screen of mm size.')
            size_mm = ScreenSizeMM(Gdk.Screen.width_mm(), Gdk.Screen.height_mm())
            SCREEN_DPMM = size_pix.width / size_mm.width

        SCREEN_DPI = SCREEN_DPMM * 25.4


def mm(value):
    """
    Convert milimeters to number of pixels.

    :param value: milimeters
    
    :returns: number of pixels, as integer
    """
    global SCREEN_DPMM
    _initialize()
    return int(value * SCREEN_DPMM)


def w(v):
    """
    Get the number of pixels covering the given part of the device screen
    in horizontal direction.

    :param v: floating point number, from 0 to 1
    
    :returns: number of pixels, as float
    """
    global size_pix
    _initialize()
    return v * size_pix.width


def h(v):
    """
    Get the number of pixels covering the given part of the device screen
    in vertical direction.

    :param v: floating point number, from 0 to 1
    
    :returns: number of pixels, as float
    """
    global size_pix
    _initialize()
    return v * size_pix.height


def pt_to_px(pt):
    """
    Convert points to number of pixels.

    :param pt: number of points

    :returns: number of pixels, as float
    """
    global SCREEN_DPMM
    _initialize()
    return pt * SCREEN_DPMM


if __name__ == '__main__':
    _initialize()
    msg = 'Your screen size in mm is {} x {}, in pixels {} x {} which gives {} DPI.'.format(
        size_mm.width,
        size_mm.height,
        size_pix.width,
        size_pix.height,
        round(SCREEN_DPI))
    print(msg)
