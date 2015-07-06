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

#include "smoother.h"

MovementSmoother::~MovementSmoother()
{
}

cv::Point2d NullSmoother::filter(const cv::Point2d & point)
{
    return point;
}

MovementSmootherWithBuffer::MovementSmootherWithBuffer()
    : m_bufSize(15)
    , m_bufX(m_bufSize, 0.0)
    , m_bufY(m_bufSize, 0.0)
{
}

cv::Point2d MovingAverageSmoother::filter(const cv::Point2d & point)
{
    m_bufX.push_back(point.x);
    m_bufY.push_back(point.y);

    return cv::Point2d(
        std::accumulate(m_bufX.begin(), m_bufX.end(), 0.0) / m_bufX.size(),
        std::accumulate(m_bufY.begin(), m_bufY.end(), 0.0) / m_bufY.size()
    );
}


DoubleMovingAverageSmoother::DoubleMovingAverageSmoother()
    : m_bufAveragesX(m_bufSize, 0.0)
    , m_bufAveragesY(m_bufSize, 0.0)
{
}

cv::Point2d DoubleMovingAverageSmoother::filter(const cv::Point2d & point)
{
    m_bufX.push_back(point.x);
    m_bufY.push_back(point.y);

    m_bufAveragesX.push_back(std::accumulate(m_bufX.begin(), m_bufX.end(), 0.0) / m_bufX.size());
    m_bufAveragesY.push_back(std::accumulate(m_bufY.begin(), m_bufY.end(), 0.0) / m_bufY.size());

    const double secondOrderAverageX =
        std::accumulate(m_bufAveragesX.begin(), m_bufAveragesX.end(), 0.0) / m_bufAveragesX.size();
    const double secondOrderAverageY =
        std::accumulate(m_bufAveragesY.begin(), m_bufAveragesY.end(), 0.0) / m_bufAveragesY.size();

    return cv::Point2d(2 * m_bufAveragesX.back() - secondOrderAverageX,
                       2 * m_bufAveragesY.back() - secondOrderAverageY);
}

cv::Point2d MedianSmoother::filter(const cv::Point2d & point)
{
    m_bufX.push_back(point.x);
    m_bufY.push_back(point.y);

    std::nth_element(m_bufX.begin(), m_bufX.begin() + m_bufX.size()/2, m_bufX.end());
    std::nth_element(m_bufY.begin(), m_bufY.begin() + m_bufY.size()/2, m_bufY.end());

    return cv::Point2d(m_bufX[m_bufX.size()/2], m_bufY[m_bufY.size()/2]);
}

DoubleExpSmoother::DoubleExpSmoother()
    : m_gamma(0.6)
    , m_alpha(0.5)
    , m_previousOutput(0, 0)
    , m_previousTrend(0, 0)
{
}

cv::Point2d DoubleExpSmoother::filter(const cv::Point2d & point)
{
    const cv::Point2d smoothedPoint(
        m_alpha*point.x + (1 - m_alpha)*(m_previousOutput.x + m_previousTrend.x),
        m_alpha*point.y + (1 - m_alpha)*(m_previousOutput.y + m_previousTrend.y)
    );

    m_previousTrend = cv::Point2d(
        m_gamma * (smoothedPoint.x - m_previousOutput.x) + (1.0 - m_gamma) * m_previousTrend.x,
        m_gamma * (smoothedPoint.y - m_previousOutput.y) + (1.0 - m_gamma) * m_previousTrend.y
    );

    m_previousOutput = smoothedPoint;

    return smoothedPoint;
}

CustomSmoother::CustomSmoother()
    : m_gamma(0.6)
    , m_alpha(0.4)
    , m_jitterThreshold(0.5)
    , m_previousOutput(0, 0)
    , m_previousTrend(0.0)
{
}

cv::Point2d CustomSmoother::filter(const cv::Point2d & point)
{
    m_bufX.push_back(point.x);
    m_bufY.push_back(point.y);

    std::nth_element(m_bufX.begin(), m_bufX.begin() + m_bufX.size()/2, m_bufX.end());
    std::nth_element(m_bufY.begin(), m_bufY.begin() + m_bufY.size()/2, m_bufY.end());

    const double medianX = m_bufX[m_bufX.size()/2];
    const double medianY = m_bufY[m_bufY.size()/2];

    const cv::Point2d smoothedPoint(
        (std::abs(point.x - medianX) > m_jitterThreshold) ? medianX :
        m_alpha*point.x + (1 - m_alpha)*(m_previousOutput.x + m_previousTrend.x),
        (std::abs(point.y - medianY) > m_jitterThreshold) ? medianY :
        m_alpha*point.y + (1 - m_alpha)*(m_previousOutput.y + m_previousTrend.y)
    );

    m_previousTrend = cv::Point2d(
        m_gamma * (smoothedPoint.x - m_previousOutput.x) + (1.0 - m_gamma) * m_previousTrend.x,
        m_gamma * (smoothedPoint.y - m_previousOutput.y) + (1.0 - m_gamma) * m_previousTrend.y);

    m_previousOutput = smoothedPoint;

    return smoothedPoint;
}

KalmanSmoother::KalmanSmoother()
    : m_filter(4, 2, 0)
    , m_input(2, 1)
{
    const double statePreX = 0.0;
    const double statePreY = 0.0;

    m_filter.transitionMatrix =
        *(cv::Mat_<float>(4, 4)
            << 1, 0, 1, 0,
               0, 1, 0, 1,
               0, 0, 1, 0,
               0, 0, 0, 1);

    m_input.setTo(cv::Scalar(0));
    m_filter.statePre.at<float>(0) = statePreX;
    m_filter.statePre.at<float>(1) = statePreY;
    m_filter.statePre.at<float>(2) = 0;
    m_filter.statePre.at<float>(3) = 0;
    cv::setIdentity(m_filter.measurementMatrix);

    // supposed and demanded level of eye movement natural noise,
    // movements in both dimensions are supposed to be independent
    cv::setIdentity(m_filter.processNoiseCov, cv::Scalar::all(5e-5));

    // supposed level of tracker measurement noise,
    // measurements of both dimensions are supposed to be independent
    cv::setIdentity(m_filter.measurementNoiseCov, cv::Scalar::all(1e-1));

    // post prediction state allowed error level,
    // dimensions should be independent
    cv::setIdentity(m_filter.errorCovPost, cv::Scalar::all(0.1));
}

cv::Point2d KalmanSmoother::filter(const cv::Point2d & point)
{
    const cv::Mat prediction = m_filter.predict();

    m_input(0) = point.x;
    m_input(1) = point.y;

    const cv::Mat estimation = m_filter.correct(m_input);

    return cv::Point2d(estimation.at<float>(0), estimation.at<float>(1));
}
