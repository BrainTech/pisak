#!/bin/bash

sudo add-apt-repository ppa:ethanak/milena

sudo apt-get update && sudo apt-get upgrade -y

sudo apt-get install -y git xdg-user-dirs wget

sudo apt-get install -y gir1.2-clutter-1.0 gir1.2-clutter-gst-2.0 gir1.2-mx-1.0 gir1.2-rsvg-2.0 libmx-1.0-2 libclutter-1.0-0 gir1.2-webkit-3.0 gir1.2-gtkclutter-1.0

sudo apt-get install -y gir1.2-gst-plugins-base-0.10 gir1.2-gst-plugins-base-1.0 gstreamer0.10-plugins-good gstreamer0.10-plugins-ugly gstreamer0.10-plugins-base gstreamer0.10-plugins-bad gstreamer0.10-x gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-x gstreamer1.0-plugins-ugly libgstreamer-plugins-base0.10-0 libgstreamer-plugins-base1.0-0 gstreamer1.0-libav

sudo apt-get install -y python3 python3-gi python3-pil python3-gi-cairo python3-sqlalchemy python3-magic python3-pip python3-bs4 python3-ws4py

sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtmultimedia

sudo apt-get install -y python3-taglib libav-tools

sudo apt-get install -y milena

sudo pip3 install pressagio configobj pydenticon ezodf python-wordpress-xmlrpc

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
mkdir css json music movies symbols icons documents logs
cd ~/.pisak/symbols
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

echo "Do you want to add a shell script to ~/bin/ for easy PISAK launching?"
read answer2
if [[ ${answer2} = "Y" || ${answer2} = "y" ]]; then
    if [ -d ~/bin ]; then
        echo "Directory ~/bin exists." 
    else
        mkdir ~/bin
    fi
    echo "#!/bin/bash" > ~/bin/pisak
    echo "cd ~/pisak" >> ~/bin/pisak
    echo "python3 pisak/pisak_main.py \"\$@\"" >> ~/bin/pisak
    chmod +x ~/bin/pisak
    echo "pisak has been established in ~/bin/."
    echo "" >> ~/.bashrc
    echo "export PATH=\$PATH:.:~/bin" >> ~/.bashrc
    echo "You can run PISAK by typing 'pisak' in terminal after logging out and logging in."
    exit
else
    echo "You can start PISAK by going to PISAK's main dir and issuing the command 'python3 pisak/pisak_main.py'."
fi
