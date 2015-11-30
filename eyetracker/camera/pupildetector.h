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

#ifndef PUPILDETECTOR_H
#define PUPILDETECTOR_H

#include "opencvcapture.h"
#include "ui_camera_setup.h"
#include <QtWidgets>
#include <QString>

#include <boost/algorithm/clamp.hpp>

class FramePupilDetector : public FrameReceiver
{
    Q_OBJECT

public:
    enum PupilDetectionResult { Ok, NoPupilCandidate, TooManyPupilCandidates };
    enum PreviewType { PreviewColor, PreviewGrayscale, PreviewThreshold };

    explicit FramePupilDetector(QObject * parent = 0);

    void loadSettings(QSettings & settings);
    void saveSettings(QSettings & settings) const;

    inline PreviewType previewType() const { return m_previewType; }
    inline void setPreviewType(PreviewType value) { m_previewType = value; }

    inline bool mirrored() const { return m_mirrored; }
    inline void setMirrored(bool value) { m_mirrored = value; }

    inline bool equalizeHistogram() const { return m_equalizeHistogram; }
    inline void setEqualizeHistogram(bool value) { m_equalizeHistogram = value; }

    inline double contrast() const { return m_contrast; }
    inline void setContrast(double value) { m_contrast = value; }

    inline double brightness() const { return m_brightness; }
    inline void setBrightness(double value) { m_brightness = value; }

    inline double gamma() const { return m_gamma; }
    inline void setGamma(double value) { m_gamma = value; }

    inline int threshold() const { return m_threshold; }
    inline void setThreshold(int value) { m_threshold = value; }

    inline double topMargin() const { return m_topMargin; }
    inline void setTopMargin(double value)
    {
        m_topMargin = boost::algorithm::clamp(value, 0.0, 1.0 - m_bottomMargin);
    }

    inline double bottomMargin() const { return m_bottomMargin; }
    inline void setBottomMargin(double value)
    {
        m_bottomMargin = boost::algorithm::clamp(value, 0.0, 1.0 - m_topMargin);
    }

    inline double rightMargin() const { return m_rightMargin; }
    inline void setRightMargin(double value)
    {
        m_rightMargin = boost::algorithm::clamp(value, 0.0, 1.0 - m_leftMargin);
    }

    inline double leftMargin() const { return m_leftMargin; }
    inline void setLeftMargin(double value)
    {
        m_leftMargin = boost::algorithm::clamp(value, 0.0, 1.0 - m_rightMargin);
    }

    inline int pointsMin() const { return m_pointsMin; }
    inline void setPointsMin(int value) { m_pointsMin = value; }

    inline int pointsMax() const { return m_pointsMax; }
    inline void setPointsMax(int value) { m_pointsMax = value; }

    inline double oblatenessLow() const { return m_oblatenessLow; }
    inline void setOblatenessLow(double value) { m_oblatenessLow = value; }

    inline double oblatenessHigh() const { return m_oblatenessHigh; }
    inline void setOblatenessHigh(double value) { m_oblatenessHigh = value; }

signals:
    void pupilData(bool, double, double, double);

private:
    void processFrame(cv::Mat & frame) override;

private:
    PreviewType m_previewType;

    // image preprocessing parameters
    bool m_mirrored = true;
    bool m_equalizeHistogram = false;
    double m_contrast = 1.0;
    double m_brightness = 0.0;
    double m_gamma = 1.0;
    int m_threshold = 27;

    // search area margins - floats from 0.0 to 1.0
    double m_topMargin    = 0.0;
    double m_bottomMargin = 0.0;
    double m_leftMargin   = 0.0;
    double m_rightMargin  = 0.0;

    // minimal and maximal number of points in contour
    unsigned int m_pointsMin = 25;
    unsigned int m_pointsMax = 690;

    // extra parameters
    double m_oblatenessLow = 0.67;
    double m_oblatenessHigh = 1.50;

    // output data
    double m_pupilX = -1.0;
    double m_pupilY = -1.0;
    double m_pupilSize = -1.0;

    // pupil detection algorithm
    PupilDetectionResult detect(const cv::Mat & frame, cv::Mat & drawFrame);
    static constexpr size_t MAX_FIRST_CANDIDATES = 6;
};

class PupilDetectorSetupWindow : public QDialog
{
    Q_OBJECT

public:
    explicit PupilDetectorSetupWindow(QWidget * parent = 0);
    ~PupilDetectorSetupWindow();

    void setVideoSource(FramePupilDetector * pupilDetector, int cameraIndex);

signals:
    void cameraIndexChanged(int);

protected:
    void showEvent(QShowEvent * event) override;
    void closeEvent(QCloseEvent * event) override;

private:
    Ui::CameraSetupForm m_gui;
    QPointer<FramePupilDetector> m_pupilDetector;
    const double m_marginCoeff = 100.0;
    const double m_contrastCoeff = 100.0;
    const double m_brightnessCoeff = 1.0;
    const double m_gammaCoeff = 100.0;
    const double m_oblatenessCoeff = 50.0;
};

#endif // PUPILDETECTOR_H
