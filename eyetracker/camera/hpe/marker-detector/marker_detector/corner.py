'''
Created on Apr 13, 2010

@author: user
'''
import cv
from vectors import *
from utils import correct_rectangle
import debug as db

MIN_RECT = 1.0 / 12
MAX_WIDTH = 640
MOVE_MARGIN = 2
MIN_SIZE = 2
MAX_COLOR_DIFFERNCE = 50
MAX_CORNER_ANGLE = r2d(150)
NOT_SIMILLAR = 1000000
FORWARD_VEC_SCALE = 2
BACK_VEC_SCALE = -.5
MAX_SEARCH_VECTOR_LENGTH = (1.0 / 4) / FORWARD_VEC_SCALE
BLACK_WHITE_DIFFERENCE = 30

class Corner(object):
    '''
    Class responsible for managing one corner
    '''
    @staticmethod
    def get_corners(points, time=0):
        '''
        Return list of corners made from points
        @param points:
        @param time: current image time
        '''
        corners = []
        for i in range(len(points)):
            corners.append(Corner(points, i, imgtime=time, id=i))
        return corners

    def __repr__(self):
        '''
        String representation
        '''
        return "<Corner:(%d,%d)-(%d,%d)-(%d,%d)> ang:%.2f" % (int(self.prev[0]), int(self.prev[1]), \
                                                   int(self.p[0]), int(self.p[1]), \
                                                   int(self.next[0]), int(self.next[1]), self.angle)

    def toString(self):
        (a, b) = self.p
        str = (a, b, length(add(self.p, self.prev, -1)), r2d(self.angle), r2d(self.rotation))
        return  "point: (%d,%d), length: %.2f, angle: %.0f, rotation: %.0f" % str

    def __init__(self, points, index=1,imgtime=0, id= -1,scale_f=1):
        '''
        Make Corner from points
        @param points: list of points
        @param index: create corner from points[index]
        @param offset: if points are in ROI
        '''
        self.p = scale(points[index],scale_f)
        self.prev = scale(points[(index + len(points) - 1) % len(points)],scale_f)
        self.next = scale(points[(index + 1) % len(points)],scale_f)
        self.id = id
        self.abs_angle = 0;
        self.abs_v = (0, 0);
        self.abs_rotation = 0;
        self.angleps = 0;
        self.rotationps = 0;
        self.vps = (0, 0);
        self.vrotation = 0
        self.vrotationps = 0
        self.predicted = self.p
        self.bounds = [self.p]
        self.time = imgtime
        self.similarity = NOT_SIMILLAR
        self.color_white = None
        self.color_black = None
        self.color_difference = (0,0)
        self.diag = (0, 0)
        self.is_predicted = False
        self.black_inside=1
        self.measure()

    def get_different(self):
        return self.similarity == NOT_SIMILLAR


    def measure(self):
        self.vp = vector(self.p, self.prev)
        self.vn = vector(self.p, self.next)
        self.len_p = length(self.vp)
        self.len_n = length(self.vn)
        self.angle = vectorAngle(self.vp, self.vn)
        self.angle = vectorAngle(self.vp, self.vn)
        if self.len_p > 0:
            v1 = self.nvp = (self.vp[0] / self.len_p, self.vp[1] / self.len_p)
        else:
            v1 = self.nvp = (0, 0)
        if self.len_n > 0:
            v2 = self.nvn = (self.vn[0] / self.len_n, self.vn[1] / self.len_n)
        else:
            v2 = self.nvn = (0, 0)

        v3 = normalize(((v1[0] + v2[0]) / 2, (v1[1] + v2[1]) / 2))
        self.rot_v = v3
        self.rotation = math.atan2(v3[1], v3[0])

    def compute_change(self, cor, image=None):
        '''
        Compute how much this Corner changed since the last time
        @param cor: corner on previous image
        '''
        time = self.time - cor.time
        if time < 1 / 50.0:
