#!/bin/bash

### dodajemy repo Mileny -- a nuż kiedyś pojawią się poprawione pakiety
sudo add-apt-repository ppa:ethanak/milena -y

### repozytorium psychopy-brain
sudo sh -c "echo deb http://obci:dlugi_przedluzacz@deb-stable.braintech.pl/xenial / > /etc/apt/sources.list.d/braintech-stable-xenial.list"
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 1452AFDF

### pakiety ogólnie
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git xdg-user-dirs wget libav-tools
sudo apt-get install -y gir1.2-clutter-1.0 gir1.2-clutter-gst-2.0 gir1.2-mx-1.0 gir1.2-rsvg-2.0 libmx-1.0-2 libclutter-1.0-0 gir1.2-webkit-3.0 gir1.2-gtkclutter-1.0
sudo apt-get install -y gir1.2-gst-plugins-base-0.10 gir1.2-gst-plugins-base-1.0 gstreamer0.10-plugins-good gstreamer0.10-plugins-ugly gstreamer0.10-plugins-base gstreamer0.10-plugins-bad gstreamer0.10-x gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-x gstreamer1.0-plugins-ugly libgstreamer-plugins-base0.10-0 libgstreamer-plugins-base1.0-0 gstreamer1.0-libav
sudo apt-get install -y python3 python3-gi python3-pil python3-gi-cairo python3-configobj python3-sqlalchemy python3-magic python3-pip python3-bs4 python3-ws4py python3-taglib python3-requests python3-pyqt5 python3-cssutils python3-usb
sudo apt-get install -y psychopy-brain
sudo apt-get install -y gnome-shell
sudo apt-get install -y v4l-utils

gsettings set org.gnome.desktop.background show-desktop-icons true

### MILENA ze źródeł jeśli nie udało się zpakietów
if ! type milena_say &> /dev/null ; then
   sudo apt-get install -y sox libsox-fmt-all antiword odt2txt libenca-dev libao-dev lame faac poppler-utils vorbis-tools 
   sudo apt-get install -y mbrola mbrola-pl1
   cd
   #to chyba można położyć na pisak.org?
   wget -N http://tts.polip.com/files/milena-0.2.88.3.tar.gz
   tar xvfz milena-0.2.88.3.tar.gz
   cd  milena-0.2.88.3
   make && sudo make install
   cd 
   rm milena-0.2.88.3.tar.gz
   rm -rf milena-0.2.88.3
fi

# pydenticon depends on Pillow, installed via pip3,
# so additional libraries for building Pillow are required
sudo apt-get install -y libjpeg-dev zlib1g-dev
pip3 install --user setuptools #tego chyba brakowało
pip3 install --user pressagio pydenticon ezodf python-wordpress-xmlrpc

### PISAK
if [ -d ~/pisak ]; then
   echo "Katalog ~/pisak już jest, więc nie sciagamy nowej wersji. Jeśli chcesz zainstalować PISAKa od nowa, skasuj najpierw katalog ~/pisak, wykonując polecenia:"  #tak miało być?
   echo "cd"
   echo "rm -rf pisak"
else
   cd 
   git clone http://github.com/BrainTech/pisak.git
fi

### n_grams
wget -c -N http://download.pisak.org/n_grams.sqlite -P ~/pisak/pisak/res


if [[ $PYTHONPATH != ?(*:)$HOME/pisak?(:*) ]]; then
    echo "" >> ~/.bashrc
    echo "export PYTHONPATH=\$PYTHONPATH:~/pisak" >> ~/.bashrc
fi

if [[ $PATH != ?(*:)$HOME/pisak/bin?(:*) ]]; then
    echo "export PATH=\$PATH:.:~/pisak/bin" >> ~/.bashrc
fi

if [[ $CLUTTER_BACKEND != x11 ]]; then
    echo "export CLUTTER_BACKEND=x11" >> ~/.bashrc
fi

### PISAK-CONFIG
echo "Instalujemy z osobnego repozytorium dźwięki, symbole itp."
if [ -d ~/pisak-config ]; then
   echo "Katalog ~/pisak-config istnieje, uaktualniam pliki"
   cd ~/pisak-config
   git pull
   cd 
else
   cd 
   git clone http://github.com/BrainTech/pisak-config.git
fi

