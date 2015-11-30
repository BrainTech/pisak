TEMPLATE = app

TARGET = pisak-eyetracker-hpe

QT += core gui widgets qml quick

CONFIG += c++11

LIBS += -lGL -lGLU \
    -lpthread \
    -lopencv_core \
    -lopencv_highgui \
    -lopencv_imgproc \
    -lopencv_calib3d \
    -lopencv_video

# remove possible other optimization flags
QMAKE_CXXFLAGS_RELEASE -= -O
QMAKE_CXXFLAGS_RELEASE -= -O1
QMAKE_CXXFLAGS_RELEASE -= -O2

# add the desired -O3 if not present
QMAKE_CXXFLAGS_RELEASE *= -O3

INCLUDEPATH += \
    ../common

SOURCES += main.cpp \
    opencvcapture.cpp \
    pupildetector.cpp \
    ../common/eyetracker.cpp \
    ../common/smoother.cpp \
    cameraeyetracker.cpp \
    calibration.cpp \
    hpe/glm.cpp \
    hpe/hpewidget.cpp

HEADERS  += \
    opencvcapture.h \
    pupildetector.h \
    ../common/etr_main.h \
    ../common/eyetracker.h \
    ../common/smoother.h \
    cameraeyetracker.h \
    calibration.h \
    hpe/glm.h \
    hpe/pstream.h \
    hpe/hpewidget.h

FORMS += \
    camera_setup.ui

RESOURCES += \
    ../common/qml.qrc
