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
from gi.repository import Pango
from gi.repository import GObject


class NicknameItem(Gtk.EventBox):

    __gsignals__ = {
        "selected": (GObject.SIGNAL_RUN_FIRST, None, []),
        "query": (GObject.SIGNAL_RUN_FIRST, None, []),
    }

    def __init__(self, nickname):
        Gtk.EventBox.__init__(self)

        self.nickname = nickname
        self.selected = False

        self.connect("button-press-event", self._press)

        self.hbox = Gtk.HBox()
        self.add(self.hbox)

        self.label = Gtk.Label(self.nickname)
        self.label.modify_font(Pango.FontDescription("10"))
        self.hbox.pack_start(self.label, False, False, 0)

        self.menu = Gtk.Menu()

        item = Gtk.MenuItem("Query")
        item.connect("activate", self._query)
        self.menu.append(item)

    def _press(self, widget, event):
        if event.button == 1 or event.button == 3:
            if not self.selected:
                self.emit("selected")
                self.selected = True

        if event.button == 3:
            self.menu.show_all()
            self.menu.popup(None, None, None, None, event.button, event.time)

    def _query(self, item):
        self.emit("query")

    def set_selected(self, is_selected):
        self.selected = is_selected
        self.update()

    def update(self):
        if self.selected:
            self.modify_bg(Gtk.StateType.NORMAL, Color.BLUE)

        else:
            if SUGAR:
                self.modify_bg(Gtk.StateType.NORMAL, Color.WHITE)

            else:
                self.modify_bg(Gtk.StateType.NORMAL, None)


class NicknamesListBox(Gtk.ScrolledWindow):

    __gsignals__ = {
        "query": (GObject.SIGNAL_RUN_FIRST, None, [str]),  # Nickname
    }

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)

        self.items = []

        self.set_size_request(150, 1)

        self.vbox = Gtk.VBox()
        self.add(self.vbox)

    def set_list(self, nicknames):
        self.clear()
        nicknames.sort()

        for nick in nicknames:
            self.add_item(nick)

    def clear(self):
        while len(self.items) > 0:
            for item in self.items:
                self.remove(item)
                self.items.remove(item)

    def add_item(self, nick):
        sorted_list = [item.nickname for item in self.items]
        sorted_list.append(nick)
        sorted_list = sorted(sorted_list, key=str.lower)

        item = NicknameItem(nick)
        item.connect("selected", self.select_item)
        item.connect("query", self._query)
        self.vbox.pack_start(item, False, False, 0)
        self.vbox.reorder_child(item, sorted_list.index(nick))

        self.items.append(item)
        self.show_all()

    def remove_item(self, nick):
        for item in self.items:
            if item.nickname == nick:
                self.vbox.remove(item)
                self.items.remove(item)
                break

    def select_item(self, item):
        for i in self.items:
            i.set_selected(i == item)

    def _query(self, item):
        self.emit("query", item.nickname)
