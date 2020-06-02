#!/bin/bash

if [ "$(id -u)" != "0" ]; then
echo “This script must be run as root” 2>&1
exit 1
fi

rm -rf /usr/share/nightmode-indicator
rm -f /usr/share/applications/nightmode-indicator.desktop
rm -f /etc/xdg/autostart/nightmode-indicator.desktop
rm -f /usr/local/bin/nightmode-indicator
