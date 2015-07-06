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

#ifndef EYETRACKER_H
#define EYETRACKER_H

#include <QObject>
#include <QPointF>

#include "smoother.h"

class Eyetracker : public QObject
{
    Q_OBJECT

public:
    explicit Eyetracker(QObject * parent = 0);
    ~Eyetracker();

    Q_INVOKABLE virtual bool loadConfig() = 0;
    Q_INVOKABLE virtual bool saveConfig() const = 0;

    Q_INVOKABLE virtual QString getBackend() const = 0;

    Q_INVOKABLE virtual void runCameraSetup() = 0;

    Q_INVOKABLE virtual bool startTracking() = 0;
    Q_INVOKABLE virtual bool stopTracking() = 0;

public slots:
    virtual void initialize() = 0;
    virtual void shutdown() = 0;

    virtual void calibrationStart() = 0;
    virtual void calibrationStop() = 0;
    virtual void calibrationAddPoint(QPointF point) = 0;
    virtual void calibrationComputeAndSet() = 0;

signals:
    void initialized(bool success, QString errorMessage);
    void shutdownCompleted(bool success, QString errorMessage);
    void cameraSetupFinished(bool success, QString errorMessage);

    void gazeData(bool eyeDetected, QPointF point);

    void calibrationStarted(bool success, QString errorMessage);
    void calibrationStopped(bool success, QString errorMessage);
    void pointCalibrated(bool success, QString errorMessage);
    void computeAndSetCalibrationFinished(bool success, QString errorMessage);

    void gazeDetectionFailed(QString errorMessage);

protected:
    virtual const char * getBackendCodename() const = 0; // only lowercase ASCII, no spaces
    QString getBaseConfigPath() const;

    virtual void emitNewPoint(cv::Point2d point);

    // factory function for smoothers
    static std::unique_ptr<MovementSmoother> createSmoother(SmoothingMethod smoothingMethod);

protected:
    std::unique_ptr<MovementSmoother> m_smoother;
    cv::Point2d m_previousPoint;
};

#endif // EYETRACKER_H
