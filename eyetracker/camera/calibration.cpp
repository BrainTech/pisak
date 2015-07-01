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

#include "calibration.h"
#include <QDebug>

EyeTrackerCalibration::EyeTrackerCalibration()
{
    setToZero();
}

cv::Point2d EyeTrackerCalibration::getGazePosition(const cv::Point2d & pupilPos)
{
    if(m_useHomography)
    {
        cv::Mat pos = (cv::Mat_<double>(3,1) << pupilPos.x, pupilPos.y, 1);
        cv::Mat res = m_transform * pos;
        //std::cout << "r: " << res << std::endl;
        return cv::Point2d(res.at<double>(0), res.at<double>(1));
    }
    else
    {
        return cv::Point2d(m_paramX[0] * pupilPos.x + m_paramX[1] * pupilPos.y + m_paramX[2],
                           m_paramY[0] * pupilPos.x + m_paramY[1] * pupilPos.y + m_paramY[2]);
    }
}

bool EyeTrackerCalibration::calibrate(const CalibrationData & calibrationData)
{
    if(calibrationData.size() == 0)
        return false;

    size_t totalCalibrationPointsNum = 0;

    for(const auto & p: calibrationData)
        totalCalibrationPointsNum += p.eyePositions.size();

    if(totalCalibrationPointsNum < 10)
        return false;

    std::vector<cv::Point2d> eyePositions;
    std::vector<cv::Point2d> screenPositions;

    if(m_dataPreprocessingType == NoPreprocessing)
    {
        eyePositions.resize(totalCalibrationPointsNum);
        screenPositions.resize(totalCalibrationPointsNum);

        size_t i = 0;
        for(const auto & p: calibrationData)
        {
            const auto screenPos = p.screenPoint;
            for(const auto & eyePos: p.eyePositions)
            {
                eyePositions[i] = eyePos;
                screenPositions[i] = screenPos;
                ++i;
            }
        }
    }
    else if(m_dataPreprocessingType == MeanPoint)
    {
        eyePositions.resize(calibrationData.size());
        screenPositions.resize(calibrationData.size());

        size_t i = 0;
        for(const auto & p: calibrationData)
        {
            double mean_x = 0.0;
            double mean_y = 0.0;
            for(const auto & eyePos: p.eyePositions)
            {
                mean_x += eyePos.x;
                mean_y += eyePos.y;
            }
            mean_x /= p.eyePositions.size();
            mean_y /= p.eyePositions.size();

            eyePositions[i] = cv::Point2d(mean_x, mean_y);
            screenPositions[i] = p.screenPoint;
            i++;
        }
    }

    return estimateParameters(eyePositions, screenPositions);
}

bool EyeTrackerCalibration::estimateParameters(
    const std::vector<cv::Point2d> & eyeData,
    const std::vector<cv::Point2d> & calPointData)
{
    Q_ASSERT(eyeData.size() == calPointData.size());

    const size_t dataCounter = eyeData.size();

    qDebug() << "Screen points:";
    for(size_t i = 0; i < dataCounter; i++)
        qDebug() << calPointData[i].x << " " << calPointData[i].y;

    qDebug() << "Pupil positions:";
    for(size_t i = 0; i < dataCounter; i++)
        qDebug() << eyeData[i].x << " " <<  eyeData[i].y;

    if(dataCounter <= 0)
    {
        setToZero();
        return false;
    }

    // Calculate calibration using two methods.
    // Active gaze estimation method can be selected later.
    estimateParametersMethod1(eyeData, calPointData);
    estimateParametersMethod2(eyeData, calPointData);

    return true;
}

