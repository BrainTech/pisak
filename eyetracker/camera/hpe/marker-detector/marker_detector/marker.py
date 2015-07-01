'''
Created on 2010-06-23

@author: Macias
'''
from corner import Corner
import cv
from vectors import add,dist_points
import debug as db

MAX_SEEN = 1.0

class Marker(object):
    '''
    Object which will be responsible for finding, recognizing and predicting
    position of key points of certain marker
    '''
    xml_init_fields = ('ident',)
    def __repr__(self):
        return "\nMarker %d:" % self.ident + self.get_int_points().__repr__() + \
                "Last seen:%d" % self.last_seen
    def __init__(self, name=None):
        '''
        Creates new object with
        @param name:  name of that marker (number, string, etc..)
        '''
        self.ident = name
        self.m_d = None
        self.last_seen = -100
        self.corners = []
        self.object_points = None
        self.hpr = None
        self.pos = None
        self.changed = 0
        self.area = 0
        self.predicted = -1
        self.black_inside=1


    def scale_up(self, scale):
        for c in self.corners:
            c.scale_up(scale, self.m_d)

    def check_contours(self, conts, scale):
        '''
        checks if conts describe this marker.
        If yes, updates itself and return True.
        If no, return False or object, where object can be used as a hint for
        other markers to fast check if these conts describe them (ie. conts
        describe good square, but with different identifier. to not do the same
        operations this square can be passed to other square markers)
        @param conts: unapproximated countours
        '''
        return (None, None)

    def check_conts_with_hint(self, conts, hint):
        '''
        This function should be fast. Checks if hint fits this marker.
        if so, update marker and return True
        @param conts: unapproximated contours
        @param hint: object
        '''
        return False

    def get_bounding_rect(self):
        '''
        Returns bounding rectangle, containing this marker
        '''
        return cv.BoundingRect(self.points)

    def find_corners(self, *args):
        return False
    def _get_approx(self, conts):
        '''
        Returns contur aproximation
        @param conts: conturs
        '''
        per = cv.ArcLength(conts)
        conts = cv.ApproxPoly(conts, cv.CreateMemStorage(), cv.CV_POLY_APPROX_DP, per * 0.05)
        #cv.DrawContours(self.img, conts, (0,0,255), (0,255,0), 4)
        return list(conts)

    def set_new_position(self, points_or_corners, offset=True, scale=1):
        '''
        Sets new position for this marker using points (in order)
        @param points_or_corners: list of points or corners
        @param offset: if true, image ROI is checked and points are shifted
        '''
        if len(points_or_corners) > 0 and type(points_or_corners[0]) == tuple:
            self.predicted = -1
            points = points_or_corners
            img = self.m_d.img
            (x, y, _, _) = rect = cv.GetImageROI(img)
            if offset and (x, y) <> (0, 0):
                points = map(lambda z: add((x, y), z), points)
            cv.ResetImageROI(img)
            crit = (cv.CV_TERMCRIT_EPS + cv.CV_TERMCRIT_ITER, 30, 0.1)
            if (scale > 1):
                points = cv.FindCornerSubPix(self.m_d.gray_img, points, (scale * 2 + 4, scale * 2 + 4), (-1, -1), crit)
            else:
                points = cv.FindCornerSubPix(self.m_d.gray_img, points, (3, 3), (-1, -1), crit)
            ncorners = Corner.get_corners(points, self.m_d.time)
            if len(self.corners) <> 0:
                for i, cor in enumerate(ncorners):
                    cor.compute_change(self.corners[i])
            cv.SetImageROI(img, rect)
        else:
            ncorners = points_or_corners
            self.predicted += len(filter(lambda x:x.is_predicted, ncorners))
        for i,c in enumerate(ncorners):
            c.black_inside=self.black_inside
#            if len(self.corners)==4:
#                if dist_points(c.p, self.corners[i].p)<4:
#                    c.p=self.corners[i].p
        self.corners = ncorners

        self.area = abs(cv.ContourArea(self.points))
        self.last_seen = self.m_d.time
        self.model_view = None


    def draw(self, img, colors=[(128, 0, 0), (0, 128, 0), (0, 0, 128), (255, 0, 0)], font=None):
        rect = self.get_int_points()
        L = len(rect)
        if L == 0 : return
        (a, b) = (0, 0)
        lcol = len(colors)

        for i in range(L):
                cv.Line(img, rect[i], rect[(i + 1) % L], colors[i % lcol], 2)
                if self.corners[i].is_predicted:
                    cv.Circle(img, rect[i], 2, (0, 0, 255), 2)
                a, b = a + rect[i][0], b + rect[i][1]
        if font is not None:
            cv.PutText(img, str(self.ident), (a / L, b / L), font, (0, 255, 0))
        return None

    def get_int_points(self):
        return map(lambda x: (int(x[0]), int(x[1])), self.points)


    def get_points(self):
        if self.corners is None:
            return []
        else:
            if None in self.corners:
                return []
            else:
                return map (lambda x: x.p, self.corners)

    def get_identifier(self):
        return self.ident

    def is_found(self):
        pred=0
        for c in self.corners:
            pred+=1 if c.is_predicted else 0
        return self.last_seen + 0.05 > self.m_d.time and pred <= 3

    rect = property(get_points, None, None, "@deprecated: Square's key points in defined order")
    points = property(get_points, None, None, "Square's key points in a defined order")
    name = property(get_identifier, None, "@deprecated: Square's identifier")
    identifier = property(get_identifier, None, "Square's identifier")
