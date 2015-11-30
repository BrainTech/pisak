/*
 * This file is part of PISAK project.
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
 */

#ifndef CAMERAEYETRACKER_H
#define CAMERAEYETRACKER_H

#include <QObject>
#include <QDebug>
#include <QMessageBox>
#include <QTimer>
#include <QThread>
#include <QApplication>

#include "../common/eyetracker.h"
#include "pupildetector.h"
#include "calibration.h"
#include "hpe/hpewidget.h"

class CameraEyetracker : public Eyetracker
{
    Q_OBJECT

public:
    explicit CameraEyetracker(QObject * parent = 0);
    ~CameraEyetracker();

    Q_INVOKABLE QString getBackend() const override;

    Q_INVOKABLE bool loadConfig() override;
    Q_INVOKABLE bool saveConfig() const override;

    Q_INVOKABLE void runCameraSetup() override;

    Q_INVOKABLE bool startTracking() override;
    Q_INVOKABLE bool stopTracking() override;

public slots:
    void initialize() override;
    void shutdown() override;

    void calibrationStart() override;
    void calibrationStop() override;
    void calibrationAddPoint(QPointF point) override;
    void calibrationComputeAndSet() override;

protected:
    const char * getBackendCodename() const override;

private:
    bool addDataPoint(std::vector<cv::Point2d> & v, const cv::Point2d & pt);

    int m_cameraIndex;
    Capture m_capture;
    FramePupilDetector m_pupilDetector;

    QPointer<QThread> m_captureThread;
    QPointer<QThread> m_detectorThread;

    QPointer<PupilDetectorSetupWindow> m_cameraSetupWindow;

    bool m_tracking;
    bool m_calibrating;
    bool m_calibrating_point;

    CalibrationData m_calibrationData;
    EyeTrackerCalibration m_calibration;
    QTimer m_pointCalibrationTimer;

    // calibration parameters
    size_t m_measurementsPerPoint;
    double m_distStdDevCoeff;
    int m_pointCalibrationTimeout;

    std::unique_ptr<MovementSmoother> m_pupilSmoother;
    cv::Point2d m_gazePosLast;

    // head position correction window and parameters
    QPointer<HpeWidget> m_hpeWindow;

    cv::Point2d m_headPos;
    cv::Point3d m_headRot;

    double m_headTranslationScaleX;
    double m_headTranslationScaleY;
    double m_headTranslationOffsetX;
    double m_headTranslationOffsetY;

    double m_headRotationScaleX;
    double m_headRotationScaleY;
    double m_headRotationOffsetX;
    double m_headRotationOffsetY;

    bool m_translationCorrectionEnabled;
    std::unique_ptr<MovementSmoother> m_headTranslationSmoother;
    cv::Point2d m_translationCorrection;

    bool m_rotationCorrectionEnabled;
    std::unique_ptr<MovementSmoother> m_headRotationSmoother;
    cv::Point2d m_rotationCorrection;

private slots:
    void pupilData(bool, double, double, double);
    void headData(double, double, double, double, double);
    void setCameraIndex(int cameraIndex);
    void cameraSetupDialogFinished(int result);
    void pointCalibrationTimeout();
};

#endif // CALIBRATION_H
