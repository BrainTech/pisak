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

#include "pupildetector.h"

static cv::Mat correctGamma(cv::Mat & img, double gamma)
{
    const double inverse_gamma = 1.0 / gamma;

    cv::Mat lut_matrix(1, 256, CV_8UC1);
    unsigned char * ptr = lut_matrix.ptr();
    for(int i = 0; i < 256; i++)
        ptr[i] = int(std::pow(double(i) / 255.0, inverse_gamma) * 255.0);

    cv::Mat result;
    cv::LUT(img, lut_matrix, result);

    return result;
}

/*
static cv::Mat equalizeIntensity(const cv::Mat & inputImage)
{
    if(inputImage.channels() >= 3)
    {
        cv::Mat ycrcb;

        cv::cvtColor(inputImage, ycrcb, CV_BGR2YCrCb);

        std::vector<cv::Mat> channels;
        cv::split(ycrcb, channels);

        cv::equalizeHist(channels[0], channels[0]);

        cv::Mat result;
        cv::merge(channels, ycrcb);

        cv::cvtColor(ycrcb, result, CV_YCrCb2BGR);

        return result;
    }
    return cv::Mat();
}
*/

static inline void drawPupil(cv::Mat & img,
                             const cv::RotatedRect & box,
                             const cv::Scalar & color,
                             int thickness)
{
    const int crossSize = 20;

    cv::ellipse(img, box, color, thickness);

    cv::line(img,
             cv::Point2f(box.center.x, box.center.y - crossSize),
             cv::Point2f(box.center.x, box.center.y + crossSize),
             color
    );

    cv::line(img,
             cv::Point2f(box.center.x - crossSize, box.center.y),
             cv::Point2f(box.center.x + crossSize, box.center.y),
             color
    );
}

FramePupilDetector::FramePupilDetector(QObject * parent)
    : FrameReceiver(parent)
{
}

void FramePupilDetector::loadSettings(QSettings & settings)
{
    setMirrored(settings.value("mirrored", false).toBool());
    setEqualizeHistogram(settings.value("equalize_hist", false).toBool());
    setContrast(settings.value("contrast", 1.0).toFloat());
    setBrightness(settings.value("brightness", 0.0).toFloat());
    setGamma(settings.value("gamma", 1.0).toFloat());
    setThreshold(settings.value("threshold", 25).toInt());

    setTopMargin(settings.value("margin_top", 0.0).toFloat());
    setBottomMargin(settings.value("margin_bottom", 0.0).toFloat());
    setRightMargin(settings.value("margin_right", 0.0).toFloat());
    setLeftMargin(settings.value("margin_left", 0.0).toFloat());

    setPointsMin(settings.value("points_min", 10).toInt());
    setPointsMax(settings.value("points_max", 600).toInt());

    setOblatenessLow(settings.value("oblateness_low", 0.67).toInt());
    setOblatenessHigh(settings.value("oblateness_high", 1.5).toInt());
}

void FramePupilDetector::saveSettings(QSettings & settings) const
{
    settings.setValue("mirrored", mirrored());
    settings.setValue("equalize_hist", equalizeHistogram());
    settings.setValue("contrast", contrast());
    settings.setValue("brightness", brightness());
    settings.setValue("gamma", gamma());
    settings.setValue("threshold", threshold());

    settings.setValue("margin_top", topMargin());
    settings.setValue("margin_bottom", bottomMargin());
    settings.setValue("margin_right", rightMargin());
    settings.setValue("margin_left", leftMargin());

    settings.setValue("points_min", pointsMin());
    settings.setValue("points_max", pointsMax());

    settings.setValue("oblateness_low", oblatenessLow());
    settings.setValue("oblateness_high", oblatenessHigh());
}

void FramePupilDetector::processFrame(cv::Mat & frame)
{
    if(m_mirrored)
        cv::flip(frame, frame, 1); // horizontal flip

    //if(m_equalizeHistogram)
    //    frame = equalizeIntensity(frame);

    frame.convertTo(frame, -1, m_contrast, m_brightness);

    frame = correctGamma(frame, m_gamma);

    cv::Mat monoFrame;
    cv::cvtColor(frame, monoFrame, CV_BGR2GRAY);

    if(m_equalizeHistogram)
        cv::equalizeHist(monoFrame, monoFrame);

    cv::Mat thresholded;
    // find areas darker than threshold
    cv::threshold(monoFrame, thresholded, m_threshold, 255, CV_THRESH_BINARY);

    cv::Mat drawFrame;
    switch(m_previewType)
    {
        case PreviewColor:
            drawFrame = frame.clone();
            break;
        case PreviewGrayscale:
            cv::cvtColor(monoFrame, drawFrame, CV_GRAY2BGR);
            break;
        case PreviewThreshold:
            cv::cvtColor(thresholded, drawFrame, CV_GRAY2BGR);
            break;
        default:
            drawFrame = frame.clone();
    }

    const PupilDetectionResult result = detect(thresholded, drawFrame);

    frame = drawFrame;

    emit pupilData(result == Ok,
                   m_pupilX,
                   m_pupilY,
                   m_pupilSize);

    /*
    if(frame.cols == 0.0 || frame.rows == 0.0)
        emit pupilData(false, -1, -1, 0);
    else
        emit pupilData(result == Ok,
                       m_pupilX / double(frame.cols),
                       m_pupilY / double(frame.rows),
                       m_pupilSize);
    */
}

