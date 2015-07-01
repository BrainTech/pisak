TEMPLATE = app

TARGET = pisak-eyetracker-mockup

QT += qml quick widgets
CONFIG += c++11

LIBS += -lopencv_core -lopencv_video

SOURCES += main.cpp \
    ../common/eyetracker.cpp \
    ../common/smoother.cpp \
    mockupeyetracker.cpp

RESOURCES += ../common/qml.qrc

INCLUDEPATH += ../common

HEADERS += \
    ../common/eyetracker.h \
    ../common/etr_main.h \
    ../common/smoother.h \
    mockupeyetracker.h
