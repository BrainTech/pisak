import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Window 2.1

import pisak.eyetracker 1.0

ApplicationWindow {
    id: applicationWnd
    visible: true
    visibility: "FullScreen"
    width: Screen.width
    height: Screen.height
    title: qsTr("Eyetracker calibration")
    color: "#555" // background color

    property bool shutdownCompleted: false

    Component.onCompleted: {
        calibration.initialize()
    }

    onClosing: {
        if(shutdownCompleted) {
            close.accepted = true
        } else {
            close.accepted = false
            calibration.shutdown()
        }
    }

    MouseArea {
        id: wndMouseArea
        anchors.fill: parent
        cursorShape: Qt.CrossCursor
    }

    Timer {
        id: calibrationStartDelayTimer
        interval: 2000
        running: false
        repeat: false
        onTriggered: calibration.calibrationStart()
    }

    Eyetracker {
        id: calibration

        function getCalibrationPoints() {
            var verticalMargin = 0.1
            var horizontalMargin = 0.06
            return [
                Qt.point(0.5, 0.5 ), // center
                Qt.point(1.0 - horizontalMargin, 0.5), // middle right
                Qt.point(1.0 - horizontalMargin, verticalMargin), // top right
                Qt.point(0.5, verticalMargin), // top middle
                Qt.point(horizontalMargin, verticalMargin), // top left
                Qt.point(horizontalMargin, 0.5), // middle left
                Qt.point(horizontalMargin, 1.0 - verticalMargin), // bottom left
                Qt.point(0.5, 1.0 - verticalMargin), // bottom middle
                Qt.point(1.0 - horizontalMargin, 1.0 - verticalMargin) // bottom rigth
            ]
        }

        function moveToNextCalibrationPoint() {
            var p = calibration.points[calibration.pointIdx]
            focusDot.moveTo(p.x, p.y)
        }

        function calibrationError(errorMessage) {
            console.log('Error: ' + errorMessage)
            focusDot.visible = false
            exitText.visible = true
            infoText.text = "<strong>Calibration error:</strong><br>" + errorMessage
            infoText.visible = true
            exitText.focus = true
        }

        function runSetup() {
            calibration.stopTracking()
            // fullscreen camera setup
            calibration.runCameraSetup()
        }

        property int pointIdx: 0
        property var points: getCalibrationPoints()

        onInitialized: {
            console.log("onInitialized")
            if(!success) {
                calibrationError(errorMessage)
                return
            } else {
                calibration.startTracking()
            }
        }

        onShutdownCompleted: {
            console.log("onShutdownCompleted")
            if(!success) {
                console.log("Eyetracker shutdown failed: ", errorMessage)
            }
            applicationWnd.shutdownCompleted = true
            applicationWnd.close()
        }

        onCameraSetupFinished: {
            console.log('onCameraSetupFinished')
            if(!success) {
                applicationWnd.close()
                return
            }

            if(calibration.saveConfig()) {
                console.log("tracker config saved")
            } else {
                console.log("error saving tracker config")
            }
            infoText.visible = false
            calibrationStartDelayTimer.running = true
            wndMouseArea.cursorShape = Qt.BlankCursor
            applicationWnd.raise()
        }

        onCalibrationStarted: {
            console.log("onCalibrationStarted")
            if(!success) {
                calibrationError(errorMessage)
                return
            }
            pointIdx = 0
            focusDot.visible = true
            moveToNextCalibrationPoint()
        }

        onCalibrationStopped: {
            console.log("onCalibrationStopped")
            if(!success) {
                calibrationError(errorMessage)
                return
            }
            console.log("Calibration stopped: OK")
            console.log("Starting tracking...")
            trackingDot.visible = true
            if(calibration.saveConfig()) {
                console.log("successfully saved config")
            } else {
                console.log("error saving config")
            }
            fixationDots.visible = true
            calibration.startTracking()
            exitText.visible = true
            exitText.focus = true
            wndMouseArea.cursorShape = Qt.CrossCursor
        }

        onPointCalibrated: {
            console.log("onPointCalibrated ", pointIdx, points.length)
            if(!success) {
                calibrationError(errorMessage)
                return
            }
            growAnimation.running = true
        }

        onComputeAndSetCalibrationFinished: {
            console.log("onComputeAndSetCalibrationFinished")
            if(!success) {
                calibrationError(errorMessage)
                return
            }
            console.log("Calibration compute: OK")
            infoText.visible = false
            calibration.calibrationStop()
        }

        onGazeDetectionFailed: {
            eyeStatus.change(false)
        }

        onGazeData: {
            //console.log(point)
            if(eyeDetected) {
                eyeStatus.change(true)
            } else {
                eyeStatus.change(false)
            }
            if(point.x !== -1 && point.y !== -1) {
                if (trackingDot.visible) {
                    trackingDot.moveTo(point.x, point.y)
                }
            }
        }
    }

    Rectangle {
        id: fixationDots
        width: parent.width
        height: parent.height
        visible: false
        focus: false
        color: 'transparent'
        layer.enabled: true

        property var dots: []

        Component.onCompleted: {
            for(var i = 0; i < calibration.points.length; i++) {
                var dot = Qt.createQmlObject('import QtQuick 2.2; Rectangle {}', fixationDots, 'fixationDot' + i)
                dot.height = applicationWnd.height * 0.03
                dot.width = dot.height
                dot.radius = dot.width * 0.5
                dot.x = calibration.points[i].x * applicationWnd.width - dot.width / 2
                dot.y = calibration.points[i].y * applicationWnd.height - dot.height / 2
                fixationDots.dots.push(dot)
            }
        }
    }

    Text {
        visible: true
        width: 0.8 * parent.width
        focus: true
        id: infoText
        anchors.centerIn: parent
        font.pixelSize: 0.08 * parent.height
        color: "#ebebeb"
        style: Text.Outline
        styleColor: "black"
        wrapMode: Text.WordWrap
        horizontalAlignment: Text.AlignHCenter
        text: qsTr("Press any key to start calibration...")

        Keys.onPressed: {
            focus = false
            eyeStatus.visible = false
            if(calibration.loadConfig()) {
                console.log("tracker config loaded")
            } else {
                console.log("error loading tracker config")
            }
            calibration.runSetup()
        }
    }

    Image {
        id: eyeStatus
        width: 0.08 * parent.height
        height: width
        x: 0.5 * (parent.width - width)
        y: 0.9 * (parent.height - height)
        visible: true
        source: "no_eye.svg"

        function change(status) {
            if (status) {
                source = "eye.svg"
            } else {
                source = "no_eye.svg"
            }
        }
    }

    Rectangle {
        id: focusDot
        width: 0.1 * parent.height
        height: width
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        visible: false
        color: "orange"
        border.color: "black"
        border.width: 1
        antialiasing: true
        radius: width * 0.5
        transformOrigin: Item.Center
        scale: 1.0

        // position of center in 0-1 coordinates
        property real posX: 0.5
        property real posY: 0.5

        onPosXChanged: { x = posX * parent.width - width / 2 }
        onPosYChanged: { y = posY * parent.height - height / 2 }

        ParallelAnimation {
            id: shrinkAnimation
            PropertyAnimation {
                target: focusDot
                properties: "color"
                from: "orange"
                to: "white"
                duration: 200
            }
            PropertyAnimation {
                target: focusDot
                properties: "scale"
                from: 1.0
                to: 0.2
                duration: 200
            }
            onStopped: {
                var p = calibration.points[calibration.pointIdx]
                calibration.calibrationAddPoint(p)
            }
        }

        ParallelAnimation {
            id: growAnimation
            PropertyAnimation {
                target: focusDot
                properties: "color"
                from: "white"
                to: "orange"
                duration: 200
            }
            PropertyAnimation {
                target: focusDot
                properties: "scale"
                from: 0.2
                to: 1.0
                duration: 200
            }
            onStopped: {
                calibration.pointIdx++
                if(calibration.pointIdx < calibration.points.length) {
                    console.log("new point:", calibration.pointIdx)
                    calibration.moveToNextCalibrationPoint()
                } else {
                    focusDot.visible = false
                    infoText.text = "Calculating calibration..."
                    infoText.visible = true
                    calibration.calibrationComputeAndSet()
                }
            }
        }

        ParallelAnimation {
            id: moveAnimation
            PropertyAnimation {
                id: moveAnimationX
                target: focusDot
                property: "posX"
                duration: 2000
                easing.type: Easing.InOutCubic
            }
            PropertyAnimation {
                id: moveAnimationY
                target: focusDot
                property: "posY"
                duration: 2000
                easing.type: Easing.InOutCubic
            }
            onStopped: {
                shrinkAnimation.running = true
            }
        }

        function moveTo(new_cx, new_cy) {
            moveAnimationX.to = new_cx
            moveAnimationY.to = new_cy
            moveAnimation.running = true
        }
    }

    Text {
        visible: false
        width: 0.8 * parent.width
        id: exitText
        y: 10
        anchors.horizontalCenter: parent.horizontalCenter
        font.pixelSize: 0.04 * parent.height
        color: "#ebebeb"
        style: Text.Outline
        styleColor: "black"
        wrapMode: Text.WordWrap
        horizontalAlignment: Text.AlignHCenter
        text: qsTr("Press any key to exit...")

        Keys.onPressed: {
            console.log('Exit in action...')
            applicationWnd.close()
        }
    }

    Rectangle {
        id: trackingDot
        width: 25
        height: width
        visible: false
        color: "orange"
        border.color: "black"
        border.width: 1
        antialiasing: true
        radius: width * 0.5

        // position of center in 0-1 coordinates
        property real posX: 0.5
        property real posY: 0.5

        onPosXChanged: { x = posX * parent.width - width / 2 }
        onPosYChanged: { y = posY * parent.height - height / 2 }

        function moveTo(new_cx, new_cy) {
            posX = new_cx
            posY = new_cy
        }
    }
}
