#!/bin/bash

if [ -d ~/pisak-config ]; then
   echo "Directory ~/pisak-config exists."
   cd ~/pisak-config
   git pull
   cd ~/
else
   cd ~/
   git clone http://github.com/BrainTech/pisak-config.git
fi

if [ -d ~/.pisak ]; then
   echo "Directory ~/.pisak already exists."
else
   mkdir ~/.pisak
fi

echo "Do you want to overwrite PISAK config? (Y/N)."
read answer

if [[ ${answer} = "Y" || ${answer} = "y" ]]; then
    cd ~
    cp -r ~/pisak-config/* ~/.pisak
    rm -rf ~/.pisak/.git
fi

