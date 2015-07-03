/*
 * This file is part of Head Pose Estimation.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 * Copyright 2015, Alex Khrabrov <alex@mroja.net>
 *
 */

/*
 * This code uses SolidTetrahedron drawing code from FreeGLUT.
 *
 * FreeGLUT Copyright (c) 1999-2000 Pawel W. Olszta. All Rights Reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included
 * in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
 * PAWEL W. OLSZTA BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
 * IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

#include <QDir>
#include <QDebug>
#include <QHBoxLayout>

#include "hpewidget.h"
#include "glm.h"

#include "opencvcapture.h"

#include <GL/glu.h>

#include <boost/algorithm/string.hpp>

static void drawSolidCylinder(GLdouble radius,
                              GLdouble height,
                              GLint slices,
                              GLint stacks)
{
    GLUquadricObj * qobj = gluNewQuadric();
    gluQuadricDrawStyle(qobj, GLU_FILL);
    gluCylinder(qobj, radius, radius, height, stacks, slices);
    gluDeleteQuadric(qobj);
}

static void drawSolidTetrahedron(void)
{
    /* Magic Numbers:  r0 = ( 1, 0, 0 )
     *                 r1 = ( -1/3, 2 sqrt(2) / 3, 0 )
     *                 r2 = ( -1/3, -sqrt(2) / 3, sqrt(6) / 3 )
     *                 r3 = ( -1/3, -sqrt(2) / 3, -sqrt(6) / 3 )
     * |r0| = |r1| = |r2| = |r3| = 1
     * Distance between any two points is 2 sqrt(6) / 3
     *
     * Normals:  The unit normals are simply the negative of the coordinates of the point not on the surface.
     */

    const double r0[3] = {             1.0,             0.0,             0.0 };
    const double r1[3] = { -0.333333333333,  0.942809041582,             0.0 };
    const double r2[3] = { -0.333333333333, -0.471404520791,  0.816496580928 };
    const double r3[3] = { -0.333333333333, -0.471404520791, -0.816496580928 };

    glBegin(GL_TRIANGLES);
        glNormal3d(-1.0, 0.0, 0.0);
        glVertex3dv(r1);
        glVertex3dv(r3);
        glVertex3dv(r2);
        glNormal3d(0.333333333333, -0.942809041582, 0.0);
        glVertex3dv(r0);
        glVertex3dv(r2);
        glVertex3dv(r3);
        glNormal3d(0.333333333333, 0.471404520791, -0.816496580928);
        glVertex3dv(r0);
        glVertex3dv(r3);
        glVertex3dv(r1);
        glNormal3d(0.333333333333, 0.471404520791, 0.816496580928);
        glVertex3dv(r0);
        glVertex3dv(r1);
        glVertex3dv(r2);
    glEnd() ;
}

static void drawAxes()
{
    // Z = red
    glPushMatrix();
        glRotated(180, 0, 1, 0);
        glColor4d(1, 0, 0, 0.5);
        drawSolidCylinder(0.05, 1, 15, 20);
        glBegin(GL_LINES);
            glVertex3d(0, 0, 0);
            glVertex3d(0, 0, 1);
        glEnd();
        glTranslated(0, 0, 1);
        glScaled(0.1, 0.1, 0.1);
        drawSolidTetrahedron();
    glPopMatrix();

    // Y = green
    glPushMatrix();
        glRotated(-90, 1, 0, 0);
        glColor4d(0, 1, 0, 0.5);
        drawSolidCylinder(0.05, 1, 15, 20);
        glBegin(GL_LINES);
            glVertex3d(0, 0, 0);
            glVertex3d(0, 0, 1);
        glEnd();
        glTranslated(0, 0, 1);
        glScaled(0.1, 0.1, 0.1);
        drawSolidTetrahedron();
    glPopMatrix();

    // X = blue
    glPushMatrix();
        glRotated(-90, 0, 1, 0);
        glColor4d(0, 0, 1, 0.5);
        drawSolidCylinder(0.05, 1, 15, 20);
        glBegin(GL_LINES);
            glVertex3d(0, 0, 0);
            glVertex3d(0, 0, 1);
        glEnd();
        glTranslated(0, 0, 1);
        glScaled(0.1, 0.1, 0.1);
        drawSolidTetrahedron();
    glPopMatrix();
}

