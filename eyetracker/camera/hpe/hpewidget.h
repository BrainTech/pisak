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

#ifndef GLWIDGET_H
#define GLWIDGET_H

#include <QOpenGLWidget>
#include <QTimer>
#include <QLabel>

#include <opencv/cv.h>
#include "glm.h"

#include <memory>

#include "pstream.h"

class HpeHeadWidget : public QOpenGLWidget
{
    Q_OBJECT
public:
    explicit HpeHeadWidget(QWidget * parent = 0);

    std::vector<cv::Point2f> estimatePose(const std::vector<cv::Point2f> & markers,
                                          const cv::Mat & img);

    friend class HpeWidget;

protected:
    void initializeGL() override;
    void paintGL() override;
    void resizeGL(int w, int h) override;

private:

    // 3d model reference points
    cv::Mat m_modelPoints3d;

    // object orientation
    double m_rot[9] = { 0 }; // opengl rotation matrix
    std::vector<double> m_tv; // opengl translation vector
    std::vector<double> m_rv;
    cv::Mat m_rvec;
    cv::Mat m_tvec;

    GLMmodel * m_headObj = nullptr;
};

class HpeWidget : public QWidget
{
    Q_OBJECT
public:
    explicit HpeWidget(QWidget * parent = 0);

    HpeHeadWidget headWidget;
    QLabel markerDetectorWidget;

signals:
    void headData(double, double, double, double, double);

private:
    void idle();

private:
    QTimer m_timer;
    const redi::pstreams::pmode m_tracker_process_mode = redi::pstreams::pstdout | redi::pstreams::pstderr;
    std::unique_ptr<redi::ipstream> m_tracker_process;
};

#endif // GLWIDGET_H
