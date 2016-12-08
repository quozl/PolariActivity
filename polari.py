#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014, Cristian García <cristian99garcia@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

from gettext import gettext as _

from consts import Screen

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from sugar3.activity import activity
from sugar3.graphics.alert import TimeoutAlert
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton

from polari_canvas import PolariCanvas


class PolariActivity(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        self.polari = PolariCanvas()
        self.set_canvas(self.polari)

        self.make_toolbar()
        self.show_all()

    def make_toolbar(self):
        def make_separator(expand=False):
            separator = Gtk.SeparatorToolItem()
            if expand:
                separator.set_expand(True)
                separator.props.draw = False

            return separator

        toolbar_box = ToolbarBox()
        self.set_toolbar_box(toolbar_box)

        toolbar = toolbar_box.toolbar

        activity_button = ActivityToolbarButton(self)
        toolbar.insert(activity_button, -1)

        toolbar.insert(make_separator(), -1)

        button_add = ToolButton(Gtk.STOCK_ADD)
        button_add.set_tooltip(_("Add a channel"))
        button_add.connect("clicked", self._add_channel)
        toolbar.insert(button_add, -1)

        toolbar.insert(make_separator(True), -1)

        stop_button = ToolButton("activity-stop")
        stop_button.connect("clicked", self._exit)
        stop_button.props.accelerator = "<Ctrl>Q"
        toolbar.insert(stop_button, -1)

    def _exit(self, *args):
        from twisted.internet import reactor
        reactor.stop()
        self.close()

    def _add_channel(self, button):
        self.polari.set_screen(Screen.NEW_CHANNEL)