//--------------------------------------------------------------------------------------------------

HpeHeadWidget::HpeHeadWidget(QWidget * parent)
    : QOpenGLWidget(parent)
    , m_rot{0}
    , m_tv(3)
    , m_rv(3)
    , m_rvec(m_rv)
    , m_tvec(m_tv)
{
    // init Kalman filter
    //initKalmanFilter(KF, nStates, nMeasurements, nInputs, dt);
    //measurements.setTo(cv::Scalar(0));

    QDir dir(QDir::homePath());

    QString modelPath = dir.filePath("pisak/eyetracker/camera/hpe/head-obj.obj");
    m_headObj = glmReadOBJ(modelPath.toLocal8Bit().data());

    double avgX = 0, avgY = 0, avgZ = 0;
    for(GLuint i = 1; i <= m_headObj->numvertices; i++)
    {
        avgX += m_headObj->vertices[3 * i + 0];
        avgY += m_headObj->vertices[3 * i + 1];
        avgZ += m_headObj->vertices[3 * i + 2];
    }
    avgX /= m_headObj->numvertices;
    avgY /= m_headObj->numvertices;
    avgZ /= m_headObj->numvertices;

    std::cout << "model mean: " << avgX << " " << avgY << " " << avgZ << std::endl;

    for(GLuint i = 1; i <= m_headObj->numvertices; i++)
    {
        m_headObj->vertices[3 * i + 0] -= avgX;
        m_headObj->vertices[3 * i + 1] -= avgY;
        //m_headObj->vertices[3 * i + 2] -= avgZ;
    }

    // feature points (in head-obj.obj coordinates)
    std::vector<cv::Point3f> modelPoints;

    // four points
    modelPoints.push_back(cv::Point3f(85.60, 234.44, 20.02));
    modelPoints.push_back(cv::Point3f(-2.92, 238.53, 20.02));
    modelPoints.push_back(cv::Point3f(-8.02, 140.93, 20.02));
    modelPoints.push_back(cv::Point3f(80.74, 140.93, 20.02));

    // NOTE: modelPoints will be destroyed when this scope ends.
    //       We MUST copy the data.
    m_modelPoints3d = cv::Mat(modelPoints).clone();

    const cv::Scalar mean_point = cv::mean(cv::Mat(modelPoints));
    std::cout << "Mean point: " << mean_point << std::endl;
    m_modelPoints3d = m_modelPoints3d - mean_point;

    //assert(norm(mean(model_points_3d)) < 1e-05); //make sure is centered
    m_modelPoints3d = m_modelPoints3d + cv::Scalar(0, 0, 20.02);

    //std::cout << "model points:\n" << m_modelPoints3d << std::endl;

    m_rvec = cv::Mat(m_rv);

    double _d[9] = { 1,  0,  0,
                     0, -1,  0,
                     0,  0, -1 };

    cv::Rodrigues(cv::Mat(3,3,CV_64FC1, _d), m_rvec);

    m_tv[0] = 0;
    m_tv[1] = 0;
    m_tv[2] = 1;

    m_tvec = cv::Mat(m_tv);
}

void HpeHeadWidget::initializeGL()
{
    glEnable(GL_CULL_FACE);
    glCullFace(GL_BACK);

    glShadeModel(GL_SMOOTH);

    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LEQUAL);

    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    glEnable(GL_LIGHT0);
    glEnable(GL_NORMALIZE);
    glEnable(GL_COLOR_MATERIAL);
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE);

    const GLfloat light_ambient[]  = { 0.0f, 0.0f, 0.0f, 1.0f };
    const GLfloat light_diffuse[]  = { 1.0f, 1.0f, 1.0f, 1.0f };
    const GLfloat light_specular[] = { 1.0f, 1.0f, 1.0f, 1.0f };
    const GLfloat light_position[] = { 0.0f, 0.0f, 1.0f, 0.0f };

    const GLfloat mat_ambient[]    = { 0.7f, 0.7f, 0.7f, 1.0f };
    const GLfloat mat_diffuse[]    = { 0.8f, 0.8f, 0.8f, 1.0f };
    const GLfloat mat_specular[]   = { 1.0f, 1.0f, 1.0f, 1.0f };
    const GLfloat high_shininess[] = { 100.0f };

    glLightfv(GL_LIGHT0, GL_AMBIENT,  light_ambient);
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  light_diffuse);
    glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular);
    glLightfv(GL_LIGHT0, GL_POSITION, light_position);

    glMaterialfv(GL_FRONT, GL_AMBIENT,   mat_ambient);
    glMaterialfv(GL_FRONT, GL_DIFFUSE,   mat_diffuse);
    glMaterialfv(GL_FRONT, GL_SPECULAR,  mat_specular);
    glMaterialfv(GL_FRONT, GL_SHININESS, high_shininess);

    glEnable(GL_LIGHTING);

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
}