FramePupilDetector::PupilDetectionResult FramePupilDetector::detect(const cv::Mat & frame,
                                                                    cv::Mat & drawFrame)
{
    cv::Mat tmp;
    frame.copyTo(tmp);

    const double xFrom = m_leftMargin * frame.cols;
    const double xTo   = frame.cols * (1.0 - m_rightMargin);
    const double yFrom = m_topMargin * frame.rows;
    const double yTo   = frame.rows * (1.0 - m_bottomMargin);

    if(!drawFrame.empty())
    {
        const cv::Point points[4] = {
            cv::Point(xFrom, yFrom),
            cv::Point(xTo, yFrom),
            cv::Point(xTo, yTo),
            cv::Point(xFrom, yTo)
        };
        const auto color = cv::Scalar(255, 255, 255);
        cv::line(drawFrame, points[0], points[1], color);
        cv::line(drawFrame, points[1], points[2], color);
        cv::line(drawFrame, points[2], points[3], color);
        cv::line(drawFrame, points[3], points[0], color);
    }

    std::vector<std::vector<cv::Point>> contours;
    std::vector<cv::Vec4i> hierarchy;

    cv::findContours(tmp, contours,
                     hierarchy,
                     CV_RETR_TREE,
                     CV_CHAIN_APPROX_NONE);

    cv::RotatedRect firstCandidateRects[MAX_FIRST_CANDIDATES];
    size_t numCandidates = 0;

    // find pupil candidates
    for(const auto & contour : contours)
    {
        // contour of the area is too short or too long
        if(contour.size() < m_pointsMin || contour.size() > m_pointsMax)
            continue;

        const cv::RotatedRect r = cv::fitEllipse(contour);

        // Is the center of ellipse in dark area?
        // TODO: this crashes
        /*const unsigned char* p = tmp.ptr<unsigned char>((int)(r.center.y) - 0);
        if(p[(int)(r.center.x) - 0] > 0)
        {
            //The center is NOT in dark area.
            continue;
        }*/

        const float oblateness = r.size.height / r.size.width;
        if(oblateness > m_oblatenessLow &&
           oblateness < m_oblatenessHigh &&
           r.center.x > xFrom &&
           r.center.y > yFrom &&
           r.center.x < xTo &&
           r.center.y < yTo)
        {
            if(!drawFrame.empty())
                drawPupil(drawFrame, r, CV_RGB(0, 255, 0), 1);

            firstCandidateRects[numCandidates] = r;
            numCandidates++;

            if(numCandidates >= MAX_FIRST_CANDIDATES)
                break;
        }
    }

    if(numCandidates == 0)
    {
        if(!drawFrame.empty())
            cv::putText(drawFrame,
                        "NO_PUPIL_CANDIDATE",
                        cv::Point2d(0, 16),
                        cv::FONT_HERSHEY_PLAIN,
                        1.0,
                        CV_RGB(255, 0, 0)
            );
        return NoPupilCandidate;
    }
    else if(numCandidates >= MAX_FIRST_CANDIDATES)
    {
        if(!drawFrame.empty())
            cv::putText(drawFrame,
                        "TOO_MANY_PUPIL_CANDIDATES",
                        cv::Point2d(0, 16),
                        cv::FONT_HERSHEY_PLAIN,
                        1.0,
                        CV_RGB(255, 0, 0)
            );
        return TooManyPupilCandidates;
    }
    else
    {
        if(!drawFrame.empty())
            cv::putText(drawFrame,
                        "PUPIL_DETECTED",
                        cv::Point2d(0, 16),
                        cv::FONT_HERSHEY_PLAIN,
                        1.0,
                        CV_RGB(0, 255, 0)
            );
    }

    // find candidate with largest size
    int maxSizeIndex = 0;
    double maxSize = -1.0;
    for(size_t i = 0; i < numCandidates; i++)
    {
        const auto & ellipseSize = firstCandidateRects[i].size;
        // assume size is proportional to area
        const double size = double(ellipseSize.width) * double(ellipseSize.height);
        if(size > maxSize)
        {
            maxSizeIndex = i;
            maxSize = size;
        }
    }

    const cv::RotatedRect pupilRect = firstCandidateRects[maxSizeIndex];

    if(!drawFrame.empty())
        drawPupil(drawFrame, pupilRect, CV_RGB(0, 255, 192), 2);

    m_pupilX = pupilRect.center.x;
    m_pupilY = pupilRect.center.y;
    m_pupilSize = pupilRect.size.width * pupilRect.size.height / 4.0; // area

    return Ok;
}