if ! [ -d ~/.pisak ]; then
  mkdir ~/.pisak
  cd 
  cp -r ~/pisak-config/* ~/.pisak
  rm -rf ~/.pisak/.git 
else
   echo "Katalog ~/.pisak juz istnieje" 
   echo "Czy chcesz nadpisac pliki konfiguracyjne PISAKa (T/N)."
   read answer4
   if [[ ${answer4} = "T" || ${answer4} = "t" ]]; then
      cd ~
      cp -r ~/pisak-config/* ~/.pisak
      rm -rf ~/.pisak/.git 
   fi
fi
cd
cp pisak/pisak/res/configs/* .pisak/configs/

### instalacja Eviacama
cd
git clone https://github.com/BrainTech/eviacam.git
cd eviacam
git checkout pisak
sudo apt-get install -y libtool automake autoconf libxext-dev libxtst-dev libgtk2.0-dev libwxgtk3.0-dev libopencv-dev libv4l-dev
./autogen.sh
./configure
make
sudo make install

### konfiguracja Eviacama
cd ~/.pisak
cp configs/eviacam .
CAM=$(v4l2-ctl --list-devices | sed -n 1p | sed 's/ [(].*$//g')
sed -i "s/cameraName=.*/cameraName=\" (Id:0) $CAM\"/g" eviacam

### prawidła pisak-switch
cd /etc/udev/rules.d
sudo sh -c 'echo "SUBSYSTEM==\"usb\", ATTR{idVendor}==\"16c0\", ATTR{idProduct}==\"05dc\", GROUP=\"plugdev\", MODE=\"0660\"" > /etc/udev/rules.d/99-pisak.rules'

### skrypty rozruchowe
cd 
(echo "#!/bin/sh";   
  echo "export CLUTTER_BACKEND=x11";   
  echo "export PATH=\$PATH:/home/$(whoami)/pisak/bin";   
  echo "export PYTHONPATH=/home/$(whoami)/pisak";   
  echo "sleep 2";   
  echo "pisak") > start_pisak.sh 
chmod +x start_pisak.sh 

(echo "#!/bin/sh";   
  echo "export CLUTTER_BACKEND=x11";   
  echo "export PYTHONPATH=/home/$(whoami)/pisak";   
  echo "sleep 2";   
  echo "python3 /home/$(whoami)/pisak/admin_panel/main.py") > konfiguruj_pisak.sh 
chmod +x konfiguruj_pisak.sh

### skróty na pulpicie
cd
if [ -d Desktop ]; then
  cd Desktop
else
  cd Pulpit
fi

(echo "[Desktop Entry]";   
  echo "Version=1.0";   
  echo "Name=PISAK";   
  echo "Exec=bash /home/$(whoami)/start_pisak.sh";   
  echo "Terminal=false";   
  echo "Type=Application";   
  echo "Icon=/home/$(whoami)/pisak/pisak/res/pisak_logo.png") > PISAK.desktop 
chmod +x PISAK.desktop 

(echo "[Desktop Entry]";   
  echo "Version=1.0";   
  echo "Name=KonfiguracjaPISAKa";   
  echo "Exec=bash /home/$(whoami)/konfiguruj_pisak.sh";   
  echo "Terminal=false";   
  echo "Type=Application";   
  echo "Icon=/home/$(whoami)/pisak/pisak/res/pisak_config.png") > KonfiguracjaPISAKa.desktop 
chmod +x KonfiguracjaPISAKa.desktop

### kompatybilność z launcherem unity
cp PISAK.desktop /home/$(whoami)/.local/share/applications/
cp KonfiguracjaPISAKa.desktop /home/$(whoami)/.local/share/applications/

### zmiania domyslnej sesji na gnome
cd
(echo "[Desktop]";echo "Session=gnome") > .dmrc
cd /var/lib/AccountsService/users
if grep -Fq "XSession" $(whoami) 
then
  sudo sed -i -e 's/XSession=.*/XSession=gnome/g' $(whoami)
else
  echo "XSession=gnome" | sudo tee --append $(whoami) > /dev/null
fi 

### komunikaty końcowe
if type ~/pisak/bin/pisak &> /dev/null ; then
  if type milena_say &> /dev/null ; then
    echo "Wygląda na to, że instalacja przebiegła pomyślnie."
    milena_say "Wygląda na to, że instalacja przebiegła pomyślnie"
    echo "Program możesz uruchomić poleceniem"
    echo "pisak"
    echo "po ponownym zalogowaniu."
    milena_say "Program możesz uruchomić poleceniem pisak po ponownym zalogowaniu"

  else
    echo "Wygląda na to, że instalacja przebiegła pomyślnie,"
    echo "ale nie udało się zainstalować syntezatora mowy,"
    echo "więc program nie będzie mógł czytać na głos wpisywanych przez Ciebie tekstów."
    echo "Program możesz uruchomić poleceniem"
    echo "pisak"
    echo "po ponownym zalogowaniu."
  fi
else
  echo "NIESTETY NIE UDAŁO SIĘ ZAINSTALOWAĆ PISAKa"
fi
