'''
Created on Apr 20, 2010

@author: user
'''

import math
import cv

def normalize(v):
    """
    return vectorwith length 1 or (0,0) when v is (0,0)
    """
    (a, b) = v
    c = math.sqrt(a * a + b * b)
    if c == 0.0:
        return (0, 0)
    else:
        return (a / c, b / c)

def add(p1, p2, a=1):
    """
    Add two points or vectors with multiplier (v3=v1+a*v2)
    """
    return (p1[0] + a * p2[0], p1[1] + a * p2[1])

def vectorAngle(v1, v2):
    """
    Return angle between two vectors
    """
    n1 = normalize(v1)
    n2 = normalize(v2)
    tmp = n1[0] * n2[0] + n1[1] * n2[1]
    if tmp > 1.0: tmp = 1.0
    elif tmp < -1.0: tmp = -1.0
        
    return math.acos(tmp)

def rotateVec(v, angle):
    """
    Rotate vector v by angle (in radians)
    """
    (x, y) = v
    ca = math.cos(angle)
    sa = math.sin(angle)
    return (x * ca - y * sa, x * sa + y * ca)

def det(a, b, c):
    """
    This function gets a determinant of: 
        [a[0] a[1] 1]
        [b[0] b[1] 1]
        [c[0] c[1] 1]
    sign is eaqual to the sign of sinus between vectors ac and ab 
    c is on the left of ab when det >0 (in normal view - y axis goes up)
    """
    return (a[0] * b[1]) + (a[1] * c[0]) + (b[0] * c[1]) - (a[0] * c[1]) - (a[1] * b[0]) - (b[1] * c[0])

def vector(a, b):
    """
    Returns vector from points a to b
    """
    return (b[0] - a[0], b[1] - a[1])

def cvrect(r):
    (x, y, wx, wy) = r
    return ((x, y), (x + wx, y + wy))

def length(vec):
    """
    length of vector vec
    """
    return math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])

def r2d(a):
    """
    convert radians to degrees
    """
    return a * 180 / math.pi

def d2r(a):
    """
    convert angle a from degrees to radians
    """
    return a / 180.0 * math.pi

def rotate_point(point, center, angle):
    """
    rotates point by angle (in degrees) around center, returns new point
    """
    
    vec = vector(center, point)
    vec = rotateVec(vec, d2r(angle))
    return add(center, vec)

def rotate_points(points, center, angle):
    """
    rotates collection of points by angle around center, returns list of points
    """
    return map(lambda x:rotate_point(x, center, angle), points)

def int_point(p):
    '''
    convert float point to int point
    @param p:
    '''
    (a, b) = p
    return (int(a), int(b))

def dist_points(a, b):
    '''
    return square of distance between points a and b
    @param a: point
    @param b: point
    '''
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2    

def solve_linear(v1, v2, p1, p2):
    A = cv.CreateMat(2, 2, cv.CV_32FC1)
    B = cv.CreateMat(2, 1, cv.CV_32FC1)
    X = cv.CreateMat(2, 1, cv.CV_32FC1)
    cv.SetReal2D(A, 0, 0, v1[0])
    cv.SetReal2D(A, 1, 0, v1[1])
    cv.SetReal2D(A, 0, 1, -v2[0])
    cv.SetReal2D(A, 1, 1, -v2[1])
    cv.SetReal2D(B, 0, 0, p2[0] - p1[0])
    cv.SetReal2D(B, 1, 0, p2[1] - p1[1])
    cv.Solve(A, B, X)
    p = cv.Get2D(X, 0, 0)
    q = cv.Get2D(X, 1, 0)
    #print 'solving p1=',p1,'v1=',v1,'p2=',p2,'v2=',v2,'result=',(p[0],q[0])
    return (p[0], q[0])

def get_angle_range(base, arm, pixels=0.5):
    '''
    Returns angle range created by base and arm considering pixel accuracy
    @param base:
    @param arm:
    '''
    if length(arm) < pixels:
        return 0, math.pi
    a, b = arm
    angles = [vectorAngle(base, (a - pixels, b - pixels)),
       vectorAngle(base, (a + pixels, b - pixels)),
       vectorAngle(base, (a + pixels, b + pixels)),
       vectorAngle(base, (a - pixels, b + pixels))]
    return min(angles), max(angles)

def middle(p1,p2):
    '''
    Returns middle point of segment p1-p2
    @param p1:
    @param p2:
    '''
    return ((p1[0]+p2[0])/2,(p1[1]+p2[1])/2)

def point_on_edge(point, rect):
    (a, b) = point
    (x, y, wx, wy) = rect
    return a < x + 2 or b < y + 2 or a + 3 > x + wx or b + 3 > y + wy

def scale(point, scale_f):
    return point[0] * scale_f, point[1] * scale_f
