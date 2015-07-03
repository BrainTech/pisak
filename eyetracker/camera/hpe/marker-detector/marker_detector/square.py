'''
Created on Mar 31, 2010

@author: user
'''
import cv

from vectors import *
from corner_predictor import CornerPredictor
from utils import standarize_contours
from marker import Marker, MAX_SEEN
from corner import Corner, NOT_SIMILLAR,BLACK_WHITE_DIFFERENCE
import debug as db
import corner

PHASES = 1
SQ_SIZE = 50
MAX_SIDE_DIFF = 0.5
REQUIRED_CORRECTNESS = 0.5
BORDER_ONLY = True

class Square(Marker):
    GRID_SIZE = 3
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOT_RIGHT = 2
    BOT_LEFT = 3
    FAILED = 4
    binTreshold = 30
    code_points = [(1, 0), (0, 1), (1, 1), (1, 2), (2, 1)]

    def __init__(self, code_nr=None):
        Marker.__init__(self,code_nr)
        if code_nr is not None:
            self.init(code_nr)

    def init(self,ident):
        ident=int(ident)
        if self.ident>(1<<self.GRID_SIZE**2-4)-1 or self.ident<0:
            return None
        size = self.GRID_SIZE + 2
        self.code = cv.CreateMat(size, size, cv.CV_8SC1)
        cv.Zero(self.code)
        for p in self.code_points:
            self.code[p[0]+1,p[1]+1]=ident%2
            ident/=2
        self.code[1,size-2]=1
        self.code[size-2,1]=1
        self.code[size-2,size-2]=1
        self.border = [0]*(4*size)
        for i in range(size):
            self.border[i]=(0,i)
            self.border[i+size]=(i,size-1)
            self.border[i+2*size]=(size-1,size-i-1)
            self.border[i+3*size]=(size-1-i,0)


    def set_new_position(self, points, offset=True,scale=1):
        res = Marker.set_new_position(self, points, offset,scale)
        le = len(points)
        if le<0 or type(points[0])<>tuple: return res
        for i, cor in enumerate(self.corners):
            cor.diag = vector(cor.p, points[(i + 2) % le])
            cor.set_colors(self.m_d.draw_img)
        return res




    @staticmethod
    def generate(ident,sp=SQ_SIZE):
        size = (Square.GRID_SIZE + 4) * sp
        img = cv.CreateImage((size, size), 8, 1)
        rim = [(0, 0), (size, 0), (size, size), (0, size)]
        border = [(sp, sp), (size - sp, sp), (size - sp, size - sp), (sp, size - sp)]
        inside = [(sp * 2, sp * 2), (sp * 5, sp * 2), (sp * 5, sp * 5), (sp * 2, sp * 5)]
        square = lambda (x, y): [((2 + x) * sp, (2 + y) * sp), ((3 + x) * sp, (2 + y) * sp),
                                ((3 + x) * sp, (3 + y) * sp), ((2 + x) * sp, (3 + y) * sp)]
        corners = [square((0, 0))]
                   #square(size-sp*2,sp*2),
                   #square(size-sp*2,size-sp*2), square(sp*2,size-sp*2)]
        code = []
        id = ident
        for p in Square.code_points:
            if ident % 2 == 0: code.append(square(p))
            ident /= 2
        cv.FillPoly(img, [rim], (255, 255, 255))
        cv.FillPoly(img, [border], (0, 0, 0))
        cv.FillPoly(img, [inside], (255, 255, 255))
        cv.FillPoly(img, corners + code, (0, 0, 0))
        font = cv.InitFont(cv.CV_FONT_HERSHEY_COMPLEX_SMALL, 0.7, 0.7)
        cv.PutText(img, "%d" % id, (0, 15), font, (50, 50, 50))
        return img
    def generate_img(self):
        return Square.generate(self.ident)
    def check_contours(self, conts,scale_factor):
        if not conts.v_next():
            #proper square has white holes
            return False

        conts = self._get_approx(conts)
        if (len(conts) != 4):
            # proper square has 4 sides