void HpeHeadWidget::paintGL()
{
    // draw the image in the back
    int vPort[4];
    glGetIntegerv(GL_VIEWPORT, vPort);

    glClear(GL_COLOR_BUFFER_BIT);

    //glEnable2D();
    //drawOpenCVImageInGL(tex_l);
    //glTranslated(vPort[2]/2.0, 0.0, 0.0);
    //drawOpenCVImageInGL(tex_r);
    //glDisable2D();

    glClear(GL_DEPTH_BUFFER_BIT); // we want to draw stuff over the image

    // draw only on left part
    glViewport(0, 0, vPort[2]/2, vPort[3]);

    glPushMatrix();

        gluLookAt(0, 0, 0, 0, 0, 1, 0, -1, 0);

        // put the object in the right position in space
        glTranslated(m_tv[0], m_tv[1], m_tv[2]);

        const GLdouble ogl_rotation_matrix[16] = {
            m_rot[0], m_rot[1], m_rot[2], 0,
            m_rot[3], m_rot[4], m_rot[5], 0,
            m_rot[6], m_rot[7], m_rot[8], 0,
            0,	      0,	    0,        1
        };

        glMultMatrixd(ogl_rotation_matrix);

        // draw the 3D head model
        glColor4f(1, 1, 1, 0.75);
        glmDraw(m_headObj, GLM_SMOOTH);

        glDisable(GL_DEPTH_TEST);
        glColor4f(0, 1, 0, 0.6);
        glBegin(GL_QUADS);
            for(int i = 0; i < 4; i++)
               glVertex3f(m_modelPoints3d.at<float>(i, 0),
                          m_modelPoints3d.at<float>(i, 1),
                          m_modelPoints3d.at<float>(i, 2));
        glEnd();
        glEnable(GL_DEPTH_TEST);

        //----------Axes
        glScaled(100, 100, 100);
        drawAxes();

    glPopMatrix();

    // restore to looking at complete viewport
    glViewport(0, 0, vPort[2], vPort[3]);
}

void HpeHeadWidget::resizeGL(int width, int height)
{
    glViewport(0, 0, width, height);

    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    //const float ar = float(width) / float(height);
    //glFrustum(-ar, ar, -1.0, 1.0, 2.0, 100.0);
    gluPerspective(47, 1.0, 0.01, 1000.0);

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
}

