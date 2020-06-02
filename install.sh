#!/bin/bash

if [ "$(id -u)" != "0" ]; then
echo “This script must be run as root” 2>&1
exit 1
fi

sh uninstall.sh

mkdir /usr/share/nightlight-indicator
cp -R icons /usr/share/nightlight-indicator/

cp *.py /usr/share/nightlight-indicator/
chmod 755 -R /usr/share/nightlight-indicator/

cp nightlight-indicator.desktop /etc/xdg/autostart/
chmod 755 /etc/xdg/autostart/nightlight-indicator.desktop

cp nightlight-indicator.desktop /usr/share/applications/
chmod 755 /usr/share/applications/nightlight-indicator.desktop

ln -s /usr/share/nightlight-indicator/nightlight-indicator.py /usr/local/bin/nightlight-indicator
chmod 755 /usr/local/bin/nightlight-indicator
