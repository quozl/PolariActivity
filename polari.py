#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014, Cristian García <cristian99garcia@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
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

import os
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk

from sugar3.activity import activity
from sugar3 import env

from widgets import ChannelsView
from widgets import ChatView

from irc.client import Client


class PolariActivity(Gtk.Window):

    def __init__(self):#, handle):
        Gtk.Window.__init__(self)#, handle)

        self.nick = 'cristian99Bot1'
        self.actual_chanel = '#testbot'

        self.client = Client()
        self._canvas = Gtk.HPaned()
        self._channels_view = ChannelsView()
        self._chat_view = ChatView(self.nick, self.client)
        self._entry = self._chat_view.get_entry()

        self.set_size_request(400, 200)
        self.client.set_nickname(self.nick)
        self.client.set_channels([self.actual_chanel])
        self.client.login()

        self._canvas.pack1(self._channels_view)
        self._canvas.pack2(self._chat_view)

        self.client.connect('connected', self.is_possible_say)
        self._entry.connect('activate', self.say_message)

        #self.set_canvas(self._canvas)
        self.add(self._canvas)
        self.show_all()

        self.start_receiving()

    def is_possible_say(self, client, possible):
        self._entry.set_sensitive(possible)

    def start_receiving(self, *args):
        self.client.start()

    def say_message(self, widget):
        self.client.say(widget.get_text(), self.actual_chanel)


if __name__ == '__main__':
    p = PolariActivity()
    p.connect('destroy', Gtk.main_quit)
    Gtk.main()