#            print "Warning - this corner was found already on this image", cor, self
            return
        self.abs_v = vector(cor.p, self.p)
        if length(self.abs_v) < MOVE_MARGIN:
            self.abs_v = (0, 0)
        self.vps = (float(self.abs_v[0]) / time, float(self.abs_v[1]) / time)
        self.abs_angle = self.angle - cor.angle
        self.angleps = self.abs_angle / time
        self.abs_rotation = self.rotation - cor.rotation
        self.rotationps = self.abs_rotation / time
        self.diag = rotateVec(cor.diag, self.abs_rotation)
        if cor.abs_v != (0, 0):
            self.vrotation = vectorAngle(cor.abs_v, self.abs_v)
            if det((0, 0), cor.abs_v, self.abs_v) < 0:
                self.vrotation = -self.vrotation
            self.vrotationps = self.vrotation / time
        self.similarity = self.how_different()
        self.id = cor.id
        self.color_black = cor.color_black
        self.color_white = cor.color_white

    def check_color(self, img, grayimg):
        if img is not None:
            c_b = self.get_color(img, self.black_inside)
            c_w = self.get_color(img, -self.black_inside)
#            print "Colors:"
#            print self.color_black, self.color_white
#            print c_b, c_w
#            db.show([db.m_d.draw_img],wait=1,height=0)
            correct = 2
            if c_b is not None and self.color_black is not None:
                for c, sc in zip(c_b, self.color_black):
                    if abs(c- sc) > MAX_COLOR_DIFFERNCE:
                        correct -= 1
                        break
            if c_w is not None and self.color_white is not None:
                for c, sc in zip(c_w, self.color_white):
                    if abs(c- sc) > MAX_COLOR_DIFFERNCE:
                        correct -= 1
                        break
            if correct == 0:
                self.similarity = NOT_SIMILLAR
                self.color_difference=(0,1)
            else:
                c_b_g = self.get_color(grayimg, self.black_inside)
                c_w_g = self.get_color(grayimg, -self.black_inside)

                if c_b_g is not None and c_w_g is not None and \
                    abs(c_b_g[0]-c_w_g[0])< BLACK_WHITE_DIFFERENCE :
                    self.color_difference=(correct,1)
                    self.similarity = NOT_SIMILLAR
                else:
                    self.color_difference=(correct,0)

    def print_change(self):
        str = ""
        for it in ["vps:", self.vps, "angps:", self.angleps, "rotps:", self.rotationps, \
        "vp:", self.vp, "vn:", self.vn]:
            str += it.__repr__() + " "
        return str
    def get_bounding_points(self, m_d):
        '''
        Return list of points which are bounduaries for this corner search
        @param time: current time
        @param size: image size
        '''
        time = m_d.time - self.time
        vector = add((0, 0), self.vps, time)
        vector = m_d.scale_down(vector)
        vec_len = length(vector)
        p = m_d.scale_down(self.p)
        size = m_d.size
        if vec_len > MAX_SEARCH_VECTOR_LENGTH * size[0]:
            vector = add((0, 0), vector, MAX_SEARCH_VECTOR_LENGTH * size[0] / vec_len)
        angle = self.vrotationps * time
        points = []
        self.predicted = add(p, rotateVec(vector, angle))
        points.append(self.predicted)
        # bounding points for corner search
        points.append(add(p, rotateVec(vector, angle), FORWARD_VEC_SCALE))
        v1 = rotateVec(vector, 1.5 * angle)
        points.append(add(p, v1, FORWARD_VEC_SCALE))
        points.append(add(p, v1, BACK_VEC_SCALE))
        v2 = rotateVec(vector, -.3 * angle)
        points.append(add(p, v2, FORWARD_VEC_SCALE))
        points.append(add(p, v2, BACK_VEC_SCALE))
        points.append(add(p, vector, FORWARD_VEC_SCALE))
        points.append(add(p, vector, BACK_VEC_SCALE))
        self.bounds = points
        return points

    def get_rectangle(self, m_d):
        '''
        Return rectangle where we will be looking for this corner
        @param time: current time
        @param size: image size
        '''
        self.get_bounding_points(m_d)
        size = m_d.size
        (x, y, wx, wy) = cv.BoundingRect(self.bounds)
        (x, y, wx, wy) = x - MIN_SIZE, y - MIN_SIZE, wx + 2 * MIN_SIZE, wy + 2 * MIN_SIZE
        min_wx = MIN_RECT * size[0]
        min_wy = MIN_RECT * size[1]
        if (wx < min_wx):
            x -= (min_wx - wx) / 2
            wx = min_wx
        if (wy < min_wy):
            y -= (min_wy - wy) / 2
            wy = min_wy
        return (x, y, wx, wy)

    def draw(self, img):
        '''
        Draw this corner on img
        @param img:
        '''
        rect = cv.GetImageROI(img)
        cv.ResetImageROI(img)
        col = (255, 255, 255)
        cv.Line(img, self.prev, self.p, col)
        cv.Line(img, self.p, self.next, col)
