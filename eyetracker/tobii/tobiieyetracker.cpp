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

#include "tobiieyetracker.h"

#include <QFile>

static QString err2msg(int error_code)
{
    switch(error_code)
    {
        case 0:
            return QString();
        case -1:
            return QObject::tr("eyetracker worker thread: m_eyetracker is NULL");
        default:
            return tobiigaze_get_error_message(static_cast<tobiigaze_error_code>(error_code));
    }
}

TobiiEyetracker::TobiiEyetracker(QObject * parent)
    : Eyetracker(parent)
{
}

TobiiEyetracker::~TobiiEyetracker()
{
    if(m_worker && m_eye_tracker)
    {
        tobiigaze_disconnect(m_eye_tracker);
        tobiigaze_break_event_loop(m_eye_tracker);
        // TODO: wait for event loop finished?
    }

    cleanup();
}

QString TobiiEyetracker::getConnectedEyeTracker() const
{
    const size_t bufSize = 256;
    char buf[bufSize];
    tobiigaze_error_code error_code;
    tobiigaze_get_connected_eye_tracker(buf, bufSize, &error_code);
    if(error_code)
        return QString();
    else
        return QString::fromUtf8(buf);
}

const char * TobiiEyetracker::getBackendCodename() const
{
    return "tobii";
}

QString TobiiEyetracker::getBackend() const
{
    return "Tobii " + QString::fromUtf8(tobiigaze_get_version());
}

void TobiiEyetracker::runCameraSetup()
{
    // tobii doesn't skips camera setup
    emit cameraSetupFinished(true, QString());
}

void TobiiEyetracker::initialize()
{
    if(m_eye_tracker || m_worker)
    {
        emit initialized(false, tr("already initialized"));
        return;
    }

    if(m_tobiiUrl.isEmpty())
        m_tobiiUrl = getConnectedEyeTracker();

    qDebug() << "Tobii URL:" << m_tobiiUrl;

    if(m_tobiiUrl.isEmpty())
    {
        emit initialized(false, tr("no eyetracker detected"));
        return;
    }

    tobiigaze_error_code error_code;

    m_eye_tracker = tobiigaze_create(m_tobiiUrl.toUtf8().data(), &error_code);
    if(error_code)
    {
        if(m_eye_tracker)
            tobiigaze_destroy(m_eye_tracker);
        m_eye_tracker = nullptr;
        emit initialized(false, err2msg(error_code));
        return;
    }

    QThread * thread = new QThread;
    EyetrackerEventLoopWorker * worker = new EyetrackerEventLoopWorker(m_eye_tracker);
    worker->moveToThread(thread);

    connect(worker, SIGNAL(calibrationStarted(int)), this, SLOT(privCalibrationStarted(int)));
    connect(worker, SIGNAL(calibrationStopped(int)), this, SLOT(privCalibrationStopped(int)));
    connect(worker, SIGNAL(pointCalibrated(int)), this, SLOT(privPointCalibrated(int)));
    connect(worker, SIGNAL(computeAndSetCalibrationFinished(int)), this, SLOT(privComputeAndSetCalibrationFinished(int)));
    connect(worker, SIGNAL(gazeData(QPointF,QPointF)), this, SLOT(privGazeData(QPointF,QPointF)));

    connect(worker, SIGNAL(finished(int)), this, SLOT(privEventLoopFinished(int)));
    connect(worker, SIGNAL(finished(int)), thread, SLOT(quit()));
    connect(worker, SIGNAL(finished(int)), worker, SLOT(deleteLater()));

    connect(thread, SIGNAL(finished()), thread, SLOT(deleteLater()));
    connect(thread, SIGNAL(started()), worker, SLOT(run()));

    m_worker = worker;

    thread->start();

    tobiigaze_connect(m_eye_tracker, &error_code);
    if(error_code)
    {
        // TODO: shutdown thread
        //thread->disconnect();
        //tobiigaze_break_event_loop(m_eye_tracker);
        emit initialized(false, err2msg(error_code));
        return;
    }

    tobiigaze_device_info info;
    tobiigaze_get_device_info(m_eye_tracker, &info, &error_code);
    if(error_code)
    {
        //m_error_code = error_code;
        //m_error_message = tobiigaze_get_error_message(error_code);
        // TODO: shutdown thread
        emit initialized(false, err2msg(error_code));
        return;
    }

    qDebug() << "Serial number:" << info.serial_number;
    qDebug() << "Model:" << info.model;
    qDebug() << "Generation:" << info.generation;
    qDebug() << "Firmware version:" << info.firmware_version;

    emit initialized(true, QString());
}

void TobiiEyetracker::shutdown()
{
    if(m_worker && m_eye_tracker)
    {
        tobiigaze_disconnect(m_eye_tracker);
        tobiigaze_break_event_loop(m_eye_tracker);
        // privEventLoopFinished slot will be called next
    }
    else
    {
        privEventLoopFinished(0);
    }
}

bool TobiiEyetracker::loadConfig()
{
    if(!m_eye_tracker)
        return false;

    const QString fileName(getBaseConfigPath() + ".bin");

    QFile file(fileName);
    if(!file.open(QIODevice::ReadOnly))
    {
        qDebug() << "unable to open calibration:" << fileName;
        return false;
    }

    if(file.size() == sizeof(tobiigaze_calibration))
    {
        QByteArray calibBytes = file.readAll();
        tobiigaze_error_code error_code;

        tobiigaze_set_calibration(
            m_eye_tracker,
            reinterpret_cast<tobiigaze_calibration*>(calibBytes.data()),
            &error_code
        );

        if(error_code)
        {
            qDebug() << "error in tobiigaze_set_calibration";
            return false;
        }
        else
        {
            return true;
        }
    }
    else
    {
        qDebug() << "bad file size";
        return false;
    }
}

