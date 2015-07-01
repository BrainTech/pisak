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

#ifndef MOCKUPEYETRACKER_H
#define MOCKUPEYETRACKER_H

#include <QTimer>
#include "../common/eyetracker.h"

class MockupEyetracker : public Eyetracker
{
    Q_OBJECT

public:
    explicit MockupEyetracker(QObject * parent = 0);
    ~MockupEyetracker();

    Q_INVOKABLE QString getBackend() const override;

    Q_INVOKABLE bool loadConfig() override;
    Q_INVOKABLE bool saveConfig() const override;

    Q_INVOKABLE void runCameraSetup() override;

    Q_INVOKABLE bool startTracking() override;
    Q_INVOKABLE bool stopTracking() override;

public slots:
    void initialize() override;
    void shutdown() override;

    void calibrationStart() override;
    void calibrationStop() override;
    void calibrationAddPoint(QPointF point) override;
    void calibrationComputeAndSet() override;

protected:
    const char * getBackendCodename() const override;
    QString getConnectedEyeTracker() const;

private:
    bool m_initialized;
    QTimer m_pollTimer;

private slots:
    void generateNewPointFromCursorPos();
};

#endif // MOCKUPEYETRACKER_H
