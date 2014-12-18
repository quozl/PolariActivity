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

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import GObject

from sugar3.graphics import style


class ChannelItem(Gtk.EventBox):

    __gsignals__ = {
        'selected': (GObject.SIGNAL_RUN_FIRST, None, []),
        'removed': (GObject.SIGNAL_RUN_FIRST, None, []),
        }

    def __init__(self, channel):
        Gtk.EventBox.__init__(self)

        channel = ('#' if not channel.startswith('#') else '') + channel

        self.selected = False
        self.hbox = Gtk.HBox()
        self.label = Gtk.Label(channel)
        self.last_widget = Gtk.Spinner()

        self.label.modify_font(Pango.FontDescription('15'))
        self.label.set_margin_left(10)
        self.set_size_request(-1, 30)
        self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))
        self.last_widget.start()

        self.connect('button-press-event', self._press)

        self.hbox.pack_start(self.label, False, False, 0)
        self.hbox.pack_end(self.last_widget, False, False, 0)
        self.add(self.hbox)

    def _press(self, widget, event):
        if event.button == 1:
            if not self.selected:
                self.emit('selected')
                self.selected = True

    def set_selected(self, is_selected):
        self.selected = is_selected
        self.update()

    def get_channel(self):
        return self.label.get_label()

    def update(self):
        if self.selected:
            self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#4A90D9'))

        else:
            self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))

    def stop_last_widget(self):
        self.last_widget.stop()
        self.hbox.remove(self.last_widget)

        button = Gtk.Button.new_from_icon_name(
            Gtk.STOCK_REMOVE, Gtk.IconSize.BUTTON)
        button.connect('clicked', lambda w: self.emit('removed'))
        self.hbox.pack_end(button, False, False, 0)
        self.show_all()


class ChannelsView(Gtk.ScrolledWindow):

    __gsignals__ = {
        'channel-selected': (GObject.SIGNAL_RUN_FIRST, None, [str, str]),
        'channel-removed': (GObject.SIGNAL_RUN_FIRST, None, [str, str]),
        }

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)

        self.items = []
        self.sections = {}
        self.vbox = Gtk.VBox()

        self.set_size_request(250, -1)
        self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))

        self.add(self.vbox)

    def add_channel(self, channel, host):
        if not self.sections.get(host, False):
            self.sections[host] = Gtk.VBox()
            label = Gtk.Label(host)
            label.host = None

            self.sections[host].pack_start(label, False, False, 0)
            self.vbox.pack_start(self.sections[host], False, False, 0)

        item = ChannelItem(channel)
        item.host = host
        item.channel = channel

        item.connect('selected', self.select_item)
        item.connect('removed', self.remove_item)
        self.sections[host].pack_start(item, False, False, 0)

        self.items.append(item)
        self.select_item(item)
        self.show_all()

    def remove_item(self, item):
        host = item.host
        channel = item.channel

        self.items.remove(item)
        self.sections[host].remove(item)

        if not self.sections[host].get_children():
            self.vbox.remove(self.sections[host])
            self.sections[host] = None

        self.emit('channel-removed', host, channel)
        item.destroy()

    def select_item(self, item):
        for i in self.items:
            i.set_selected(i == item)

        self.emit('channel-selected', item.host, item.channel)


