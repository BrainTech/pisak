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

#include "mockupeyetracker.h"
#include <QCursor>
#include <QDesktopWidget>

MockupEyetracker::MockupEyetracker(QObject * parent)
    : Eyetracker(parent)
    , m_initialized(false)
{
    m_pollTimer.setSingleShot(false);
    QObject::connect(&m_pollTimer, SIGNAL(timeout()),
                     this, SLOT(generateNewPointFromCursorPos()));
}

MockupEyetracker::~MockupEyetracker()
{
}

const char * MockupEyetracker::getBackendCodename() const
{
    return "mockup";
}

QString MockupEyetracker::getBackend() const
{
    return QStringLiteral("Mockup Eyetracker 1.0");
}

void MockupEyetracker::generateNewPointFromCursorPos()
{
    const QDesktopWidget widget;
    const QRect mainScreenSize = widget.screenGeometry(widget.primaryScreen());
    const QPoint mousePos = QCursor::pos();
    const QPointF pos(qreal(mousePos.x()) / qreal(mainScreenSize.width()),
                      qreal(mousePos.y()) / qreal(mainScreenSize.height()));
    emitNewPoint(cv::Point2d(pos.x(), pos.y()));
}

void MockupEyetracker::runCameraSetup()
{
    emit cameraSetupFinished(true, QString());
}

void MockupEyetracker::initialize()
{
    m_pollTimer.setInterval(1000/30); // 30 FPS
    m_pollTimer.stop(); // stop tracking if currently running
    m_initialized = true;
    emit initialized(true, QString());
}

void MockupEyetracker::shutdown()
{
    stopTracking();
    m_initialized = false;
    emit shutdownCompleted(true, QString());
}

bool MockupEyetracker::loadConfig()
{
    return true;
}

bool MockupEyetracker::saveConfig() const
{
    return true;
}

void MockupEyetracker::calibrationStart()
{
    if(m_initialized)
        emit calibrationStarted(true, QString());
    else
        emit calibrationStarted(false, QStringLiteral("not initialized"));
}

void MockupEyetracker::calibrationStop()
{
    if(m_initialized)
        emit calibrationStopped(true, QString());
    else
        emit calibrationStopped(false, QStringLiteral("not initialized"));
}

void MockupEyetracker::calibrationAddPoint(QPointF point)
{
    Q_UNUSED(point);

    if(m_initialized)
        emit pointCalibrated(true, QString());
    else
        emit pointCalibrated(false, QStringLiteral("not initialized"));
}

void MockupEyetracker::calibrationComputeAndSet()
{
    if(m_initialized)
        emit computeAndSetCalibrationFinished(true, QString());
    else
        emit computeAndSetCalibrationFinished(false, QStringLiteral("not initialized"));
}

bool MockupEyetracker::startTracking()
{
    if(m_initialized)
    {
        m_pollTimer.start();
        return true;
    }
    else
    {
        return false;
    }
}

bool MockupEyetracker::stopTracking()
{
    if(m_initialized)
    {
        m_pollTimer.stop();
        return true;
    }
    else
    {
        return false;
    }
}
