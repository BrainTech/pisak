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

#include "eyetracker.h"

#include <QDebug>
#include <QDir>

Eyetracker::Eyetracker(QObject * parent)
    : QObject(parent)
{
    m_smoother = createSmoother(SmoothingMethod::Kalman);
}

Eyetracker::~Eyetracker()
{
}

QString Eyetracker::getBaseConfigPath() const
{
    const QDir dir(QDir::homePath() + "/.pisak/eyetracker");
    if(!dir.exists())
        dir.mkpath(".");
    return dir.filePath(getBackendCodename());
}

void Eyetracker::emitNewPoint(cv::Point2d point)
{
    bool eyeDetected = true;

    if(std::isnan(point.x) || std::isnan(point.y))
    {
        eyeDetected = false;
        point.x = m_previousPoint.x;
        point.y = m_previousPoint.y;
    }

    const cv::Point2d smoothed(m_smoother->filter(point));
    m_previousPoint = smoothed;

    const QPointF ret(smoothed.x, smoothed.y);
    // qDebug() << "pos:" << ret;

    emit gazeData(eyeDetected, ret);
}

std::unique_ptr<MovementSmoother> Eyetracker::createSmoother(SmoothingMethod smoothingMethod)
{
    switch(smoothingMethod)
    {
        case SmoothingMethod::None:
            return std::unique_ptr<MovementSmoother>(new NullSmoother);
        case SmoothingMethod::MovingAverage:
            return std::unique_ptr<MovementSmoother>(new MovingAverageSmoother);
        case SmoothingMethod::DoubleMovingAverage:
            return std::unique_ptr<MovementSmoother>(new DoubleMovingAverageSmoother);
        case SmoothingMethod::Median:
            return std::unique_ptr<MovementSmoother>(new MedianSmoother);
        case SmoothingMethod::DoubleExp:
            return std::unique_ptr<MovementSmoother>(new DoubleExpSmoother);
        case SmoothingMethod::Custom:
            return std::unique_ptr<MovementSmoother>(new CustomSmoother);
        case SmoothingMethod::Kalman:
            return std::unique_ptr<MovementSmoother>(new KalmanSmoother);
        default:
            return std::unique_ptr<MovementSmoother>(new NullSmoother);
    }
}