class ChatView(Gtk.VBox):

    __gsignals__ = {
        'nickname-changed': (GObject.SIGNAL_RUN_FIRST, None, [str]),
        }

    def __init__(self):
        Gtk.VBox.__init__(self)

        self.user = None
        self.client = None
        self.last_user = None

        self.scrolled = Gtk.ScrolledWindow()
        self.chat_area = Gtk.TextView()
        self.buffer = self.chat_area.get_buffer()
        self.nicker = Gtk.Entry()
        self.entry = Gtk.Entry()
        hbox = Gtk.HBox()

        self.create_tags()
        self.chat_area.set_editable(False)
        self.chat_area.set_cursor_visible(False)
        self.chat_area.set_wrap_mode(Gtk.WrapMode.WORD)
        self.chat_area.modify_font(Pango.FontDescription('Monospace 14'))
        self.nicker.set_size_request(100, -1)
        self.nicker.set_max_length(16)
        self.nicker.set_sensitive(False)
        self.entry.set_sensitive(False)
        self.entry.set_placeholder_text(_('Speak'))
        self.set_size_request(400, -1)

        self.nicker.connect('activate', lambda w: self.set_user(w.get_text()))
        self.entry.connect('activate', self.send_message)

        hbox.pack_start(self.nicker, False, False, 0)
        hbox.pack_end(self.entry, True, True, 0)
        self.scrolled.add(self.chat_area)
        self.pack_start(self.scrolled, True, True, 5)
        self.pack_end(hbox, False, False, 5)

    def set_user(self, user, emit=True):
        if not self.entry.get_sensitive():
            self.nicker.set_sensitive(False)

        if '-' not in user and ' ' not in user:
            self.user = user
            self.nicker.set_placeholder_text(self.user)

            if emit:
                self.emit('nickname-changed', self.user)

        else:
            self.add_system_message(
                self.client, user + _(' is not a valid nickname.'))

        self.nicker.set_text('')

    def set_client(self, client):
        self.client = client
        self.client.connect('new-user-message', self.message_recived)
        self.client.connect('system-message', self.add_system_message)

    def send_message(self, widget):
        message = widget.get_text()
        self.add_message_to_view(self.user, message, force=True)
        self.client.say(message)
        widget.set_text('')

    def add_system_message(self, client, message):
        if message == self.user + _(' is already in use.'):
            if not self.nicker.get_sensitive():
                self.nicker.set_sensitive(True)

            else:
                self.set_user(self.client.last_nickname, False)

        self.last_user = '<SYSTEM>'

        _iter = self.buffer.get_end_iter()
        offset = _iter.get_offset()
        self.buffer.insert(_iter, message + '\n', -1)

        start = self.buffer.get_iter_at_offset(offset)
        self.buffer.apply_tag(self.tag_system_msg, start, _iter)

    def add_message_to_view(self, user, message, force=False):
        if user != self.user or force:
            if user == self.last_user:
                user = ' ' * (len(user) + 2)

            else:
                self.last_user = user
                user += ': '

            _iter = self.buffer.get_end_iter()
            offset = _iter.get_offset()
            self.buffer.insert(_iter, user, -1)

            start = self.buffer.get_iter_at_offset(offset)
            self.buffer.apply_tag(self.tag_nick, start, _iter)

            _iter = self.buffer.get_end_iter()
            offset = _iter.get_offset()
            self.buffer.insert(_iter, ' %s\n' % message, -1)

            start = self.buffer.get_iter_at_offset(offset)
            self.buffer.apply_tag(self.tag_message, start, _iter)

    def message_recived(self, client, _dict):
        self.add_message_to_view(_dict['sender'], _dict['message'])

    def get_entry(self):
        return self.entry

    def create_tags(self):
        self.tag_nick = self.buffer.create_tag('nick', foreground='#4A90D9')
        self.tag_message = self.buffer.create_tag(
            'message', background='#FFFFFF')
        self.tag_system_msg = self.buffer.create_tag(
            'sys-msg', foreground='#AAAAAA')
        self.tag_url = self.buffer.create_tag(
            'url', underline=Pango.Underline.SINGLE)


class Field(Gtk.HBox):

    def __init__(self, label, prepopulate):
        Gtk.HBox.__init__(self)

        lb = Gtk.Label()
        lb.set_markup(
            "<span size='large' foreground='%s'>%s</span>" % (
                style.COLOR_BUTTON_GREY.get_html(),
                label))

        self.pack_start(lb, True, False, 0)

        self.entry = Gtk.Entry()
        self.entry.set_text(prepopulate)
        self.pack_end(self.entry, True, True, 0)
        
        self.show_all()

    def get_value(self):
        return self.entry.get_text()


class AddChannelBox(Gtk.EventBox):

    __gsignals__ = {
        'new-channel': (GObject.SIGNAL_RUN_FIRST, None, [str, str, str, int]),
        'cancel': (GObject.SIGNAL_RUN_FIRST, None, []),
        }

    def __init__(self, nick=None, host=None, port=None, channel=None):
        Gtk.EventBox.__init__(self)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        boxi = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        form = Gtk.VBox()

        self.modify_bg(Gtk.StateType.NORMAL,
                       style.COLOR_WHITE.get_gdk_color())

        self.nick = Field("Nick", "Nickname" or nick)
        form.pack_start(self.nick, False, False, 5)

        self.server = Field("Server", "irc.freenode.net")
        form.pack_start(self.server, False, False, 5)

        self.port = Field("Port", "8000" or port)
        form.pack_start(self.port, False, False, 5)

        self.channels = Field("Channel", "#sugar" or port)
        form.pack_start(self.channels, False, False, 5)

        self.enter = Gtk.Button(label="Connect!")
        self.enter.connect("clicked", self.__connect_clicked)
        form.add(self.enter)

        self.cancel = Gtk.Button(label='Cancel')
        self.cancel.connect('clicked', self.__cancel)
        form.add(self.cancel)

        boxi.pack_start(form, True, False, 0)
        box.pack_start(boxi, True, False, 0)
        self.add(box)
        self.show_all()

    def __cancel(self, widget):
        self.emit('cancel')

    def __text_changed(self, *args):
        sensitive = bool(self.nick.get_text()) and \
                bool(self.server.get_text()) and \
                bool(self.channels.get_text()) and \
                bool(self.port.get_text())

        try:
            int(self.port.get_text())

        except ValueError:
            sensitive = False

        self.enter.set_sensitive(sensitive)

    def __connect_clicked(self, button):
        data = {
            "nick": self.nick.get_value(),
            "server": self.server.get_value(),
            "channels": self.channels.get_value(),
            "port": int(self.port.get_value())
        }
        self.emit("new-channel",
                  data["nick"],
                  data["server"],
                  data["channels"],
                  data["port"])


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

    def set_canvas(self, canvas, expand=True, fill=True, padding=0):
        for child in self.get_children():
            self.remove(child)

        self.pack_start(canvas, expand, fill, padding)
        self.show_all()

    def set_originals_boxes(self, *args):
        for child in self.get_children():
            self.remove(child)

        self.pack_start(self.channels_box, False, False, 1)
        self.pack_start(self.chat_box, True, True, 0)

        self.show_all()



