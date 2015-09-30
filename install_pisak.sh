#!/bin/bash

sudo add-apt-repository ppa:ethanak/milena

sudo apt-get update && sudo apt-get upgrade -y

sudo apt-get install -y git xdg-user-dirs wget libav-tools

sudo apt-get install -y gir1.2-clutter-1.0 gir1.2-clutter-gst-2.0 gir1.2-mx-1.0 gir1.2-rsvg-2.0 libmx-1.0-2 libclutter-1.0-0 gir1.2-webkit-3.0 gir1.2-gtkclutter-1.0

sudo apt-get install -y gir1.2-gst-plugins-base-0.10 gir1.2-gst-plugins-base-1.0 gstreamer0.10-plugins-good gstreamer0.10-plugins-ugly gstreamer0.10-plugins-base gstreamer0.10-plugins-bad gstreamer0.10-x gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-x gstreamer1.0-plugins-ugly libgstreamer-plugins-base0.10-0 libgstreamer-plugins-base1.0-0 gstreamer1.0-libav

sudo apt-get install -y python3 python3-gi python3-pil python3-gi-cairo python3-sqlalchemy python3-magic python3-pip python3-bs4 python3-ws4py python3-taglib python3-configobj python3-requests

sudo apt-get install -y milena

sudo pip3 install pressagio pydenticon ezodf python-wordpress-xmlrpc

# if [ -d ~/pisak ]; then
#     echo "Directory ~/pisak exists." 
# else
#     cd ~/
#     git clone http://github.com/BrainTech/pisak.git
# fi

wget download.pisak.org/n_grams.sqlite -P ~/pisak/pisak/res 

if [ -d ~/.pisak ]; then
   echo "Directory ~/.pisak already exists."
else
   mkdir ~/.pisak
fi

cd ~/.pisak
echo > configuration.ini
mkdir css json symbols icons logs
cd ~/.pisak/symboler_sheets/
echo -n > "symbols_topology.ods"

echo "Do you want the PYTHONPATH var to be extended with PISAK dir? (Y/N)."
echo "Needed for PISAK to function, press 'N' if it was already extended."
read answer

if [[ ${answer} = "Y" || ${answer} = "y" ]]; then
    echo "" >> ~/.bashrc
    echo "export PYTHONPATH=\$PYTHONPATH:.:~/pisak" >> ~/.bashrc
    echo "PYTHONPATH has been extended."
else
    echo "PYTHONPATH was not extended."
fi

echo "Do you want to extend you PATH var for easy PISAK launching?"
read answer2
if [[ ${answer2} = "Y" || ${answer2} = "y" ]]; then
    echo "export PATH=\$PATH:.:~/pisak/bin" >> ~/.bashrc
    echo "You can run PISAK by typing 'pisak' in terminal after logging out and logging in."
    exit
else
    echo "Launch scripts are in pisak/bin directory, remember to add it to your PATH variable to be able to have the apps work from the main window."
fi