std::vector<cv::Point2f> HpeHeadWidget::estimatePose(
        const std::vector<cv::Point2f> & markers,
        const cv::Mat & img)
{
    if(markers.size() < 4 || markers.size() > 4)
        return std::vector<cv::Point2f>();

    const double max_d = std::max(img.rows, img.cols);

    cv::Mat camMatrix = (
        cv::Mat_<double>(3,3) <<
            max_d, 0,     img.cols/2.0,
            0,	   max_d, img.rows/2.0,
            0,	   0,	  1.0
    );

    //std::cout << "cam matrix " << std::endl << camMatrix << std::endl;

    double _dc[] = { 0, 0, 0, 0};

    // CV_ITERATIVE,
    // CV_P3P - requires frour points
    // CV_EPNP

    // TODO: Kalman filter from:
    //	http://docs.opencv.org/trunk/doc/tutorials/calib3d/real_time_pose/real_time_pose.html

    cv::Mat ip(markers);

    //std::cout << "ip: " << ip << std::endl;
    //std::cout << "m_modelPoints3d: " << m_modelPoints3d << std::endl;

    cv::solvePnP(
        m_modelPoints3d,
        ip,
        camMatrix,
        cv::Mat(1, 4, CV_64FC1, _dc),
        m_rvec,
        m_tvec,
        true,
        CV_P3P
    );

    // second, iterative run
    cv::solvePnP(
        m_modelPoints3d,
        ip,
        camMatrix,
        cv::Mat(1, 4, CV_64FC1, _dc),
        m_rvec,
        m_tvec,
        true,
        CV_ITERATIVE
    );

    //std::cout << "rvec: " << m_rvec << std::endl;
    //std::cout << "tvec: " << m_tvec << std::endl;

    // convert rotation vector to rotation matrix
    cv::Mat rotM(3,3,CV_64FC1, m_rot);
    cv::Rodrigues(m_rvec, rotM);

    //std::cout << "rot vec:" << m_rvec << std::endl;

    double * _r = rotM.ptr<double>();

    //printf("rot mat: \n %.3f %.3f %.3f\n%.3f %.3f %.3f\n%.3f %.3f %.3f\n",
    //    _r[0],_r[1],_r[2],_r[3],_r[4],_r[5],_r[6],_r[7],_r[8]);

    //printf("trans vec: \n %.3f %.3f %.3f\n",tv[0],tv[1],tv[2]);

/*
    // Get the measured translation
    cv::Mat translation_measured(3, 1, CV_64F);
    translation_measured = tvec.clone();

    // Get the measured rotation
    cv::Mat rotation_measured(3, 3, CV_64F);
    rotation_measured = rotM.clone();

    // fill the measurements vector
    fillMeasurements(measurements, translation_measured, rotation_measured);

    // Instantiate estimated translation and rotation
    cv::Mat translation_estimated(3, 1, CV_64F);
    cv::Mat rotation_estimated(3, 3, CV_64F);

    // update the Kalman filter with good measurements
    updateKalmanFilter(KF, measurements,
                       translation_estimated, rotation_estimated);

    rotM = rotation_estimated;
    tvec = translation_estimated;
*/

    // original matrix
    /*
    const double _pm[12] = {
        _r[0],_r[1],_r[2], m_tv[0],
        _r[3],_r[4],_r[5], m_tv[1],
        _r[6],_r[7],_r[8], m_tv[2]
    };
    */

    const double _pm[12] = {
        _r[0],_r[1],_r[2], m_tv[0],
        _r[3],_r[4],_r[5], m_tv[1],
        _r[6],_r[7],_r[8], m_tv[2]
    };

    cv::Matx34d P(_pm);
    cv::Mat KP = camMatrix * cv::Mat(P);

    //std::cout << "KP " << std::endl << KP << std::endl;

    std::vector<cv::Point2f> reprojected_points(m_modelPoints3d.rows);

    // reproject object points to check validity of found projection matrix
    for(int i = 0; i < m_modelPoints3d.rows; i++)
    {
        cv::Mat_<double> X = (cv::Mat_<double>(4,1) <<
            m_modelPoints3d.at<float>(i,0), m_modelPoints3d.at<float>(i,1), m_modelPoints3d.at<float>(i,2), 1.0);
        // std::cout << "object point " << X << std::endl;
        cv::Mat_<double> opt_p = KP * X;
        cv::Point2f opt_p_img(opt_p(0)/opt_p(2), opt_p(1)/opt_p(2));
        // std::cout << "object point reproj " << opt_p_img << std::endl;
        reprojected_points[i] = opt_p_img;
    }

    rotM = rotM.t(); // transpose to conform with majorness of opengl matrix

    return reprojected_points;
}

HpeWidget::HpeWidget(QWidget * parent)
    : QWidget(parent)
{
    QDir dir(QDir::homePath());

    QString path = dir.filePath("pisak/eyetracker/camera/hpe/marker-detector/run_detector.py");
    QString cmd = "python \"" + path + "\"";
    qDebug() << cmd;
    m_tracker_process.reset(new redi::ipstream(cmd.toLocal8Bit().data(), m_tracker_process_mode));

    {
        std::string tmp;
        *m_tracker_process >> tmp;
        std::cout << tmp << std::endl;
    }

    if(!m_tracker_process->is_open())
        std::cerr << "Creating tracker process failed!" << std::endl;
    else
        std::cout << "Tracker process created!" << std::endl;

    markerDetectorWidget.setScaledContents(true);

    QHBoxLayout * layout = new QHBoxLayout;
    layout->addWidget(&headWidget);
    layout->addWidget(&markerDetectorWidget);
    setLayout(layout);

    m_timer.setInterval(10);
    m_timer.setSingleShot(false);

    QObject::connect(&m_timer, &QTimer::timeout, [=]() {
        idle();
    });

    m_timer.start();

    resize(1200, 200);
}

