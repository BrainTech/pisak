'''
Created on 20-02-2011

@author: Macias
'''
from marker import Marker
from square import Square
import cv
from marker_detector import SquareDetector
import debug as db
import vectors as v
import math

image=None

MAX_DISTANCE=32*32*4
BORDER_ACCURACY=0.25
CONFLICT_THRESHOLD=3

class QRMarker(Square):

    def __init__(self,name):
        '''
        Constructor
        '''
        Marker.__init__(self, name)
        self.black_inside=-1
        self.GRID_SIZE=2
        self.rot_conflict=0
#    def check_contours(self,conts,scale):
#        if not conts.v_next():
#            #proper square has white holes
#            return False
#        next = conts.v_next()
#        if not next.v_next() or next.h_next():
#            return False
#        next=next.v_next()
#        if not next.v_next() or next.h_next():
#            return False
#        next=next.v_next()
#        if not next.v_next() or next.h_next():
#            return False
#        next=next.v_next()
#        if not next.v_next() or next.h_next():
#            return False
#        next_n=next.v_next()
##        if next_n.v_next() or next_n.h_next():
##            return False
#        conts = self._get_approx(conts)
#        if (len(conts) != 4):
#            #proper square has 4 sides
#            print "not square" 
#            return False
#        print "set_position"
#        self.set_new_position(conts)
#        self.draw(image)
#        return False
#    def get_line(self,p1,p2,img):
#        li=cv.InitLineIterator(img, p1, p2,4)
#        list=[]
#        for c in li:
#            list.append(c)
#        return list
    def code_correctness(self,points,code=None,outsiders=None,code_m=None):
        return 1
        pass
    def set_new_position(self, points, offset=True,scale=1):
        res = Marker.set_new_position(self, points, offset,scale)
        le = len(points)
        if le<0 or type(points[0])<>tuple: return res
        for i, cor in enumerate(self.corners):
            cor.diag = v.vector(cor.p, points[(i + 2) % le])
            cor.set_colors(self.m_d.img)
        return res
    def get_line(self,p1,p2,img):
        a,b = v.vector(p1, p2)
        if a>b:l=a
        else:l=b
        if l==0: return [],[]
        li=cv.InitLineIterator(img, p1, p2,8)
        points=[]
        for i,c in enumerate(li):
            points.append(c)
        l=len(points)
        if len(points)==0:
            return [],[]
        vec=(a/float(l),b/float(l))
        real_p=[]
        for i in range(l):
#            list.append(c)
#        for i in range(l):
            p=v.int_point(v.add(p1,vec,i))
            real_p.append(p)
#            points.append(img[p[1],p[0]]);
        return points,real_p
    
    def compress_line(self,line):
        nl=[]
        pop=line[0]
        line.append(0)
        count=0
        for i in line:
            if i!=pop: 
                nl.append(('B' if pop==1 else 'C',count))
                count=0
            count+=1
            pop=i
        return nl
    def check_begining(self,line,l):
        if len(line)<8:
#            print "Wrong length"
            return 0
        (a,b)=line[0]
        if a=='C' and b<3:
            line=line[1:]
            (a,b)=line[0]
        if (a=='B' and (b<4*l/32 or b>l/5)) or a=='C':
#           t "Wrong first segment:",(a,b)
            return 0
        c1=line[1][1]
        b1=line[2][1]
        cc=line[3][1]
        b2=line[4][1]
        c2=line[5][1]
        def the_same(a,b):
            return  a==b or (a<b and 2*a>=b) or (a>b and 2*b>=a)
        if sum([c1,c2,b1,b2,cc,line[0][1]])>5*l/11:
#            print "Segment to long"
            return 0
        if cc< max([c1,c2,b1,b2]):
#            print line[3]," is not max",max([c1,c2,b1,b2])
            return 0
#        if not the_same(c1,b1):
#            print line[1],"is not the same as ", line[2]
#            return 0
#        if not the_same(c2,b2):
#            print line[4],"is not the same as ", line[5]
#            return 0
        return 1
    def get_border_points(self,rect):
        black=[]
        white=[]
        vec1=v.vector(rect[0], rect[2])
        vec2=v.vector(rect[1], rect[3])
        real_p=[]
        f=2.0/32
        img=self.m_d.gray_img
        def get_points(p1,p2,f1,f2,points):
            a,b=self.get_line(v.add(p1, vec1, f1), v.add(p2,vec2,f2), img)
            points.extend(a)
            real_p.extend(b)
        def get_points_color(f,points):
            get_points(rect[0],rect[1],-f,-f,points)
            get_points(rect[2],rect[1],f,-f,points)
            get_points(rect[0],rect[3],-f,f,points)
            get_points(rect[2],rect[3],f,f,points)
        get_points_color(f,black)
        get_points_color(-f,white)
        return black,white,real_p
        
    def threshold_lines(self,lines):
        all_lines=sum(lines,[])
        tmp=cv.CreateImage((len(all_lines),1), 8, 1)
        for i,p in enumerate(all_lines):
            tmp[0,i]=p
        cv.Threshold(tmp, tmp, 0, 1, cv.CV_THRESH_OTSU)
        j=0
        for l in lines:
            for i in range(len(l)):
                l[i]=tmp[0,j]
                j+=1
    
    def draw_lines(self,img,rect=None,line=None,real_p=None):
        if rect is not None:
            font = cv.InitFont(cv.CV_FONT_HERSHEY_COMPLEX_SMALL, 1, 1)
            col=[255,0,0,255,255,0]
            for i in range(4):
                cv.Circle(img, rect[i], 2, col[i:i+3])
                cv.PutText(img, str(i), rect[i], font, col[i:i+3])

        w,h=cv.GetSize(img)            
        if line is not None and real_p is not None:
            line=sum(line,[])
            real_p=sum(real_p,[])
            for va,p in zip(line,real_p):
                x,y=p
                if x<w and y<h:
                    img[y,x]=(va*255,va*255,va*255)
    
    def get_assumed_rotation(self,rect):
        if self.is_found():
            values = self.get_points()
            min_d=(MAX_DISTANCE,rect,0)
            for i in range(4):
                nrect=rect[i:]+rect[:i]
                sumd=0
                
                for j,p in enumerate(values):
                    sumd+=v.dist_points(nrect[j], p)
                if sumd<min_d[0]:min_d=(sumd,nrect,i)
            if min_d[0]<MAX_DISTANCE:
#                print "min:",min_d
#                print "values:",values
                return min_d[2]  
        return self.FAILED      
    
    def _decode_rect(self,rect):
        img= self.m_d.draw_img
        cv.ResetImageROI(img)
        nrect=cv.FindCornerSubPix(self.m_d.gray_img, rect, (2,2), (-1,-1), (cv.CV_TERMCRIT_ITER | cv.CV_TERMCRIT_EPS, 10, 0.01))
        for i,p in enumerate(nrect):
            rect[i]=p
        lines=[]
        r=rect
        def add_line(a,b,c,d,factor):
            p1=v.add(r[a],v.vector(r[a],r[b]),factor)
            p2=v.add(r[c],v.vector(r[c],r[d]),factor)
            lines.append(((p1,p2),(a,c)))
        add_line(0,0,2,2,0)
        add_line(1,1,3,3,0)
        add_line(0,1,3,2,0.25)
        add_line(1,0,2,3,0.25)
        add_line(0,3,1,2,0.25)
        add_line(3,0,2,1,0.25)
        positions,values=[],[]
        for (p1,p2),_ in lines:
            pt,rpt=self.get_line(p1, p2, self.m_d.gray_img)
            values.append(pt)
            positions.append(rpt)
        for pt in values:
            if len(pt)<32*1.5:
                return self.FAILED,"to short %d"%len(pt)
           
        black,white,real_p=self.get_border_points(rect)
        self.threshold_lines(values+[black,white])
        self.draw_lines(img, rect,values +[black,white], positions+[real_p])
#        db.show(img, "draw_lines", 0, 0, 0)
        if sum(black)>BORDER_ACCURACY*len(black):
            return self.FAILED,"no black border"
        if sum(white)<(1-BORDER_ACCURACY)*len(white):
            return self.FAILED,"no white border"
          
        res=[0]*4
        for line,(_,(a,b)) in zip(values,lines):
            comp=self.compress_line(line)
            res[a]+=1 if self.check_begining(comp, len(line)) else 0
            comp.reverse()
            res[b]+=1 if self.check_begining(comp, len(line)) else 0
#        print res
        min_s=min(res)
        i=0;
        count=0
        while i<7:
            count=count+1 if res[i%4]>min_s else 0
            if count==3:
                break;
            i+=1
        if i==7:
            rotation=self.FAILED
        else:
            rotation=(i+3)%4
        ass_rot=self.get_assumed_rotation(rect)
        if rotation==self.FAILED:
#            print "Assumed rotation:",rotation
            return ass_rot,self.ident
        if ass_rot==self.FAILED:
            return rotation,self.ident 
        if ass_rot!=rotation:
#            print "Rotation conflict: assumed:%d, calculated: %d"
            self.rot_conflict+=1
            if self.rot_conflict<=CONFLICT_THRESHOLD:
#                print "Assumed used"
                rotation=ass_rot
        else: self.rot_conflict=0
        return rotation,self.ident 
        
#        return self.FAILED,0
    def get_identifier(self):
        return "QR %s"%self.ident
        
    identifier = property(get_identifier, None, "QR identifier")
        
        
if __name__=='__main__':
    from image_providers import CamImageProvider,MovieImageProvider
    ip=CamImageProvider(0,"test_data.avi")
    #ip=MovieImageProvider("test_data.avi",start_from=80)
    db.DEBUG=True
    #size=(200,200)
    img=ip.next()
    #image=cv.CreateImage(size, 8, 3)
    sd=SquareDetector(image)
    qr=QRMarker("QR")
    sd.add_marker(qr)
    while cv.WaitKey(1)!=27:
        image,img_time=ip.getImage()
        if image is None:
            break
    #    cv.SetImageROI(img, (0,0,200,200))
    #    cv.Copy(img,image)
    #    cv.ResetImageROI(img)
        sd.find_markers(image,img_time)
        sd.draw_markers(image)
    #    gray = cv.CreateImage((640,480), 8, 1)
    #    bw=cv.CloneImage(gray)
    #    cv.CvtColor(img, gray, cv.CV_BGR2GRAY)
    #    cv.Threshold(gray, bw, 128, 255, cv.CV_THRESH_OTSU)
        cv.ShowImage("temp", image)
        cv.ShowImage("draw", sd.draw_img)
        cv.ShowImage("canny", sd.canny_img)
        