//---------------------------------------------------------------------------------

PupilDetectorSetupWindow::PupilDetectorSetupWindow(QWidget * parent)
    : QDialog(parent)
    , m_pupilDetector(nullptr)
{
    m_gui.setupUi(this);

    connect(m_gui.cameraIndexSpinBox,
            static_cast<void (QSpinBox::*)(int)>(&QSpinBox::valueChanged), // isn't C++ beautiful?
            [&](int value){
                // do not emit cameraIndexChanged when no pupilDetector is connected
                if(m_pupilDetector)
                    emit cameraIndexChanged(value);
            }
    );

    connect(m_gui.mirrorCheckBox, &QCheckBox::stateChanged, [&](int value){
        if(m_pupilDetector)
            m_pupilDetector->setMirrored(value != 0);
    });

    connect(m_gui.equalizeHistogramCheckBox, &QCheckBox::stateChanged, [&](int value){
        if(m_pupilDetector)
            m_pupilDetector->setEqualizeHistogram(value != 0);
    });

    connect(m_gui.previewTypeComboBox,
            static_cast<void (QComboBox::*)(int)>(&QComboBox::currentIndexChanged),
            [&](int index){
                if(m_pupilDetector)
                {
                    FramePupilDetector::PreviewType previewType;
                    switch(index)
                    {
                        case 0:
                            previewType = FramePupilDetector::PreviewColor;
                            break;
                        case 1:
                            previewType = FramePupilDetector::PreviewGrayscale;
                            break;
                        case 2:
                            previewType = FramePupilDetector::PreviewThreshold;
                            break;
                        default:
                            previewType = FramePupilDetector::PreviewGrayscale;
                    }
                    m_pupilDetector->setPreviewType(previewType);
                }
            }
    );

    connect(m_gui.thresholdSlider, &QSlider::valueChanged, [&](int value){
        m_gui.thresholdValueLabel->setText(QString::number(value));
        if(m_pupilDetector)
            m_pupilDetector->setThreshold(value);
    });

    connect(m_gui.contrastSlider, &QSlider::valueChanged, [&](int value){
        const double v = double(value) / m_contrastCoeff;
        m_gui.contrastValueLabel->setText(QString::number(v, 'f', 1));
        if(m_pupilDetector)
            m_pupilDetector->setContrast(v);
    });

    connect(m_gui.brightnessSlider, &QSlider::valueChanged, [&](int value){
        const double v = double(value) / m_brightnessCoeff;
        m_gui.brightnessValueLabel->setText(QString::number(v, 'f', 0));
        if(m_pupilDetector)
            m_pupilDetector->setBrightness(v);
    });

    connect(m_gui.gammaSlider, &QSlider::valueChanged, [&](int value){
        const double v = double(value) / m_gammaCoeff;
        m_gui.gammaValueLabel->setText(QString::number(v, 'f', 1));
        if(m_pupilDetector)
            m_pupilDetector->setGamma(v);
    });

    connect(m_gui.marginTopSlider, &QSlider::valueChanged, [&](int value){
        const double v = double(value) / m_marginCoeff;
        m_gui.marginTopValueLabel->setText(QString::number(v, 'f', 1));
        if(m_pupilDetector)
            m_pupilDetector->setTopMargin(v);
    });

    connect(m_gui.marginBottomSlider, &QSlider::valueChanged, [&](int value){
        const double v = double(value) / m_marginCoeff;
        m_gui.marginBottomValueLabel->setText(QString::number(v, 'f', 1));
        if(m_pupilDetector)
            m_pupilDetector->setBottomMargin(v);
    });

    connect(m_gui.marginRightSlider, &QSlider::valueChanged, [&](int value){
        const double v = double(value) / m_marginCoeff;
        m_gui.marginRightValueLabel->setText(QString::number(v, 'f', 1));
        if(m_pupilDetector)
            m_pupilDetector->setRightMargin(v);
    });

    connect(m_gui.marginLeftSlider, &QSlider::valueChanged, [&](int value){
        const double v = double(value) / m_marginCoeff;
        m_gui.marginLeftValueLabel->setText(QString::number(v, 'f', 1));
        if(m_pupilDetector)
            m_pupilDetector->setLeftMargin(v);
    });

    connect(m_gui.pointsMinSlider, &QSlider::valueChanged, [&](int value){
        m_gui.pointMinValueLabel->setText(QString::number(value));
        if(m_pupilDetector)
            m_pupilDetector->setPointsMin(value);
    });

    connect(m_gui.pointsMaxSlider, &QSlider::valueChanged, [&](int value){
        m_gui.pointMaxValueLabel->setText(QString::number(value));
        if(m_pupilDetector)
            m_pupilDetector->setPointsMax(value);
    });

    connect(m_gui.oblatenessLowSlider, &QSlider::valueChanged, [&](int value){
        const double v = double(value) / m_oblatenessCoeff;
        m_gui.oblatenessLowValueLabel->setText(QString::number(v, 'f', 2));
        if(m_pupilDetector)
            m_pupilDetector->setOblatenessLow(v);
    });

    connect(m_gui.oblatenessHighSlider, &QSlider::valueChanged, [&](int value){
        const double v = double(value) / m_oblatenessCoeff;
        m_gui.oblatenessHighValueLabel->setText(QString::number(v, 'f', 2));
        if(m_pupilDetector)
            m_pupilDetector->setOblatenessHigh(v);
    });

    connect(m_gui.acceptButton, &QPushButton::clicked, [&](){
        accept();
        close();
    });

    connect(m_gui.exitButton, &QPushButton::clicked, [&](){
        reject();
        close();
    });
}

