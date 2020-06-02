#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Nightmode Indicator
#
# Copyright (c) 2019 - 2020 AXeL

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GdkPixbuf, GLib, Gio, AppIndicator3 as AppIndicator
import os, subprocess, webbrowser
import sys

class NightmodeStatus:
	On, Off = (True, False)

class NightmodeIndicator():
	def __init__(self):
		# Setup Indicator Applet
		self.indicator = AppIndicator.Indicator.new('nightmode-indicator', 'nightmode', AppIndicator.IndicatorCategory.APPLICATION_STATUS)
		self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

		# Set Attributes
		self.nightmode_schema = 'org.gnome.settings-daemon.plugins.color'
		self.nightmode_key = 'night-light-enabled'
		self.gsettings = Gio.Settings.new(self.nightmode_schema)
		self.default_text_editor = 'gedit'
		self.keep_nightmode_always_on = '--always-on' in sys.argv[1:]

		# Keep Nightmode always on
		if self.keep_nightmode_always_on:
			# Monitor Nightmode every 10 seconds
			GLib.timeout_add_seconds(10, self.monitor_nightmode)

		# Get Nightmode Status
		self.status = self.get_nightmode_status()

		# Set Indicator Icon
		self.set_icon()

		# Setup The Menu
		self.menu = Gtk.Menu()

		# Menu Item: Turn On / Off
		if self.status == NightmodeStatus.On:
			label = 'Turn off'
			#restart_sensitivity = True
		else:
			label = 'Turn on'
			#restart_sensitivity = False
		self.turnOnOffItem = Gtk.MenuItem(label)
		self.turnOnOffItem.connect('activate', self.toggle_nightmode)
		self.menu.append(self.turnOnOffItem)

		# Menu Item: Restart
		self.restartItem = Gtk.MenuItem('Restart')
		#self.restartItem.set_sensitive(restart_sensitivity)
		self.restartItem.connect('activate', self.restart_nightmode)
		self.menu.append(self.restartItem)
		self.menu.append(Gtk.SeparatorMenuItem())

		# Menu Item: Display settings
		displaySettinsItem = Gtk.MenuItem('Display settings')
		displaySettinsItem.connect('activate', self.open_display_settings)
		self.menu.append(displaySettinsItem)
		self.menu.append(Gtk.SeparatorMenuItem())

		# Menu Item: Indicator
		indicatorMenu = Gtk.Menu()
		indicatorItem = Gtk.MenuItem('Indicator')
		indicatorItem.set_submenu(indicatorMenu)
		self.menu.append(indicatorItem)

		# SubMenu Item: Refresh
		refreshItem = Gtk.MenuItem('Refresh')
		refreshItem.connect('activate', self.update_status)
		indicatorMenu.append(refreshItem)

		# SubMenu Item: About
		aboutItem = Gtk.MenuItem('About')
		aboutItem.connect('activate', self.about)
		indicatorMenu.append(aboutItem)

		# Menu Item: Quit
		exitItem = Gtk.MenuItem('Quit\t\t\t\t\t') # tabulations used to get some space
		exitItem.connect('activate', self.quit)
		self.menu.append(exitItem)

		# Show All Menu Items
		self.menu.show_all()

		# Assign Menu To Indicator
		self.indicator.set_menu(self.menu)

	def get_nightmode_status(self):
		status = self.gsettings.get_boolean(self.nightmode_key)
		print('Night mode is: %s' % ('On' if status else 'Off'))
		return status

	def open_file_in_editor(self, widget, filename):
		editor = os.getenv('EDITOR')
		if editor is None:
			editor = self.default_text_editor
		subprocess.Popen(self.pkexec_args + [editor, filename])

	def open_path(self, widget, path):
		subprocess.Popen(['xdg-open', path])

	def open_url(self, widget, url):
		webbrowser.open(url)

	def open_display_settings(self, widget):
		subprocess.Popen(['gnome-control-center', 'display'])

	def monitor_nightmode(self, loop = True):
		# Enable Nightmode if disabled
		if self.keep_nightmode_always_on and self.get_nightmode_status() == NightmodeStatus.Off:
			self.enable_nightmode(True)
		
		if not loop or not self.keep_nightmode_always_on:
			return False # Do not loop
		else:
			return True # Loop

	def toggle_nightmode(self, widget):
		# Disable Widget
		widget.set_sensitive(False)
		# Turn On/Off Nightmode
		if self.status == NightmodeStatus.On:
			self.disable_nightmode()
		else:
			self.enable_nightmode()
		# Update Status
		self.update_status(widget)

	def enable_nightmode(self, update_status = False, widget = None):
		self.gsettings.set_boolean(self.nightmode_key, True)
		if update_status:
			# Update Status
			self.update_status(widget)

	def disable_nightmode(self):
		self.gsettings.set_boolean(self.nightmode_key, False)

	def restart_nightmode(self, widget):
		# Disable Turn On/Off Menu Item
		self.turnOnOffItem.set_sensitive(False)
		# Disable Widget
		widget.set_sensitive(False)
		# Set Indicator Icon 'Off'
		self.set_icon('sun-off.svg')
		# Disable night mode
		self.disable_nightmode()
		# Enable night mode after 1 second & update status
		GLib.timeout_add_seconds(1, self.enable_nightmode, True, widget)

	def update_status(self, widget):
		# Update Nightmode Status
		#old_status = self.status
		self.status = self.get_nightmode_status()
		# Enable Widget
		if widget is not None:
			widget.set_sensitive(True)
		# Set Indicator Icon
		self.set_icon()
		# Change Turn On/Off Menu Item Label & sensitivity
		if self.status == NightmodeStatus.On:
			self.turnOnOffItem.set_label('Turn off')
			#self.restartItem.set_sensitive(True)
		else:
			self.turnOnOffItem.set_label('Turn on')
			#self.restartItem.set_sensitive(False)
		self.turnOnOffItem.set_sensitive(True)

	def set_icon(self, icon_name = None):
		if icon_name is None:
			icon_name = 'sun-off.svg'
			if self.status == NightmodeStatus.On:
				icon_name = 'sun.svg'
		icon = os.path.dirname(os.path.realpath(__file__)) + '/icons/' + icon_name
		if os.path.exists(icon):
			self.indicator.set_icon(icon)
		else:
			print('ERROR: Cannot find icon %s' % icon)

	def about(self, widget):
		about_dialog = Gtk.AboutDialog()
		about_dialog.set_position(Gtk.WindowPosition.CENTER)
		logo = GdkPixbuf.Pixbuf.new_from_file(os.path.dirname(os.path.realpath(__file__)) + '/icons/sun.svg')
		about_dialog.set_logo(logo)
		about_dialog.set_program_name('Nightmode Indicator')
		about_dialog.set_version('1.0')
		about_dialog.set_comments('A night mode indicator for Gnome based Linux desktops')
		about_dialog.set_website('https://github.com/AXeL-dev/nightmode-indicator')
		about_dialog.set_website_label('GitHub')
		about_dialog.set_copyright('Copyright © 2020 AXeL-dev')
		about_dialog.set_authors(['AXeL-dev <contact.axel.dev@gmail.com> (Developer)'])
		about_dialog.set_license('''Xampp Indicator, A night mode indicator for Gnome based Linux desktops.
Copyright © 2020 AXeL-dev

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.''')
		about_dialog.run()
		about_dialog.destroy()

	def quit(self, widget):
		Gtk.main_quit()

	def main(self):
		Gtk.main()

if __name__ == '__main__':
	indicator = NightmodeIndicator()
	indicator.main()
