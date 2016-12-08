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

from twisted.internet import reactor

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from sugar3.activity import activity
from sugar3.graphics.alert import TimeoutAlert
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import _create_activity_icon as ActivityIcon

from polari_canvas import PolariCanvas


class PolariActivity(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        self.box = Polari()
        self.set_canvas(self.box)

        self.make_toolbar()
        self.show_all()

    def make_toolbar(self):
        def make_separator(expand=False, size=0):
            separator = Gtk.SeparatorToolItem()
            separator.set_size_request(size, -1)
            if expand:
                separator.set_expand(True)

            if expand or size:
                separator.props.draw = False

            return separator

        toolbar_box = ToolbarBox()
        toolbar = toolbar_box.toolbar
        activity_button = ToolButton()
        button_add = ToolButton(Gtk.STOCK_ADD)
        self.entry_nick = Gtk.Entry()
        stop_button = ToolButton('activity-stop')

        activity_button.set_icon_widget(ActivityIcon(None))
        button_add.set_tooltip(_('Add channel'))
        stop_button.connect('clicked', self._exit)
        stop_button.props.accelerator = '<Ctrl>Q'

        ##button_add.connect('clicked', self.add_channel)

        toolbar.insert(activity_button, -1)
        toolbar.insert(make_separator(size=30), -1)
        toolbar.insert(button_add, -1)
        toolbar.insert(make_separator(expand=True), -1)
        toolbar.insert(stop_button, -1)
        self.set_toolbar_box(toolbar_box)

    def _exit(self, *args):
        self.close()
        reactor.stop()