#        cv.Line(img, self.p, add(self.p, rotateVec((30, 0), self.rotation), 1), col)
        cv.Circle(img, self.p, 2, col)
        font = cv.InitFont(cv.CV_FONT_HERSHEY_COMPLEX_SMALL, 0.7, 0.7)
        cv.PutText(img, "(%d,%d)" % self.p, self.p, font, col)
        cv.SetImageROI(img, rect)

    def _append_candidates_from_conts(self, rect, result, nconts, m_d):
        nconts = map(lambda (x,y):(x+rect[0],y+rect[1]),nconts)
        nconts.append(nconts[0])
        nconts.append(nconts[1])
        dir = 0
        a, b = add(nconts[0], nconts[2])
        a, b = add((a, b), nconts[1], 1000)
        conv = cv.PointPolygonTest(nconts, (a / 1002.0, b / 1002.0), 0)
        dir = det(nconts[0], nconts[1], nconts[2])
        if (conv * dir < 0):
            nconts = list(reversed(nconts))
        for i in range(1, len(nconts) - 1):
            if  not point_on_edge(nconts[i], rect) and \
                det(nconts[i - 1], nconts[i], nconts[i + 1]) > 0:
                # direction is ok - it is "convex corner"
                if nconts[i]==(104,197):
                    pass
                cor = Corner(nconts, i, imgtime=m_d.time,scale_f=m_d.scale_factor)
                cor.black_inside = self.black_inside
                cor.compute_change(self, m_d.img)
                cor.check_color(m_d.imgs[0], m_d.gray_imgs[0])
                if not cor.different: result.append(cor)

    def get_candidates(self, m_d):
        '''
        Get candidates for this corner from new image
        @param m_d: marker_detector
        '''
        # if this corner is wider then MAX_CORNER_ANGLE, we probably won't
        # find it anyway. Instead lets find narrow corners and calculate its
        # position
        if self.angle > MAX_CORNER_ANGLE: return []
        cr = self.get_rectangle(m_d)
        cr = correct_rectangle(cr, m_d.size)
        if cr is None: return []
        m_d.set_ROI(cr)
        tmp_img = m_d.tmp_img
        gray_img = m_d.gray_img
        bw_img = m_d.bw_img
        canny = m_d.canny_img
        cv.Copy(gray_img, tmp_img)
        cv.Threshold(gray_img, bw_img, 125, 255, cv.CV_THRESH_OTSU)
        if self.black_inside>0:
            cv.Not(bw_img, bw_img)
        cv.Canny(gray_img, canny, 300, 500)
        cv.Or(bw_img, canny, bw_img)
        tmpim = m_d.canny_img
        cv.Copy(bw_img, tmpim)
        cv.Set2D(tmpim, 1, 1, 255)
        conts = cv.FindContours(tmpim, cv.CreateMemStorage(), cv.CV_RETR_EXTERNAL);
        cv.Zero(tmpim)
        m_d.set_ROI()
        cv.SetImageROI(tmpim, cr)
        result = []
        while conts:
            aconts = cv.ApproxPoly(conts, cv.CreateMemStorage(), cv.CV_POLY_APPROX_DP, 2)
            nconts = list(aconts)
            cv.PolyLine(tmpim, [nconts], True, (255,255,255))
            self._append_candidates_from_conts(cr, result, nconts, m_d)
            conts = conts.h_next()
