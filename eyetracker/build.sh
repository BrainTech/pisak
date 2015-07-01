#!/bin/bash

cd mockup
qmake pisak-eyetracker-mockup.pro
make -j4
cd ..

cd camera
qmake pisak-eyetracker-hpe.pro
make -j4
cd ..

cd tobii
qmake pisak-eyetracker-tobii.pro
make -j4
cd ..

