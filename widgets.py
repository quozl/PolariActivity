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

import time
import thread

from gi.repository import Gtk
from gi.repository import Pango


class ChannelsView(Gtk.ScrolledWindow):

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)

        self.vbox = Gtk.VBox()
        self.hbox = Gtk.HBox()
        self.view = Gtk.TreeView()

        self.hbox.set_margin_right(5)
        self.hbox.set_margin_left(5)
        self.hbox.set_margin_top(5)
        self.hbox.set_margin_bottom(5)

        self.hbox.pack_start(Gtk.Button.new_from_icon_name(Gtk.STOCK_ADD, Gtk.IconSize.BUTTON), False, False, 0)
        self.hbox.pack_end(Gtk.Button.new_from_icon_name(Gtk.STOCK_APPLY, Gtk.IconSize.BUTTON), False, False, 0)
        self.vbox.pack_start(self.hbox, False, False, 5)
        self.vbox.pack_start(self.view, True, True, 0)
        self.add(self.vbox)


class ChatView(Gtk.VBox):

    def __init__(self, user, client):
        Gtk.VBox.__init__(self)

        self.user = user
        self.client = client
        self.last_user = None

        self.scrolled = Gtk.ScrolledWindow()
        self.chat_area = Gtk.TextView()
        self.buffer = self.chat_area.get_buffer()
        self.entry = Gtk.Entry()

        self.create_tags()
        self.chat_area.set_editable(False)
        self.chat_area.set_cursor_visible(False)
        self.chat_area.modify_font(Pango.FontDescription('Monospace'))
        self.entry.set_sensitive(False)

        self.client.connect('new-user-message', self.message_recived)
        self.client.connect('system-message', self.add_system_message)
        self.entry.connect('activate', self.send_message)

        self.scrolled.add(self.chat_area)
        self.pack_start(self.scrolled, True, True, 10)
        self.pack_end(self.entry, False, False, 0)

    def send_message(self, widget):
        message = widget.get_text()
        self.add_message_to_view(self.user, message, force=True)
        self.client.say(message)
        widget.set_text('')

    def add_system_message(self, client, message):
        def add():
            end_iter = self.buffer.get_end_iter()
            self.buffer.insert(end_iter, message + '\n', -1)

        thread.start_new_thread(add, ())

    def add_message_to_view(self, user, message, force=False):
        if user != self.user or force:
            if user == self.last_user:
                user = ' ' * (len(user) + 10)  # 1 is :

            else:
                self.last_user = user
                user = '[%s:%s]<%s>:' % ('02', '32', user)

            end_iter = self.buffer.get_end_iter()
            self.buffer.insert(end_iter, '\n%s %s' % (user, message), -1)

    def message_recived(self, client, _dict):
        self.add_message_to_view(_dict['sender'], _dict['message'])

    def get_entry(self):
        return self.entry

    def create_tags(self):
        tag_table = self.buffer.get_tag_table()
        tags = {'nick':      ['left-margin', 6],
                'gap':       ['pixels-above-lines', 10],
                'message':   ['indent', 0],
                'highlight': ['weight', Pango.Weight.BOLD],
                'status':    ['left-margin', 6, 'indent', 0, 'justification', Gtk.Justification.RIGHT],
                'timestamp': ['left-margin', 6, 'indent', 0, 'weight', Pango.Weight.BOLD, 'justification', Gtk.Justification.RIGHT],
                'action':    ['left-margin', 6],
                'url':       ['underline', Pango.Underline.SINGLE]}

        for name, sets in tags.iteritems():
            print name, sets
            #for _property, value in sets:
            #    tag = Gtk.TextTag()
            #    tag.set_property(_property, tag)
            #    tag_table.add(tag)
