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

#ifndef SMOOTHER_H
#define SMOOTHER_H

#include <boost/circular_buffer.hpp>
#include <opencv2/opencv.hpp>

// Skeletal Joint Smoothing White Paper
// https://msdn.microsoft.com/en-us/library/jj131429.aspx

enum class SmoothingMethod {
    None,
    MovingAverage,
    DoubleMovingAverage,
    Median,
    Kalman,
    DoubleExp,
    Custom
};


class MovementSmoother
{
public:
    virtual ~MovementSmoother();

    virtual cv::Point2d filter(const cv::Point2d & point) = 0;
};


class NullSmoother final : public MovementSmoother
{
public:
    cv::Point2d filter(const cv::Point2d & point) override;
};


class MovementSmootherWithBuffer : public MovementSmoother
{
public:
    MovementSmootherWithBuffer();

protected:
   int m_bufSize;

   boost::circular_buffer<double> m_bufX;
   boost::circular_buffer<double> m_bufY;
};


class MovingAverageSmoother final : public MovementSmootherWithBuffer
{
public:
    cv::Point2d filter(const cv::Point2d & point) override;
};


class DoubleMovingAverageSmoother final : public MovementSmootherWithBuffer
{
public:
    DoubleMovingAverageSmoother();

    cv::Point2d filter(const cv::Point2d & point) override;

private:
    boost::circular_buffer<double> m_bufAveragesX;
    boost::circular_buffer<double> m_bufAveragesY;
};


class MedianSmoother final : public MovementSmootherWithBuffer
{
public:
    cv::Point2d filter(const cv::Point2d & point) override;
};


class DoubleExpSmoother final : public MovementSmoother
{
public:
    DoubleExpSmoother();

    cv::Point2d filter(const cv::Point2d & point) override;

private:
    double m_gamma;
    double m_alpha;

    cv::Point2d m_previousOutput;
    cv::Point2d m_previousTrend;
};


class CustomSmoother final : public MovementSmootherWithBuffer
{
public:
    CustomSmoother();

    cv::Point2d filter(const cv::Point2d & point) override;

private:
    double m_gamma;
    double m_alpha;

    double m_jitterThreshold;

    cv::Point2d m_previousOutput;
    cv::Point2d m_previousTrend;
};


class KalmanSmoother final : public MovementSmoother
{
public:
    KalmanSmoother();

    cv::Point2d filter(const cv::Point2d & point) override;

private:
    cv::KalmanFilter m_filter;
    cv::Mat_<float> m_input;
};

#endif
