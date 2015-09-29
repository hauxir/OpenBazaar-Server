#!/bin/bash
# Script to install the OpenBazaar Server
# run as sudo 

#install packages
apt-get update

packages=(python python-pip python-dev pylint libffi-dev libsodium-dev)

for package in "${packages[@]}"
do
    apt-get install $package -y
done

easy_install pip
pip install -r requirements.txt 

#might be needed
#make
#sudo python keyutils/setup.py install


while true; do
    read -p "Do you wish to start the Server?" yn
    case $yn in
        [Yy]* ) python openbazaard.py start; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer [Y]es or [N]o.";;
    esac
done