void HpeWidget::idle()
{
    std::string str;

    if(m_tracker_process && m_tracker_process->is_open())
        *m_tracker_process >> str;

    static std::vector<cv::Point2f> points;

    if(!str.empty() && str != "none")
    {
        //std::cout << "input line: " << str << std::endl;
        points.clear();

        std::vector<std::string> vals;
        boost::split(vals, str, boost::is_any_of("|;"));

        if(vals.size() >= 8)
        {
            float x1, x2, x3, x4, y1, y2, y3, y4;
            x1 = std::stof(vals[0]);
            y1 = std::stof(vals[1]);
            x2 = std::stof(vals[2]);
            y2 = std::stof(vals[3]);
            x3 = std::stof(vals[4]);
            y3 = std::stof(vals[5]);
            x4 = std::stof(vals[6]);
            y4 = std::stof(vals[7]);

            points.push_back(cv::Point2f(x4, y4));
            points.push_back(cv::Point2f(x3, y3));
            points.push_back(cv::Point2f(x2, y2));
            points.push_back(cv::Point2f(x1, y1));
        }
    }

    cv::Mat frame = cv::Mat::zeros(480, 640, CV_8UC3);

    if(points.size() >= 4)
    {
        cv::circle(frame, points[0], 3, cv::Scalar(0,   255, 0  ), -1, CV_AA, 0); // g - top right
        cv::circle(frame, points[1], 3, cv::Scalar(255, 255, 255), -1, CV_AA, 0); // w - bottom right
        cv::circle(frame, points[2], 3, cv::Scalar(255, 0,   0  ), -1, CV_AA, 0); // r - top left
        cv::circle(frame, points[3], 3, cv::Scalar(0,   0,   255), -1, CV_AA, 0); // b - bottom left

        //std::cout << "p0: " << points[0].x << ' ' << points[0].y << std::endl;
        //std::cout << "p1: " << points[1].x << ' ' << points[1].y << std::endl;
        //std::cout << "p2: " << points[2].x << ' ' << points[2].y << std::endl;
        //std::cout << "p3: " << points[3].x << ' ' << points[3].y << std::endl;

        const std::vector<cv::Point2f> reprojected_markers = headWidget.estimatePose(points, frame);

        if(reprojected_markers.size() >= 4)
        {
            const cv::Point2f mean_point(
                (points[0].x + points[1].x +
                 points[2].x + points[3].x) / 4.0,
                (points[0].y + points[1].y +
                 points[2].y + points[3].y) / 4.0
            );

            emit headData(
                mean_point.x, mean_point.y,
                headWidget.m_rv[0], headWidget.m_rv[1], headWidget.m_rv[2]
            );

            cv::circle(frame, reprojected_markers[0], 9, cv::Scalar(0,   255, 0  ), 1, CV_AA, 0); // g - top right
            cv::circle(frame, reprojected_markers[1], 9, cv::Scalar(255, 255, 255), 1, CV_AA, 0); // w - bottom right
            cv::circle(frame, reprojected_markers[2], 9, cv::Scalar(255, 0,   0  ), 1, CV_AA, 0); // r - top left
            cv::circle(frame, reprojected_markers[3], 9, cv::Scalar(0,   0,   255), 1, CV_AA, 0); // b - bottom left

            //std::cout << "m0: " << reprojected_markers[0].x << ' ' << reprojected_markers[0].y << std::endl;
            //std::cout << "m1: " << reprojected_markers[1].x << ' ' << reprojected_markers[1].y << std::endl;
            //std::cout << "m2: " << reprojected_markers[2].x << ' ' << reprojected_markers[2].y << std::endl;
            //std::cout << "m3: " << reprojected_markers[3].x << ' ' << reprojected_markers[3].y << std::endl;
        }
    }

    markerDetectorWidget.setPixmap(QPixmap::fromImage(convertMatToQImage(frame)));

    headWidget.update();
}