PupilDetectorSetupWindow::~PupilDetectorSetupWindow()
{
    setVideoSource(nullptr, 0); // disconnect from m_pupilDetector
}

void PupilDetectorSetupWindow::setVideoSource(FramePupilDetector * pupilDetector, int cameraIndex)
{
    if(m_pupilDetector)
        m_gui.cameraView->disconnect();

    m_pupilDetector = pupilDetector;

    if(!m_pupilDetector)
        return;

    m_gui.cameraView->connect(m_pupilDetector, SIGNAL(imageReady(QImage)), SLOT(setImage(QImage)));

    qDebug() << "Video source connected...";

    m_gui.cameraIndexSpinBox->setValue(cameraIndex);
    m_gui.mirrorCheckBox->setChecked(m_pupilDetector->mirrored());
    m_gui.equalizeHistogramCheckBox->setChecked(m_pupilDetector->equalizeHistogram());

    m_pupilDetector->setPreviewType(FramePupilDetector::PreviewGrayscale);
    m_gui.previewTypeComboBox->setCurrentIndex(1);

    m_gui.thresholdSlider->setValue(m_pupilDetector->threshold());
    m_gui.contrastSlider->setValue(int(m_pupilDetector->contrast() * m_contrastCoeff));
    m_gui.brightnessSlider->setValue(int(m_pupilDetector->brightness() * m_brightnessCoeff));
    m_gui.gammaSlider->setValue(int(m_pupilDetector->gamma() * m_gammaCoeff));

    m_gui.pointsMinSlider->setValue(m_pupilDetector->pointsMin());
    m_gui.pointsMaxSlider->setValue(m_pupilDetector->pointsMax());

    m_gui.marginTopSlider->setValue(int(m_pupilDetector->topMargin() * m_marginCoeff));
    m_gui.marginBottomSlider->setValue(int(m_pupilDetector->bottomMargin() * m_marginCoeff));
    m_gui.marginRightSlider->setValue(int(m_pupilDetector->rightMargin() * m_marginCoeff));
    m_gui.marginLeftSlider->setValue(int(m_pupilDetector->leftMargin() * m_marginCoeff));

    m_gui.oblatenessLowSlider->setValue(int(m_pupilDetector->oblatenessLow() * m_oblatenessCoeff));
    m_gui.oblatenessHighSlider->setValue(int(m_pupilDetector->oblatenessHigh() * m_oblatenessCoeff));
}

void PupilDetectorSetupWindow::showEvent(QShowEvent * event)
{
    Q_UNUSED(event);
    setResult(-1);
}

void PupilDetectorSetupWindow::closeEvent(QCloseEvent * event)
{
    Q_UNUSED(event);
    qDebug() << "Video source disconnected";
    setVideoSource(nullptr, 0);
    emit finished(result() == QDialog::Accepted);
}