bool TobiiEyetracker::saveConfig() const
{
    if(!m_eye_tracker)
        return false;

    tobiigaze_calibration calib;
    tobiigaze_error_code error_code;

    tobiigaze_get_calibration(m_eye_tracker, &calib, &error_code);

    if(error_code)
    {
        qDebug() << "error in tobiigaze_get_calibration:" << err2msg(error_code);
        return false;
    }
    else
    {
        const QString fileName(getBaseConfigPath() + ".bin");
        QFile file(fileName);

        if(!file.open(QIODevice::WriteOnly | QIODevice::Truncate))
        {
            qDebug() << "unable to open calibration:" << fileName;
            return false;
        }

        if(file.write(reinterpret_cast<char *>(&calib), sizeof(tobiigaze_calibration)) == -1)
            return false;
        else
            return true;
    }
}

void TobiiEyetracker::calibrationStart()
{
    if(m_eye_tracker && m_worker)
        tobiigaze_calibration_start_async(
            m_eye_tracker,
            EyetrackerEventLoopWorker::calibration_start_helper,
            m_worker
        );
    else
        emit calibrationStarted(false, tr("eyetracker not initialized"));
}

void TobiiEyetracker::calibrationStop()
{
    if(m_eye_tracker && m_worker)
        tobiigaze_calibration_stop_async(
            m_eye_tracker,
            EyetrackerEventLoopWorker::calibration_stop_helper,
            m_worker
        );
    else
        emit calibrationStopped(false, tr("eyetracker not initialized"));
}

void TobiiEyetracker::calibrationAddPoint(QPointF point)
{
    if(m_eye_tracker && m_worker)
    {
        const tobiigaze_point_2d tobiigaze_point { point.x(), point.y() };
        tobiigaze_calibration_add_point_async(
            m_eye_tracker,
            &tobiigaze_point,
            EyetrackerEventLoopWorker::calibration_add_point_helper,
            m_worker
        );
    }
    else
        emit pointCalibrated(false, tr("eyetracker not initialized"));
}

void TobiiEyetracker::calibrationComputeAndSet()
{
    if(m_eye_tracker && m_worker)
        tobiigaze_calibration_compute_and_set_async(
            m_eye_tracker,
            EyetrackerEventLoopWorker::calibration_compute_and_set_helper,
            m_worker
        );
    else
        emit computeAndSetCalibrationFinished(false, tr("eyetracker not initialized"));
}

bool TobiiEyetracker::startTracking()
{
    if(m_eye_tracker && m_worker)
    {
        tobiigaze_error_code error_code;
        tobiigaze_start_tracking(
            m_eye_tracker,
            EyetrackerEventLoopWorker::gaze_data_helper,
            &error_code,
            m_worker
        );
        return error_code == 0;
    }
    return false;
}

bool TobiiEyetracker::stopTracking()
{
    if(m_eye_tracker)
    {
        tobiigaze_error_code error_code;
        tobiigaze_stop_tracking(m_eye_tracker, &error_code);
        return error_code == 0;
    }
    return false;
}

cv::Point2d TobiiEyetracker::calculateSinglePoint(QPointF right, QPointF left)
{
    cv::Point2d pt(std::numeric_limits<double>::quiet_NaN(),
                   std::numeric_limits<double>::quiet_NaN());

    if(!std::isnan(right.x()) &&
       !std::isnan(right.y()) &&
       !std::isnan(left.x()) &&
       !std::isnan(left.y()))
    {
        pt.x = 0.5 * (right.x() + left.x());
        pt.y = 0.5 * (right.y() + left.y());
    }
    else if(!std::isnan(right.x()) && !std::isnan(right.y()))
    {
        pt.x = right.x();
        pt.y = right.y();
    }
    else if(!std::isnan(left.x()) && !std::isnan(left.y()))
    {
        pt.x = left.x();
        pt.y = left.y();
    }
    return pt;
}

// private implementation details

void TobiiEyetracker::cleanup()
{
    m_worker = nullptr;

    if(m_eye_tracker)
    {
        tobiigaze_destroy(m_eye_tracker);
        m_eye_tracker = nullptr;
    }
}

void TobiiEyetracker::privEventLoopFinished(int error_code)
{
    cleanup();
    emit shutdownCompleted(error_code == 0, err2msg(error_code));
}

void TobiiEyetracker::privCalibrationStarted(int error_code)
{
    emit calibrationStarted(error_code == 0, err2msg(error_code));
}

void TobiiEyetracker::privCalibrationStopped(int error_code)
{
    emit calibrationStopped(error_code == 0, err2msg(error_code));
}

void TobiiEyetracker::privPointCalibrated(int error_code)
{
    emit pointCalibrated(error_code == 0, err2msg(error_code));
}

void TobiiEyetracker::privComputeAndSetCalibrationFinished(int error_code)
{
    emit computeAndSetCalibrationFinished(error_code == 0, err2msg(error_code));
}

void TobiiEyetracker::privGazeData(QPointF right, QPointF left)
{
    emitNewPoint(calculateSinglePoint(right, left));
}