#            print "wrong sides"
            return False
        oconts = list(conts)
        conts = [(x*scale_factor,y*scale_factor) for x,y in conts]
        conts = standarize_contours(conts)
        ans, data = self._check_rectangle(conts,scale_factor)
        if ans is False: # this isnt proper square marker
            db.PolyLine(self.m_d.draw_img, [conts], True, (255, 255, 0),data)
            return False
        db.PolyLine(self.m_d.draw_img, [conts], True, (255, 255, 0),None)

        (ident, rotation) = data
        rect = conts[rotation:] + conts[:rotation]
        if ident == self.ident: #we found it!
            self.set_new_position(rect,scale=scale_factor)
            return True
        else: # we found square marker but with different identifier
            return (int(ident), rect)


    def check_conts_with_hint(self, conts, hint,scale):
        (ident, rect) = hint
        if ident == self.ident and self.last_seen<>self.m_d.time:
            self.set_new_position(rect,scale=scale)
            return True
        else:
            return False

    def _check_rectangle(self, rect,scale_factor):
        '''
        Checks if rectangle is a good square marker
        @param rect:
        '''
        if cv.CheckContourConvexity(rect) != 1:
            return False, 'conv'
        area = abs(cv.ContourArea(rect))
        if area < SQ_SIZE:
            return False, 'area %d' % area

        orientation, code = self._decode_rect(rect)

        if orientation == self.FAILED:
            return False, 'no_corner: '+str(code)
        else:
            return True, (code, orientation)

    def _rotate_code(self, cod, ori):
        '''
        Rotates matrix cod depending on the value of ori
        @param cod:
        @param ori:
        '''
        if ori == self.TOP_LEFT:
            pass
        elif ori == self.TOP_RIGHT:
            cv.Transpose(cod, cod)
            cv.Flip(cod)
            return cod
        elif ori == self.BOT_RIGHT:
            cv.Flip(cod, cod, -1)
        else:
            cv.Transpose(cod, cod)
            cv.Flip(cod, cod, 1)

    def _find_first_corner(self, code,offset=0):
        '''
        looks where exactly one black corner (first) lies and return position
        @param code: matrix of ones and zeroes
        '''
        div = self.GRID_SIZE-1+offset
        a = code[offset, offset] == 1
        b = code[offset, div] == 1
        c = code[div, offset] == 1
        d = code[div, div] == 1
        if (a, b, c, d) == (False, True, True, True):
            return self.TOP_LEFT
        elif (a, b, c, d) == (True, False, True, True):
            return self.TOP_RIGHT
        elif (a, b, c, d) == (True, True, False, True):
            return self.BOT_LEFT
        elif (a, b, c, d) == (True, True, True, False):
            return self.BOT_RIGHT
        else:
            return self.FAILED

    def code_correctness(self,points,code=None,outsiders=None,code_m=None):
        gs = self.GRID_SIZE+2
        if code is None:
            code,outsiders = self._extract_code(points,gs, 0.5,self.m_d.draw_img)
        if BORDER_ONLY:
            colors = [0]*(4*gs)
            def get_colors(col1,col2,offset):
                col_change = [(x-y)/(gs-1) for x,y in zip(col1,col2)]
                for i in range(gs):
                    colors[offset+i]=[c+i*change for c,change in zip(col1,col_change)]
            get_colors(self.corners[0].color_black,self.corners[1].color_black,0)
            get_colors(self.corners[1].color_black,self.corners[2].color_black,gs)
            get_colors(self.corners[2].color_black,self.corners[3].color_black,2*gs)
            get_colors(self.corners[3].color_black,self.corners[0].color_black,3*gs)
            all = 4*gs
            correct = all

            for (x,y),col in zip(self.border,colors):
                if (x,y) in outsiders:
                    all-=1
                    correct-=1
                else:
                    c = code[x*gs+y]
                    for c1, c2 in zip(c,col):
                        if abs(c1-c2)>corner.MAX_COLOR_DIFFERNCE:
                            correct-=1
                            break
        else:
            correct = 0
            all = gs*gs
            if code_m is not None:
                code=code_m
            else:
                code= self._get_code_matrix(code, gs)
            if code is None: return 0
            for x,y in outsiders:
                code[x,y]=2
            for i in range(gs):
                for j in range(gs):
                    if code[i,j]==self.code[i,j]: correct+=1
                    elif code[i,j] == 2: all-=1
        if all==0:
            return 1.0
        return float(correct)/(all)


    def _extract_code(self,rect,gs,offset,img):
        gsf=float(self.GRID_SIZE+2)
        code = []
        (a, b, c, d) = (rect[0], rect[1], rect[2], rect[3])
        aa = ((d[0] - a[0]) / gsf, (d[1] - a[1]) / gsf)
        bb = ((c[0] - b[0]) / gsf, (c[1] - b[1]) / gsf)
        # lets first check if this is white_square in black or black in white
        #white_pixel = draw_img[int(a[0]- 0.5*aa[0]),int(a[1]-0.5*aa[1])]
        #black_pixel = draw_img[int(a[0]+ 0.5*aa[0]),int(a[1]+0.5*aa[1])]
        #if (white_pixel<black_pixel):
        #    return self.FAILED,0
        a = (a[0] + offset * aa[0], a[1] + offset * aa[1])
        b = (b[0] + offset * bb[0], b[1] + offset * bb[1])
        wx,wy=cv.GetSize(img)
        outsiders = []
        for i in range(0, gs):
            p1 = (a[0] + i * aa[0], a[1] + i * aa[1])
            p2 = (b[0] + i * bb[0], b[1] + i * bb[1])
            cc = ((p2[0] - p1[0]) / gsf, (p2[1] - p1[1]) / gsf)
            p1 = (p1[0] + offset * cc[0], p1[1] + offset * cc[1])
            for j in range(0, gs):
                x,y = (int(p1[0] + j * cc[0]), int(p1[1] + j * cc[1]))
                v=(0,0,0)
                if x<0  or x>=wx or y<0 or  y>=wy:
                    outsiders.append((i,j))
                else:
                    v = cv.Get2D(img, y,x)
                    cv.Circle(self.m_d.draw_img, (x,y), 2, (0, 255, 0))
                code.append(v)

        return code,outsiders
    def _get_code_matrix(self,codel,gs):
        code = cv.CreateMat(gs, gs, cv.CV_8UC1)
        min, max = 255,0
        for i,c in enumerate(codel):
            code[i/gs,i%gs]=c[0]
            if c[0]>max:max=c[0]
            if c[0]<min:min=c[0]


        if (max - min < BLACK_WHITE_DIFFERENCE):
            # this means that this square is all black or all white,
            # or the contrast is too low
            return None
        cv.Threshold(code, code, self.binTreshold, 1, cv.CV_THRESH_OTSU)
        return code

    def _decode_rect(self, rect):
        '''
        Reads binary code within rect using draw_img image
        Returns orientation of the code and decoded code
        @param rect: rectangle to use
        '''
        gs = self.GRID_SIZE+2
        codel,_ = self._extract_code(rect, gs, .5,self.m_d.gray_img)

        code =self._get_code_matrix(codel, gs)
        if code is None:
            return self.FAILED, 0
        bor=0
        for b in self.border:
            if code[b[0],b[1]]==0:
                bor+=1;
        if bor<len(self.border)-1:
            return self.FAILED,0

        first = self._find_first_corner(code,1)
        if first == self.FAILED:
            return self.FAILED, 0

        self._rotate_code(code, first)

        dec = 0
        if self.m_d.flip_H:
            cv.Transpose(code, code)
        for (x, y) in reversed(self.code_points):
            dec *= 2
            dec += cv.Get2D(code, y+1, x+1)[0]
        return first, dec



    def find_corners(self):
        '''
        Tries to find corners or to predict them. Return empty list,
        if every corner is found, or list of points in the area which tell where
        to do futher checking
        '''
        time = self.m_d.time
        if time-self.last_seen >= MAX_SEEN:
            return False
        #cv.ResetImageROI(draw_img)
        ncorners = []
        bounds = []
        for c in self.corners:
            db.db_break("find_corners")
            cands = c.get_candidates(self.m_d)
            min = NOT_SIMILLAR;
            bestcand = None;
            for cand in cands:
                if cand.similarity < min:
                    min = cand.similarity;
                    bestcand = cand
            ncorners.append(bestcand)
            bounds.extend(cvrect(cv.GetImageROI(self.m_d.bw_img)))
            if bestcand is None:
                pass

        db.pr([ncorners], "find_corners")
        for cor in ncorners:
            if cor is not None:
                cor.draw(self.m_d.tmp_img)
        if None in ncorners:
            pass
        CP = CornerPredictor(self.corners, time, self.m_d)
        ncorners = CP.predict_corners(ncorners)
        db.pr([ncorners], "new corners")
        if ncorners is not None:
            points = [x.p for x in ncorners]
            correctness = self.code_correctness(points)
            if correctness>REQUIRED_CORRECTNESS:
                self.set_new_position(ncorners)
                return True
            else:
                db.PolyLine(self.m_d.tmp_img,[points], True, (255,255,255),
                            "%.2f"%correctness)
        self.m_d.borders.extend(CP.bounds)
        return False

    def _get_bounding_rects(self, phase, time):
        '''
        Return rectangle where to look for this marker
        @param phase:
        @param time:
        '''
        nrect = []
        for cor in self.corners:
            (x, y, wx, wy) = cor.get_rectangle(time)
#            print (x, y, wx, wy)
            nrect.extend([(x, y), (x + wx, y + wy)])
#        print nrect
        rect = cv.BoundingRect(nrect)
#        print rect
        return [rect]

    def get_identifier(self):
        return "sq%d" % self.ident
    identifier = property(get_identifier, None, "Square's identifier")

if __name__ == '__main__':
    for i in range(32):
        img = Square.generate(i)
        cv.SaveImage("resources/square_%d.jpg" % i, img)
