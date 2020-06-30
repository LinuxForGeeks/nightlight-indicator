#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Nightlight Indicator
#
# Copyright (c) 2019 - 2020 AXeL

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GdkPixbuf, GLib, Gio, AppIndicator3 as AppIndicator
import os, subprocess, webbrowser
import sys
import dbus  
from dbus.mainloop.glib import DBusGMainLoop

class NightlightStatus:
	On, Off = (True, False)

class NightlightIndicator():
	def __init__(self):
		# Setup Indicator Applet
		self.indicator = AppIndicator.Indicator.new('nightlight-indicator', 'nightlight', AppIndicator.IndicatorCategory.APPLICATION_STATUS)
		self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

		# Set Attributes
		self.nightlight_schema = 'org.gnome.settings-daemon.plugins.color'
		self.nightlight_key = 'night-light-enabled'
		self.gsettings = Gio.Settings.new(self.nightlight_schema)
		self.default_text_editor = 'gedit'
		cmd_line_args = sys.argv[1:]
		self.keep_nightlight_always_on = '--always-on' in cmd_line_args
		self.restart_on_startup = '--restart-on-startup' in cmd_line_args
		self.restart_on_unlock = '--restart-on-unlock' in cmd_line_args
		self.restart_on_monitor_flicker = '--restart-on-monitor-flicker' in cmd_line_args
		self.isMonitorGoingOff = False

		# Print Command Line Arguments Status
		print('---------------------------')
		print('Always on: %s' % ('Enabled' if self.keep_nightlight_always_on else 'Disabled'))
		print('Restart on startup: %s' % ('Enabled' if self.restart_on_startup else 'Disabled'))
		print('Restart on unlock: %s' % ('Enabled' if self.restart_on_unlock else 'Disabled'))
		print('Restart on monitor flicker: %s' % ('Enabled' if self.restart_on_monitor_flicker else 'Disabled'))
		print('---------------------------')

		# Get Nightlight Status
		self.status = self.get_nightlight_status()

		# Set Indicator Icon
		self.set_icon()

		# Setup The Menu
		self.menu = Gtk.Menu()

		# Menu Item: Turn On / Off
		if self.status == NightlightStatus.On:
			label = 'Turn off'
			#restart_sensitivity = True
		else:
			label = 'Turn on'
			#restart_sensitivity = False
		self.turnOnOffItem = Gtk.MenuItem(label)
		self.turnOnOffItem.connect('activate', self.toggle_nightlight)
		self.menu.append(self.turnOnOffItem)

		# Menu Item: Restart
		self.restartItem = Gtk.MenuItem('Restart')
		#self.restartItem.set_sensitive(restart_sensitivity)
		self.restartItem.connect('activate', self.restart_nightlight)
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

		# Watch Nightlight every 5 seconds
		GLib.timeout_add_seconds(5, self.watch_nightlight)

		# Watch dbus messages
		DBusGMainLoop(set_as_default=True)
		bus = dbus.SessionBus()
		bus.add_match_string("type='signal',interface='org.gnome.ScreenSaver'")
		bus.add_match_string_non_blocking("interface='org.gnome.Mutter.IdleMonitor',eavesdrop='true'")
		bus.add_message_filter(self.on_dbus_message)

		# Restart on startup
		if self.restart_on_startup:
			self.restart_nightlight(self.restartItem)

	def get_nightlight_status(self, print_status = True):
		status = self.gsettings.get_boolean(self.nightlight_key)
		if print_status:
			print('Night light is: %s' % ('On' if status else 'Off'))
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

	def watch_nightlight(self, loop = True):
		# Get status
		old_status = self.status
		self.status = self.get_nightlight_status(False)
		# Enable Nightlight if disabled & keep always on is true
		if self.keep_nightlight_always_on and self.status == NightlightStatus.Off:
			self.enable_nightlight()
		# Update Status
		if self.status != old_status:
			self.update_status()
		# Continue?
		if not loop:
			return False # Do not loop
		else:
			return True # Loop

	def on_dbus_message(self, bus, message):
		member = message.get_member()
		# Screen lock/unlock
		if member == 'ActiveChanged':
			args = message.get_args_list()
			if args[0] == True:
				print('Screen Locked')
			else:
				print('Screen Unlocked')
				if self.restart_on_unlock:
					self.restart_nightlight(self.restartItem)
		# Monitor state change
		elif member == 'AddUserActiveWatch':
			self.isMonitorGoingOff = True
			print('Monitor off')
			return
		elif member == 'RemoveWatch':
			print('Monitor on')
		elif member == 'WatchFired' and self.isMonitorGoingOff:
			print('Monitor flickers')
			if self.restart_on_monitor_flicker:
				self.restart_nightlight(self.restartItem)
		# Reset isMonitorGoingOff value
		self.isMonitorGoingOff = False

	def toggle_nightlight(self, widget):
		# Disable Widget
		widget.set_sensitive(False)
		# Turn On/Off Nightlight
		if self.status == NightlightStatus.On:
			self.disable_nightlight()
		else:
			self.enable_nightlight()
		# Update Status
		self.update_status(widget)

	def enable_nightlight(self, update_status = False, widget = None):
		self.gsettings.set_boolean(self.nightlight_key, True)
		if update_status:
			# Update Status
			self.update_status(widget)

	def disable_nightlight(self):
		self.gsettings.set_boolean(self.nightlight_key, False)

	def restart_nightlight(self, widget):
		# Disable Turn On/Off Menu Item
		self.turnOnOffItem.set_sensitive(False)
		# Disable Widget
		widget.set_sensitive(False)
		# Set Indicator Icon 'Off'
		self.set_icon('nightlight-off.svg')
		# Disable night light
		self.disable_nightlight()
		# Enable night light after 1 second & update status
		GLib.timeout_add_seconds(1, self.enable_nightlight, True, widget)

	def update_status(self, widget = None):
		# Update Nightlight Status
		#old_status = self.status
		self.status = self.get_nightlight_status()
		# Enable Widget
		if widget is not None:
			widget.set_sensitive(True)
		# Set Indicator Icon
		self.set_icon()
		# Change Turn On/Off Menu Item Label & sensitivity
		if self.status == NightlightStatus.On:
			self.turnOnOffItem.set_label('Turn off')
			#self.restartItem.set_sensitive(True)
		else:
			self.turnOnOffItem.set_label('Turn on')
			#self.restartItem.set_sensitive(False)
		self.turnOnOffItem.set_sensitive(True)

	def set_icon(self, icon_name = None):
		if icon_name is None:
			icon_name = 'nightlight-off.svg'
			if self.status == NightlightStatus.On:
				icon_name = 'nightlight-on.svg'
		icon = os.path.dirname(os.path.realpath(__file__)) + '/icons/' + icon_name
		if os.path.exists(icon):
			self.indicator.set_icon(icon)
		else:
			print('ERROR: Cannot find icon %s' % icon)

	def about(self, widget):
		about_dialog = Gtk.AboutDialog()
		about_dialog.set_position(Gtk.WindowPosition.CENTER)
		logo = GdkPixbuf.Pixbuf.new_from_file(os.path.dirname(os.path.realpath(__file__)) + '/icons/nightlight.svg')
		about_dialog.set_logo(logo)
		about_dialog.set_program_name('Nightlight Indicator')
		about_dialog.set_version('1.0')
		about_dialog.set_comments('A night light indicator for Gnome based Linux desktops')
		about_dialog.set_website('https://github.com/AXeL-dev/nightlight-indicator')
		about_dialog.set_website_label('GitHub')
		about_dialog.set_copyright('Copyright © 2020 AXeL-dev')
		about_dialog.set_authors(['AXeL-dev <contact.axel.dev@gmail.com> (Developer)'])
		about_dialog.set_license('''Nightlight Indicator, A night light indicator for Gnome based Linux desktops.
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
	indicator = NightlightIndicator()
	indicator.main()
