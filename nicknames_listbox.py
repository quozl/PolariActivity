#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2016, Cristian García <cristian99garcia@gmail.com>
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

from consts import Color, SUGAR

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import GObject


class NicknamesListBox(Gtk.ScrolledWindow):

    __gsignals__ = {
        "query": (GObject.SIGNAL_RUN_FIRST, None, [str]),  # Nickname
    }

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)

        self.nicknames = []
        self.model = Gtk.ListStore(str)
        self.selected_nickname = None

        self.set_size_request(150, 1)

        self.view = Gtk.TreeView()
        self.view.set_model(self.model)
        self.view.set_headers_visible(False)
        self.view.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.view.connect("button-release-event", self._button_release)
        self.add(self.view)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Nickname", renderer, text=0)
        self.view.append_column(column)

        self.menu = Gtk.Menu()

        item = Gtk.MenuItem("Query")
        item.connect("activate", self._query)
        self.menu.append(item)

    def set_list(self, nicknames):
        self.clear()
        nicknames.sort()

        for nick in nicknames:
            self.add_nickname(nick)

    def clear(self):
        while len(self.nicknames) > 0:
            for item in self.nicknames:
                self.nicknames.remove(item)

        self.model.clear()

    def add_nickname(self, nickname):
        self.nicknames.append(nickname)
        self.nicknames = sorted(self.nicknames, key=str.lower)

        self.model.append([nickname])
        #self.model.insert([nickname], self.nicknames.index(nickname))
        self.show_all()

    def remove_nickname(self, nickname):
        self.model.remove(nickname)

    def _button_release(self, widget, event):
        ##selection = self.view.get_selection()
        ##if selection == None:
        ##    return False

        row = self.view.get_dest_row_at_pos(event.x, event.y)
        if row == None or event.button != 3:
            self.selected_nickname = None
            return False

        path = row[0]
        iter = self.model.get_iter(path)
        self.selected_nickname = self.model.get_value(iter, 0)

        self.menu.show_all()
        self.menu.popup(None, None, None, None, event.button, event.time)

    def _query(self, item):
        if self.selected_nickname != None:
            self.emit("query", self.selected_nickname)