#        print result
#        db.show([tmpim,m_d.draw_img], 'tmpim', 0, 0, 0)
        return result
    def scale_up(self,m_d):

        self.p=m_d.scale_up(self.p)
        crit = (cv.CV_TERMCRIT_EPS + cv.CV_TERMCRIT_ITER, 30, 0.1)
        if not self.is_predicted:
            self.p = cv.FindCornerSubPix(m_d.gray_img, [self.p], (5, 5), (0, 0), crit)[0]
        self.prev=m_d.scale_up(self.prev)
        self.next=m_d.scale_up(self.next)
        self.measure()
        self.abs_v=m_d.scale_up(self.abs_v)
        self.vps=m_d.scale_up(self.vps)

    def set_colors(self, img):
        self.color_black = self.get_color(img, self.black_inside)
        self.color_white = self.get_color(img, -self.black_inside)

    def how_different(self):
        '''
        Return how different this corner is from the previous one. Lower-> more similar
        @param cor: Corner
        '''

        #corner has to have arms at least MIN_SIZE long
        if self.len_n < MIN_SIZE or self.len_p < MIN_SIZE: return NOT_SIMILLAR

        #angle can change by max 360 deg per second:
        angleps = abs(self.angleps)
        if (angleps > 2 * math.pi): return NOT_SIMILLAR

        # corner can rotate by no more then 360 deg per second:
        rotationps = abs(self.rotationps)
        if (rotationps > 2 * math.pi):return NOT_SIMILLAR

        #corner cannot move faster then MAX_WIDTH
        len_vps = length(self.vps)
        if (len_vps > MAX_WIDTH): return NOT_SIMILLAR

        return (angleps + rotationps) * 60 + len_vps

    def get_color(self, img, dir):
        wx, wy = cv.GetSize(img)
        point = add(self.p, self.diag, dir * 0.1)
        x, y = int(point[0]), int(point[1])
        if x < 0 or y < 0 or x >= wx or y >= wy:
            return None
        else:
            c = cv.Get2D(img, y, x)
            db.Circle(db.m_d.draw_img, (x, y), 2, (0, 128+dir*127, 128-dir*127))
            return c

    def get_prediction_vector(self, to_prev, old_corner):
        '''
        Returns vector which will be used for prediction of neighbor location.
        It considers the fact that if further visible point is very close
        (prediction is not accurate)
        and predicted vector is within some limit, old vector is used.
        @param to_prev: which neighbor to consider
        @param old_corner: previous position of this corner.
        '''
        v1 = self.vp
        v2 = self.vn
        if to_prev:
            mina, maxa = get_angle_range(v2, v1)
            if mina < old_corner.angle < maxa:
                vec = rotateVec(v2, old_corner.angle)
            else:
                vec = v1
            L = length(old_corner.vp)
        else:
            mina, maxa = get_angle_range(v1, v2)
            if mina < old_corner.angle < maxa:
                vec = rotateVec(v1, -old_corner.angle)
            else:
                vec = v2
            L = length(old_corner.vn)
        if vec <> (0, 0):
            lv = L / length(vec)
        else:
            print "get_prediction_vector has vector length 0"
            lv = L
        return (vec[0] * lv, vec[1] * lv)

    different = property(get_different, None, None,
        "Tells if this corner is completly different from its previous position")





if __name__ == '__main__':
    img = cv.CreateImage((200, 200), 8, 1)

    col = (128, 128, 128)
    p3 = [(0, 0), (65, 65), (200, 0)]
    p1 = [(0, 0), (120, 65), (200, 0)]
    p2 = [(0, 200), (120, 100), (200, 0)]
    c1 = Corner(p1, 1)
    #print det((0,0),(0,1) , (1,0)), det((0,0),(1,0),(0,1))
    c1.measure()
    c2 = Corner(p2, 1, imgtime=2)
    c2.measure()
    c3 = Corner(p3, 1, imgtime=2)
    c3.measure()
    c1.computeChange(c3, 1)

    c2.computeChange(c1, 1)
    c3.draw(img)
    c1.draw(img)
    c2.draw(img)
    points = c2.get_bounding_points(1)
    for p in points:
        cv.Circle(img, p, 2, (255, 255, 255))
    cv.Line(img, c2.p, points[0], (255, 255, 255))
    rect = c2.get_rectangle(1)
    #print rect
    cv.Rectangle(img, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), (64, 64, 64))
    cv.NamedWindow('a')
    cv.ShowImage('a', img)
    cv.WaitKey(120000)

