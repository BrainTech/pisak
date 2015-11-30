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

#ifndef CALIBRATION_H
#define CALIBRATION_H

#include <QSettings>
#include <opencv2/opencv.hpp>

struct CalibrationPoint {
    cv::Point2d screenPoint;
    std::vector<cv::Point2d> eyePositions;
};

typedef std::vector<CalibrationPoint> CalibrationData;

struct EyeTrackerCalibration
{
public:
    EyeTrackerCalibration();

    cv::Point2d getGazePosition(const cv::Point2d & pupilPos);

    bool calibrate(const CalibrationData & calibrationData);

    void save(QSettings & settings) const;
    void load(QSettings & settings);

    void setToZero();

private:
    bool estimateParameters(const std::vector<cv::Point2d> & eyeData,
                            const std::vector<cv::Point2d> & calPointData);

    bool m_useHomography = true;
    enum DataPreprocessingType { NoPreprocessing, MeanPoint };
    const DataPreprocessingType m_dataPreprocessingType = MeanPoint;

    // method 1
    cv::Mat m_transform;
    void estimateParametersMethod1(
        const std::vector<cv::Point2d> & eyeData,
        const std::vector<cv::Point2d> & calPointData);

    // method 2
    double m_paramX[3] = { 0, 0, 0 };
    double m_paramY[3] = { 0, 0, 0 };
    void estimateParametersMethod2(
        const std::vector<cv::Point2d> & eyeData,
        const std::vector<cv::Point2d> & calPointData);
};

#endif // CALIBRATION_H
