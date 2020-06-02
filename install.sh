#!/bin/bash

if [ "$(id -u)" != "0" ]; then
echo “This script must be run as root” 2>&1
exit 1
fi

sh uninstall.sh

mkdir /usr/share/nightmode-indicator
cp -R icons /usr/share/nightmode-indicator/

cp *.py /usr/share/nightmode-indicator/
chmod 755 -R /usr/share/nightmode-indicator/

cp nightmode-indicator.desktop /etc/xdg/autostart/
chmod 755 /etc/xdg/autostart/nightmode-indicator.desktop

cp nightmode-indicator.desktop /usr/share/applications/
chmod 755 /usr/share/applications/nightmode-indicator.desktop

ln -s /usr/share/nightmode-indicator/nightmode-indicator.py /usr/local/bin/nightmode-indicator
chmod 755 /usr/local/bin/nightmode-indicator
