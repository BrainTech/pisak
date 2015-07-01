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

#include <cstring>
#include <iostream>

#include <QApplication>
#include <QtQml>

template<typename EyeTrackerType>
int etr_main(int argc, char * argv[])
{
    // make sure floats are printed with dot regardless of system locale
    std::cout.imbue(std::locale("C"));

    bool trackingOnly = false;

    if(argc > 1)
    {
        for(int i = 1; i < argc; i++)
        {
            if(std::strcmp(argv[i], "--tracking") == 0)
            {
                trackingOnly = true;
                break;
            }
        }
    }

    QApplication app(argc, argv);

    if(trackingOnly)
    {
        EyeTrackerType tracker;

        QObject::connect(&tracker, &EyeTrackerType::initialized,
            [&tracker](bool success, QString errorMessage)
            {
                if(!success)
                {
                    std::cerr << "tracker initialization failed: "
                              << errorMessage.toLocal8Bit().data()
                              << std::endl;

                    QApplication::instance()->exit(1);
                }
                else
                {
                    std::cout << "tracker initialized" << std::endl;
                    tracker.startTracking();
                }
            }
        );

        QObject::connect(&tracker, &EyeTrackerType::shutdownCompleted,
            [](bool success, QString errorMessage)
            {
                if(success)
                    std::cout << "tracker shutdown completed" << std::endl;
                else
                    std::cout << "tracker shutdown error: "
                              << errorMessage.toLocal8Bit().data()
                              << std::endl;
            }
        );

        QObject::connect(&tracker, &EyeTrackerType::gazeData,
            [](bool eyeDetected, QPointF pt)
            {
                Q_UNUSED(eyeDetected);
                std::cout << "gaze_pos: " << pt.x() << " " << pt.y() << std::endl;
            }
        );

        if(tracker.loadConfig())
            std::cout << "configuration loaded" << std::endl;
        else
            std::cout << "error loading configuration" << std::endl;

        tracker.initialize();

        return app.exec();
    }
    else // calibration mode
    {
        qmlRegisterType<EyeTrackerType>("pisak.eyetracker", 1, 0, "Eyetracker");

        QQmlApplicationEngine engine;
        engine.load(QUrl(QStringLiteral("qrc:///calibration.qml")));

        return app.exec();
    }
}