void EyeTrackerCalibration::estimateParametersMethod1(
    const std::vector<cv::Point2d> & eyeData,
    const std::vector<cv::Point2d> & calPointData)
{
    const size_t dataCounter = eyeData.size();
    cv::Mat IJ(dataCounter, 3, CV_64FC1); // positions of eye in video frame
    cv::Mat X(dataCounter, 1, CV_64FC1); // positions of point on screen
    cv::Mat Y(dataCounter, 1, CV_64FC1);

    for(int i = 0; i < IJ.rows; i++)
    {
        double * Mi = IJ.ptr<double>(i);
        Mi[0] = eyeData[i].x;
        Mi[1] = eyeData[i].y;
        Mi[2] = 1.0;
    }

    cv::MatIterator_<double> it;

    int i;
    for(i = 0, it = X.begin<double>(); it != X.end<double>(); it++)
    {
        *it = calPointData[i].x;
        i++;
    }

    for(i = 0, it = Y.begin<double>(); it != Y.end<double>(); it++)
    {
        *it = calPointData[i].y;
        i++;
    }

    const cv::Mat PX = (IJ.t() * IJ).inv() * IJ.t() * X;
    const cv::Mat PY = (IJ.t() * IJ).inv() * IJ.t() * Y;

    //g_GX = IJ*PX;  //If calibration results are necessary ...
    //g_GY = IJ*PY;

    for(int i = 0; i < 3; i++)
    {
        const double * MiX = PX.ptr<double>(i);
        const double * MiY = PY.ptr<double>(i);
        m_paramX[i] = *MiX;
        m_paramY[i] = *MiY;
    }

    qDebug() << "Calibration coeffs:";
    qDebug() << m_paramX[0] << " " <<  m_paramX[1] << " " << m_paramX[2];
    qDebug() << m_paramY[0] << " " <<  m_paramY[2] << " " << m_paramY[2];
}

void EyeTrackerCalibration::estimateParametersMethod2(
    const std::vector<cv::Point2d> & eyeData,
    const std::vector<cv::Point2d> & calPointData)
{
    cv::Mat src(eyeData);
    cv::Mat dst(calPointData);
    m_transform = cv::findHomography(src, dst, cv::RANSAC);
}

void EyeTrackerCalibration::save(QSettings & settings) const
{
    settings.setValue("param_x_0", m_paramX[0]);
    settings.setValue("param_x_1", m_paramX[1]);
    settings.setValue("param_x_2", m_paramX[2]);
    settings.setValue("param_y_0", m_paramY[0]);
    settings.setValue("param_y_1", m_paramY[1]);
    settings.setValue("param_y_2", m_paramY[2]);

    settings.setValue("transform_0_0", m_transform.at<double>(0, 0));
    settings.setValue("transform_0_1", m_transform.at<double>(0, 1));
    settings.setValue("transform_0_2", m_transform.at<double>(0, 2));
    settings.setValue("transform_1_0", m_transform.at<double>(1, 0));
    settings.setValue("transform_1_1", m_transform.at<double>(1, 1));
    settings.setValue("transform_1_2", m_transform.at<double>(1, 2));
    settings.setValue("transform_2_0", m_transform.at<double>(2, 0));
    settings.setValue("transform_2_1", m_transform.at<double>(2, 1));
    settings.setValue("transform_2_2", m_transform.at<double>(2, 2));
}

void EyeTrackerCalibration::load(QSettings & settings)
{
    m_paramX[0] = settings.value("param_x_0", 0.0).toDouble();
    m_paramX[1] = settings.value("param_x_1", 0.0).toDouble();
    m_paramX[2] = settings.value("param_x_2", 0.0).toDouble();
    m_paramY[0] = settings.value("param_y_0", 0.0).toDouble();
    m_paramY[1] = settings.value("param_y_1", 0.0).toDouble();
    m_paramY[2] = settings.value("param_y_2", 0.0).toDouble();

    m_transform.at<double>(0, 0) = settings.value("transform_0_0", 0.0).toDouble();
    m_transform.at<double>(0, 1) = settings.value("transform_0_1", 0.0).toDouble();
    m_transform.at<double>(0, 2) = settings.value("transform_0_2", 0.0).toDouble();
    m_transform.at<double>(1, 0) = settings.value("transform_1_0", 0.0).toDouble();
    m_transform.at<double>(1, 1) = settings.value("transform_1_1", 0.0).toDouble();
    m_transform.at<double>(1, 2) = settings.value("transform_1_2", 0.0).toDouble();
    m_transform.at<double>(2, 0) = settings.value("transform_2_0", 0.0).toDouble();
    m_transform.at<double>(2, 1) = settings.value("transform_2_1", 0.0).toDouble();
    m_transform.at<double>(2, 2) = settings.value("transform_2_2", 0.0).toDouble();
}

void EyeTrackerCalibration::setToZero()
{
    m_paramX[0] = 0.0;
    m_paramX[1] = 0.0;
    m_paramX[2] = 0.0;
    m_paramY[0] = 0.0;
    m_paramY[1] = 0.0;
    m_paramY[2] = 0.0;

    m_transform = cv::Mat::zeros(3, 3, CV_64F);
}
