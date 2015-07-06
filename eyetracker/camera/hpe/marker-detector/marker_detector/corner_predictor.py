'''
Created on Apr 27, 2010

@author: user
'''
import cv

from corner import Corner
from vectors import *
from utils import correct_rectangle
import debug as db
#import __builtin__


class CornerPredictor(object):
    '''
    Class responsible for looking for corners which are not found
    '''


    def __init__(self, corners, time, m_d):
        '''

        @param corners: old corners
        @param time: how much time from last image
        @param image: image where we will be checking for colors
        @param gray_image:
        @param bw_img:
        @param tmp_img:
        '''

        self.corners = corners
        self.time = time
        self.bw_img = m_d.bw_img
        self.tmp_img = m_d.tmp_img
        self.gray_img = m_d.gray_img
        self.image = m_d.img
        self.m_d = m_d
        self.bounds = []

    def find_better_point(self, from_, direction, predicted_length, range=20):
        '''
        Tries to find better corner arm - goes from from_ using vector direction
        on a line to find last visible point on this line
        @param from_:
        @param tpredicted_length: predicted length of this side
        @param direction:
        '''
        img = self.bw_img
        timg = self.tmp_img
        L1 = predicted_length * 1.2
        vec = direction
        L2 = length(vec)
        vec = add((0, 0), vec, L1 / L2) #vector towards direction of length of old side
        vec1 = rotateVec(vec, d2r(range))
        vec2 = rotateVec(vec, d2r(-range))
        x, y = from_
        cv.ResetImageROI(img)
        size = cv.GetSize(img)

        border_points = [add(from_, vec1), add(from_, vec2), (x - 5, y - 5), (x + 5, y + 5)]
        (x, y, wx, wy) = cv.BoundingRect(border_points)
        crect = correct_rectangle((x - 3, y - 3, wx + 6, wy + 6), size)
        [cv.SetImageROI(i, crect) for i in [img, timg, self.gray_img]]
        self.bounds.extend(cvrect(crect))
        cv.Threshold(self.gray_img, img, 125, 255, cv.CV_THRESH_OTSU)
        cv.Not(img, timg)
        cv.Canny(self.gray_img, img, 300, 500)
        cv.Or(img, timg,timg)
        rect = cvrect(crect)
        cv.Set2D(timg, 1, 1, (30, 30, 30))
        conts = cv.FindContours(timg, cv.CreateMemStorage(), cv.CV_RETR_EXTERNAL)
        db.DrawContours(timg, conts, (255, 255, 255), (128, 128, 128), 10)
        cv.Zero(timg)
        fr = add(from_, rect[0], -1)
        ans = []
        while conts:
            cont = cv.ApproxPoly(conts, cv.CreateMemStorage(), cv.CV_POLY_APPROX_DP, parameter=2, parameter2=0)
            cv.DrawContours(timg, cont, (255, 255, 255), (128, 128, 128), 10)
            cont = list(cont)
            L = len(cont)
            for i, p in enumerate(cont):
                if length(vector(fr, p)) < 5:
                    prev = cont[(i - 1 + L) % L]
                    next = cont[(i + 1) % L]
                    ans.append(vector(fr, prev))
                    ans.append(vector(fr, next))
            conts = conts.h_next()
        [cv.ResetImageROI(i) for i in [self.gray_img, timg, img]]
        if len(ans) == 0:
            # we didn't find corresponding corner,
            # that means it wasn't really a corner
            return None
        if len(ans) == 2 and ans[0] == ans[1]: return add(from_, direction)
        min = math.pi
        min_index = 0
        for i, v in enumerate(ans):
            tmp = vectorAngle(vec, v)
            if tmp < min:
                min = tmp
                min_index = i

        ans = ans[min_index]

        if length(ans)+1< L2:
            # the point we just found is closer then the previous one
            return add(from_,direction)

        abs_point = add(from_, ans)
        if point_on_edge(abs_point, crect):
            if not point_on_edge(abs_point, (0, 0, size[0], size[1])):
                if range < 20:
                    # this is recurence call. When we are here it means that
                    # side is longer then expected by over 2 times - it is not
                    # the side we are looking for- corner is not valid
                    return None
                else:
                    return self.find_better_point(from_, abs_point,
                                                  predicted_length * 2, 5)

        return abs_point

        #cv.Rectangle(img, rect[0], rect[1], (200,200,200))

    def _improve_corner(self, new_corners, index):
        cor = new_corners[index]
        if cor is None:
            return None
        L = len(new_corners)
        prev_index = (index + L - 1) % L
        next_index = (index + 1) % L
        if new_corners[prev_index] is None:
            side_length = length(vector(self.corners[index].p,
                                        self.corners[prev_index].p))
            prev = self.find_better_point(cor.p, cor.vp, side_length)
        else:
            prev = new_corners[prev_index].p
        if new_corners[next_index] is None:
            side_length = length(vector(self.corners[index].p,
                                        self.corners[next_index].p))
            next = self.find_better_point(cor.p, cor.vn, side_length)
        else:
            next = new_corners[next_index].p
        if prev is None or next is None:
            return None
        else:
            scale_f = self.m_d.scale_factor
            if scale_f <>1:
                cor.prev = self.find_corner_in_full_scale(prev)
                cor.next = self.find_corner_in_full_scale(next)
                cor.p = self.md.scale_up(cor.p,scale_f)
            else:
                cor.prev= prev
                cor.next = next

            crit = (cv.CV_TERMCRIT_EPS + cv.CV_TERMCRIT_ITER, 30, 0.1)
            cor.p = cv.FindCornerSubPix(self.m_d.gray_imgs[0], [cor.p],
                                (scale_f+4, scale_f+4), (0, 0), crit)[0]
            cor.measure()
            cor.compute_change(self.corners[index])
            return cor
    def find_corner_in_full_scale(self,point):
        point= self.m_d.scale_up(point)
        scale = self.m_d.scale
        self.m_d.set_scale(0)
        gray_img = self.m_d.gray_img
        canny_img = self.m_d.canny_img
        x,y = point
        cr = correct_rectangle((x-5,y-5,10,10), cv.GetSize(gray_img))
        for img in [gray_img,canny_img]:
            cv.SetImageROI(img, cr)
        cv.Canny(gray_img, canny_img, 300, 500)
        conts = cv.FindContours(canny_img, cv.CreateMemStorage(),
                                cv.CV_RETR_LIST,(cr[0],cr[1]))
        db.DrawContours(self.m_d.tmp_img, conts, (255,255,255), (128,128,128), 10)
        min =10
        min_point = None
        while conts:
            for c in  conts:
                vec = vector(point,c)
                len =length(vec)
                if len<min:
                    min = len
                    min_point = c

            conts.h_next()
        self.m_d.set_scale(scale)
        return min_point


    def _improve_corners(self, new_corners):
        '''
        new corners are made only from small rectangles, that means that corners
        arms are very short, and we should expand them as far as we can
        @param new_corners: list of corners
        '''
        L = len(new_corners)
        ncorners = list(new_corners)
        #print 'improve'
        crit = (cv.CV_TERMCRIT_EPS + cv.CV_TERMCRIT_ITER, 30, 0.1)
        cv.ResetImageROI(self.gray_img)
        for i, cor in enumerate(new_corners):
            if cor is not None:
                #TODO Check efficiency, maybe we should do it once for all corners?
                ncorners[i] = self._improve_corner(new_corners, i)
                if ncorners[i] is None and i > 0: #this corner is not valid
                    #previous corner was already improved by wrong data
                    #we have to correct that
                    ncorners[i - 1] = self._improve_corner(new_corners, i - 1)

        if self.m_d<>0:
            scale_factor = 1<<self.m_d.scale
            for cor in ncorners:
                if cor is not None:
                    cor.scale_up(self.m_d)
                    cor.p = cv.FindCornerSubPix(self.gray_img, [cor.p],
                                                (scale_factor+1, scale_factor+1), (0, 0), crit)[0]
        return ncorners


    def _predict_one(self, index, new_corners):
        '''
        predict position of corner index
        @param index:
        @param new_corners:
        '''
        # predicting by taking vectors form near corners along the sides
        # and solving linear equation for intersection
        L = len(new_corners)
        nb = (index + 1) % L
        b = new_corners[nb]
        nd = (index - 1 + L) % L
        d = new_corners[nd]
        assert isinstance(b, Corner)
        v1 = b.get_prediction_vector(True, self.corners[nb])
        v2 = d.get_prediction_vector(False, self.corners[nd])
        p1 = b.p
        p2 = d.p
        (p, _) = solve_linear(v1, v2, p1, p2)
        point = add(b.p, v1, p)
        cor = Corner([d.p, point, b.p], imgtime=b.time)
        cor.compute_change(self.corners[index])
        cor.is_predicted = True
        if cor.similarity < self.avg_sim * 2:
            new_corners[index] = cor


    def _predict_diagonally(self, a, b, new_corners):
        self._predict_one(a, new_corners)
        self._predict_one(b, new_corners)

    def _predict_neighbours(self, a, b, new_corners):
        if a == b + 1 or (b == 3 and a == 0):
            a, b = b, a
        na = (a + 3) % 4
        v1 = new_corners[na].get_prediction_vector(False, self.corners[na])
        nb = (b + 1) % 4
        v2 = new_corners[nb].get_prediction_vector(True, self.corners[nb])
        ap = add(new_corners[na].p, v1)
        bp = add(new_corners[nb].p, v2)

        cor_a = Corner([new_corners[na].p, ap, bp], 1,
                                imgtime=new_corners[na].time)
        cor_b = Corner([ap, bp, new_corners[nb].p], 1,
                                imgtime=new_corners[na].time)
        cor_b.is_predicted = cor_a.is_predicted = True

        cor_a.compute_change(self.corners[a], self.image)
        cor_b.compute_change(self.corners[b], self.image)
        if cor_a.different:
            if cor_b.different: return
            else:
                new_corners[b] = cor_b
                self._predict_one(a, new_corners)
        else:
            new_corners[a] = cor_a
            if cor_b.different:
                self._predict_one(b, new_corners)
            else:
                new_corners[b] = cor_b

    def _predict_from_one(self, a, new_corners):
        vec = new_corners[a].get_prediction_vector(True, self.corners[a])
        pa = (a + 3) % 4
        p1 = add(new_corners[a].p, vec)
        vec = (-vec[0],-vec[1])
        vec=rotateVec(vec, self.corners[pa].angle)
        pp1= add(p1,vec)
        cor_p = Corner([pp1, p1, new_corners[a].p], 1,
                                 imgtime=new_corners[a].time)

        vec = new_corners[a].get_prediction_vector(False, self.corners[a])
        na = (a + 1) % 4
        p2 = add(new_corners[a].p, vec)
        vec = (-vec[0],-vec[1])
        vec=rotateVec(vec, self.corners[na].angle)
        np2= add(p1,vec)
        cor_n = Corner([new_corners[a].p, p2, np2], 1,
                                 imgtime=new_corners[a].time)
        cor_p.is_predicted = cor_n.is_predicted = True
        cor_p.compute_change(self.corners[pa], self.image)
        cor_n.compute_change(self.corners[na], self.image)
        da= (a + 2) % 4
        if cor_p.different:
            if cor_n.different: return
            else:
                new_corners[na] = cor_n
                self._predict_neighbours(pa, da, new_corners)
        else:
            new_corners[pa] = cor_p
            if cor_n.different:
                self._predict_neighbours(na, da, new_corners)
            else:
                new_corners[na] = cor_n
                self._predict_one(da, new_corners)

    def validate_corners(self, new_corners):
        L = len(new_corners)
        not_valid = [0] * L
        for i, cor1 in enumerate(new_corners):
            cor2 = new_corners[(i + 1) % L]
            if cor1 is None or cor2 is None: continue
            v1p, v1n = cor1.vp, cor1.vn
            v2p, v2n = cor2.vp, cor2.vn
            v12 = vector(cor1.p, cor2.p)
            v21 = vector(cor2.p, cor1.p)
            v12a = vectorAngle(v1p, v12)
            v21a = vectorAngle(v2n, v21)
            min1a, max1a = get_angle_range(v1p, v1n, 1)
            min2a, max2a = get_angle_range(v2n, v2p, 1)
            if not (min1a < v12a < max1a) or not (min2a < v21a < max2a):
                if cor1.similarity < cor2.similarity:
                    not_valid[(i + 1) % L] += 1
                else:
                    not_valid[i] += 1
        for i in range(L):
            if not_valid[i] > 0:
                db.pr(["corner ", new_corners[i], "not_valid with score",
                       not_valid[i]], "validate_corners")
                new_corners[i] = None
        db.pr(not_valid, "validate_corners")
        pass
    def _predict_corners(self, new_corners):
        unknown = []
        for i in range(4):
            if new_corners[i] is None:
                unknown.append(i)
        l = len(unknown)
        #depending on what corners are missing we are trying to predict them
        if l == 0 :
            return new_corners
        elif l == 1:
            c = unknown[0]
            return self._predict_one(c, new_corners)
        elif l == 2:
            (a, b) = (unknown[0], unknown[1])
            if (a + 2 == b):
                return self._predict_diagonally(a, b, new_corners)
            else:
                return self._predict_neighbours(a, b, new_corners)
        elif l == 3:
            for i in range(4):
                if i not in unknown:
                    return self._predict_from_one(i, new_corners)
        else:
            return new_corners

    def predict_corners(self, new_corners):
        '''
        If in new_corners are Nones then this function tries to predict where
        not found corners are
        @param new_corners:
        '''
        db.db_break()
        new_corners = self._improve_corners(new_corners)
        self.validate_corners(new_corners)
        corners = filter(lambda x: x is not None, new_corners)
        def cmp(x, y):
            if  x.similarity > y.similarity:
                return  1
            else: return - 1
        corners = sorted(corners, cmp)
        self.avg_sim = reduce(lambda x, y: x + y.similarity, corners, 0)
        while len(corners) > 0:
            ncorners = list(new_corners)
            self.avg_sim /= len(corners)
            self._predict_corners(ncorners)
            if all(ncorners):
                if cv.CheckContourConvexity([x.p for x in ncorners]) == 1:
                    le = len(ncorners)
                    for i,c in enumerate(ncorners):
                        n= (i+1)%le
                        ncorners[n].prev = c.p
                        c.next = ncorners[n].p
                    for c in ncorners:c.measure()
                    return ncorners
            last = corners[-1]
            new_corners[last.id] = None
            self.avg_sim = self.avg_sim * len(corners) - last.similarity
            corners.remove(last)

        return None



if __name__ == '__main__':
    img = cv.CreateImage((100, 100), 8, 1)
    a = (50, -10)
    b = (85, 50)
    c = (50, 90)
    d = (5, 50)
    cv.FillConvexPoly(img, [a, b, c, d], (255, 255, 255))
    temp = 'temp'
    cv.NamedWindow(temp)

    oa, ob, oc, od = (48, -8), (80, 50), (48, 88), (0, 50)
    points = [oa, ob, oc, od]
    corners = [Corner(points, 0), Corner(points, 1), Corner(points, 2), Corner(points, 3)]
    CP = CornerPredictor(corners, 50, img)

    cv.PolyLine(img, [[oa, ob, oc, od]], 1, (150, 100, 100))

    dimg = cv.CreateImage((200, 200), 8, 1)
    cv.PyrUp(img, dimg)
    cv.ShowImage(temp, dimg)
    cv.WaitKey(10000)






