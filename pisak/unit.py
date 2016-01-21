"""
Module gives access to various properties of the device screen and relations
between them. They should be relevant no matter which operating system is
being used. It also contains tools for conversion between different units.
"""
import sys
from collections import namedtuple


MonitorSizeMM = namedtuple('MonitorSizeMM', 'width height')
MonitorSizePix = namedtuple('MonitorSizePix', 'width height')

size_pix = None
size_mm = None

MONITOR_DPMM = None
MONITOR_DPI = None
MONITOR_X = None
MONITOR_Y = None


def initialize():
    global size_pix, size_mm, MONITOR_X, MONITOR_Y, MONITOR_DPMM, MONITOR_DPI

    if "--debug" in sys.argv:
        size_pix = MonitorSizePix(800, 600)
        MONITOR_X = 0
        MONITOR_Y = 0
        MONITOR_DPI = 96.0
        MONITOR_DPMM = MONITOR_DPI / 25.4
        size_mm = MonitorSizeMM(size_pix.width / MONITOR_DPMM, size_pix.height / MONITOR_DPMM)
    else:
        from gi.repository import Gdk

        screen = Gdk.Screen.get_default()
        n_monitors = screen.get_n_monitors()
        primary_monitor_id = screen.get_primary_monitor()

        if '--monitor-secondary' in sys.argv:
            if n_monitors > 1:
                for m_id in range(n_monitors):
                    if m_id != primary_monitor_id:
                        monitor_id = m_id
                        break
            else:
                monitor_id = primary_monitor_id
        else:
            monitor_id = primary_monitor_id

        monitor_geometry = screen.get_monitor_geometry(monitor_id)
        MONITOR_X = monitor_geometry.x
        MONITOR_Y = monitor_geometry.y
        size_pix = MonitorSizePix(monitor_geometry.width,
                                  monitor_geometry.height)
        size_mm = MonitorSizeMM(screen.get_monitor_width_mm(monitor_id),
                                screen.get_monitor_height_mm(monitor_id))
        try:
            MONITOR_DPMM = size_pix.width / size_mm.width
        except ZeroDivisionError:
            MONITOR_DPMM = 72 / 25.4
        MONITOR_DPI = MONITOR_DPMM * 25.4


def mm(value):
    """
    Convert milimeters to number of pixels.

    :param value: milimeters.
    
    :return: number of pixels, as integer.
    """
    return int(value * MONITOR_DPMM)


def w(v):
    """
    Get the number of pixels covering the given part of the device screen
    in horizontal direction.

    :param v: floating point number, from 0 to 1.
    
    :return: number of pixels, as float.
    """
    return v * size_pix.width


def h(v):
    """
    Get the number of pixels covering the given part of the monitor
    in vertical direction.

    :param v: floating point number, from 0 to 1.
    
    :return: number of pixels, as float.
    """
    return v * size_pix.height


def pt_to_px(pt):
    """
    Convert points to number of pixels.

    :param pt: number of points.

    :return: number of pixels, as float.
    """
    return pt * MONITOR_DPMM
