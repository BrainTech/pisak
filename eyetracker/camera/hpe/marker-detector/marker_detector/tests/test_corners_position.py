'''
Created on 15-08-2010

@author: Macias
'''

from OpenGL.GL import * #@UnusedWildImport
from OpenGL.GLUT import * #@UnusedWildImport
from OpenGL.GLU import * #@UnusedWildImport
from cv import *
import debug as db #@UnusedImport
import pstats
from image_provider import CamImageProvider
from scene.camera import Camera
import math
from corner import Corner
play = True
stats = pstats.Stats("../resources/stats")
sb = None
frames =0
times= 0
profiling = False
rotx, roty, rotz, transx,transy,transz,cx,cy,cz = (0,0,0,0,0,-6.0,.1,.1,-.01)
rng = None
camera = None
points = [(0.0,0.0,0.0),(1.0,0.0,0.0),(1.0,1.0,0.0),(0.0,1.0,0.0)]
angle_min = math.pi
angle_max = 0
angle_diff_min = 100
angle_diff_max = 0
prop_min  = 40
prop_max = 0
rot_max = 0
from vectors import *
def stats(points):
    global prop_max,prop_min,angle_max,angle_min,rot_max,angle_diff_max,angle_diff_min
    a = length(vector(points[0],points[1]))
    b = length(vector(points[1],points[2]))
    c = length(vector(points[2],points[3]))
    d = length(vector(points[3],points[0]))
    if a>c:
        a,c = c,a
    if b>d:
        b,d = d,b
    if c == 0.0:
        pass
    else:
        #print "sides a/c:", a/c
        if (c-a)/c > prop_max: prop_max = (c-a)/c
        if (c-a)/c < prop_min: prop_min = (c-a)/c
    if d==0.0:
        pass
    else:
        #print "sides b/d", b/d
        if (d-b)/d > prop_max: prop_max =(d-b)/d
        if (d-b)/d < prop_min: prop_min = (d-b)/d
    corners = Corner.get_corners(points)
    for cor in corners:
        if cor.angle < angle_min:angle_min = cor.angle
        if cor.angle > angle_max:angle_max = cor.angle
        if cor.rotation > rot_max: rot_max = cor.rotation
    a,b,c,d = [c.angle for c in corners]
    if a>c:
        a,c=c,a
    if b>d:
        b,d=d,b
    if (c-a)/c > angle_diff_max: angle_diff_max=(c-a)/c
    if (c-a)/c< angle_diff_min: angle_diff_min = (c-a)/c
    #print "angle diff a/c", (c-a)/c
    if (d-b)/d > angle_diff_max: angle_diff_max=(d-b)/d
    if (d-b)/d< angle_diff_min: angle_diff_min = (d-b)/d
    #print "angle diff b/d", (d-b)/d
    if angle_diff_max > 0.90:
        pass

def draw():
    global rotx, roty, rotz, transx,transy,transz, frames,cx,cz,cy
    frames+=1
    glLoadIdentity()
    if frames%100==0:
        rotx=RandReal(rng)
        roty=RandReal(rng)
        rotz=RandReal(rng)
    glTranslate(transx+cx,transy+cy,transz+cz)
    glRotate(frames*5.0,rotx,roty,rotz)
    proj = [gluProject(p[0]-.5,p[1]-.5,p[2]) for p in points]
    minx= min(p[0] for p in proj)
    maxx= max(p[0] for p in proj)
    if minx<0 and maxx>640:
        cx = 0
    elif minx>=0 and maxx<640 and cx == 0:
        cx = RandReal(rng)-1
    elif minx<0:
        cx=RandReal(rng)*.5
    elif maxx>640:
        cx=-RandReal(rng)*.5
    minx= min(p[1] for p in proj)
    maxx= max(p[1] for p in proj)
    if minx<0 and maxx>480:
        cy=0
    elif minx>=0 and maxx<480 and cy == 0:
        cy = RandReal(rng)-1
    elif minx<0:
        cy=RandReal(rng)*.5
    elif maxx>480:
        cy=-RandReal(rng)*.5   
    transx+=cx
    transy+=cy
    transz+=cz*max(abs(transz/5),1)
    if transz<-60:
        cz=.05
    elif transz>-1:
        cz= -.05
    glLoadIdentity()
    glTranslate(transx,transy,transz)
    glRotate(frames*5.0,rotx,roty,rotz)
    glClearColor (0.0, 0.0, 0.0, 0.0) 
    glClear (GL_COLOR_BUFFER_BIT) 
    glBegin(GL_QUADS)
    for p in points:
        glColor3f (p[0], p[1], 1.0); 
        glVertex3f(p[0]-.5,p[1]-.5,p[2]) 
    glEnd(); 
    glutSwapBuffers()
    proj = [gluProject(p[0]-.5,p[1]-.5,p[2]) for p in points]
    if length(vector(proj[0],proj[1]))>3 and \
        length(vector(proj[1],proj[2]))>3 and \
        length(vector(proj[2],proj[3]))>3 and\
        length(vector(proj[3],proj[0]))>3: 
        stats(proj)
def print_stats():
    print "angle_min", angle_min
    print "angle_max", angle_max
    print "prop_min", prop_min
    print "prop_max", prop_max
    print "rot_max",rot_max
    print "angle_diff_min", angle_diff_min
    print "angle_diff_max",angle_diff_max
    
    
def key(k,x,y):
    global transx,transy,transz
    if k==101:
        transy+=0.05
    elif k==102:
        transx+=0.05
    elif k==103:
        transy-=0.05
    elif k==100:
        transx-=0.05
    elif k=="z":
        transz-=0.05
    elif k=="x":
        transz+=0.05
    elif ord(k)==27:
        print_stats()
        exit()
    pass

def reshape(width, height):
        '''
        Called after window reshape changes viewport and perspective
        @param width:
        @param height:
        '''
        global camera
        viewport = camera.get_openGL_viewport()
        glViewport(viewport[0],viewport[1],viewport[2],viewport[3])
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        project = camera.get_openGL_perspective()
        gluPerspective(project[0],project[1],project[2],project[3])
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()


def main():
    #ip = MovieImageProvider("resources/Video4.avi",0,70)
    global camera
    camera = Camera()
    camera.load_from_file("../resources/camera_params.xml")
    global rng
    rng= RNG()
    glutInit()
    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE)
    glutInitWindowPosition(2000, 0)
    glutInitWindowSize(640, 480)
    glutCreateWindow("AR")
    glShadeModel(GL_SMOOTH)
    glEnable(GL_DEPTH_TEST)    
    glutDisplayFunc(draw)
    glutReshapeFunc(reshape)
    
    def idle(int):
        glutPostRedisplay()
        glutTimerFunc(50,idle,0)
        
    glutKeyboardFunc(key)
    glutSpecialFunc(key)
    glutTimerFunc(50,idle,0)
    glutMainLoop()
    pass

if __name__ == '__main__':
    #print cProfile.run('main()')
    main()