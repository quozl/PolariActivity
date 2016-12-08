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

import globals as G
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import GObject

from sugar3.graphics import style


class Canvas(Gtk.HBox):

    def __init__(self):
        Gtk.HBox.__init__(self)

        self.channels_box = ChannelsView()
        self.chat_box = Gtk.VBox()
        self.chat_view = None

        self.set_originals_boxes()

    def set_chat_view(self, chat_view):
        if self.chat_box.get_children():
            self.chat_box.remove(self.chat_view)

        self.chat_view = chat_view
        self.chat_box.pack_start(self.chat_view, True, True, 0)
        self.show_all()

    def set_canvas(self, canvas):
        for child in self.get_children():
            self.remove(child)

        self.pack_start(canvas, True, True, 0)
        self.show_all()

    def set_originals_boxes(self, *args):
        for child in self.get_children():
            self.remove(child)

        self.pack_start(self.channels_box, False, False, 1)
        self.pack_start(self.chat_box, True, True, 0)

        self.show_all()
