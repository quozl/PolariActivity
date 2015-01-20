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

import globals as G
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

    def __init__(self, name):
        Gtk.EventBox.__init__(self)

        channel = name.split('@')[1]
        nickname = channel.split(':')[1]
        channel = channel.split(':')[0]
        channel = ('#' if not channel.startswith('#') else '') + channel

        self.selected = False
        self.name = name
        self.nickname = nickname
        self.hbox = Gtk.HBox()
        self.label = Gtk.Label(channel)
        self.spinner = Gtk.Spinner()

        self.label.modify_font(Pango.FontDescription('15'))
        self.label.set_margin_left(10)
        self.set_size_request(-1, 30)
        self.modify_bg(Gtk.StateType.NORMAL, G.COLOR_WHITE)

        self.connect('button-press-event', self._press)

        self.hbox.pack_start(self.label, False, False, 0)
        self.hbox.pack_end(self.spinner, False, False, 0)
        self.add(self.hbox)

        self.spinner.start()

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
            self.modify_bg(Gtk.StateType.NORMAL, G.COLOR_BLUE)

        else:
            self.modify_bg(Gtk.StateType.NORMAL, G.COLOR_WHITE)

    def stop_spinner(self):
        self.spinner.stop()
        self.hbox.remove(self.spinner)

        button = Gtk.Button.new_from_icon_name(
            Gtk.STOCK_REMOVE, Gtk.IconSize.BUTTON)
        button.connect('clicked', lambda w: self.emit('removed'))
        self.hbox.pack_end(button, False, False, 0)
        self.show_all()


class ChannelsView(Gtk.ScrolledWindow):

    __gsignals__ = {
        'channel-selected': (GObject.SIGNAL_RUN_FIRST, None, [str]),
        'channel-removed': (GObject.SIGNAL_RUN_FIRST, None, [str]),
        }

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)

        self.items = []
        self.sections = {}
        self.vbox = Gtk.VBox()

        self.set_size_request(250, -1)
        self.modify_bg(Gtk.StateType.NORMAL, G.COLOR_WHITE)

        self.add(self.vbox)

    def add_channel(self, host, channel, nickname):
        channel = channel[1:] if channel.startswith('#') else channel
        section = host + '@' + channel
        name = section + ':' + nickname

        if not self.sections.get(section, False):
            self.sections[section] = Gtk.VBox()
            label = Gtk.Label(host)
            label.host = None

            self.sections[section].pack_start(label, False, False, 0)
            self.vbox.pack_start(self.sections[section], False, False, 0)

        item = ChannelItem(name)
        item.host = host
        item.channel = channel

        item.connect('selected', self.select_item)
        item.connect('removed', self.remove_item)
        self.sections[section].pack_start(item, False, False, 0)

        self.items.append(item)
        self.select_item(item)
        self.show_all()

    def remove_item(self, item):
        section = item.name.split(':')[0]
        idx = self.items.index(item)
        self.items.remove(item)
        self.sections[section].remove(item)

        if not self.sections[section].get_children():
            self.vbox.remove(self.sections[section])
            self.sections[section] = None

        self.emit('channel-removed', item.name)
        item.destroy()

        if idx > 0:
            idx -= 1

        if self.items:
            self.select_item(self.items[idx])

    def select_item(self, item):
        for i in self.items:
            i.set_selected(i == item)

        self.emit('channel-selected', item.name)

    def select_item_from_string(self, name):
        for item in self.items:
            if item.name == name:
                self.select_item(item)
                break


class ChatView(Gtk.VBox):

    __gsignals__ = {
        'nickname-changed': (GObject.SIGNAL_RUN_FIRST, None, [str]),
        'stop-widget': (GObject.SIGNAL_RUN_FIRST, None, []),
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

        hbox.set_margin_left(10)
        hbox.set_margin_right(10)

        self.set_entries_theme()
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

        hbox.pack_start(self.nicker, False, False, 1)
        hbox.pack_start(self.entry, True, True, 0)
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

        self.client.start()

    def send_message(self, widget):
        message = widget.get_text()
        self.add_message_to_view(self.user, message, force=True)
        self.client.say(message)
        widget.set_text('')

    def add_text_with_tag(self, text, tag):
        end = self.buffer.get_end_iter()
        self.buffer.insert_with_tags_by_name(end, text, tag)

    def add_system_message(self, client, message):
        if message == self.user + G.NICKNAME_USED:
            if not self.nicker.get_sensitive():
                self.nicker.set_sensitive(True)

            else:
                self.set_user(self.client.last_nickname, False)

        elif message == G.CONNECTION_ERROR:
            self.emit('stop-widget')

        self.last_user = '<SYSTEM>'
        self.add_text_with_tag(message + '\n', 'sys-msg')

    def add_message_to_view(self, user, message, force=False):
        if user != self.user or force:
            if user == self.last_user:
                user = ' ' * (len(user) + 2)

            else:
                self.last_user = user
                user += ': '

            self.add_text_with_tag(user, 'nick')

            end = self.buffer.get_end_iter()
            offset = end.get_offset()

            self.add_text_with_tag(message + '\n', 'message')
            end = self.buffer.get_iter_at_offset(offset)
            if self.last_user != self.user:
                self.search_and_mark(self.user, end, 'self')

            offset = end.get_offset()

            for url in G.get_urls(message):
                end = self.buffer.get_iter_at_offset(offset)
                self.search_and_mark(url, end, 'url')

    def search_and_mark(self, text, start, tag):
        end = self.buffer.get_end_iter()
        match = start.forward_search(text, 0, end)

        if match != None:
            match_start, match_end = match
            self.buffer.apply_tag_by_name(tag, match_start, match_end)
            self.search_and_mark(text, match_end, tag)

    def message_recived(self, client, _dict):
        self.add_message_to_view(_dict['sender'], _dict['message'])

    def set_entries_theme(self):
        theme_entry = "GtkEntry {border-radius:0px 30px 30px 0px;}"
        css_provider_entry = Gtk.CssProvider()
        css_provider_entry.load_from_data(theme_entry)

        style_context = self.entry.get_style_context()
        style_context.add_provider(css_provider_entry,
                                   Gtk.STYLE_PROVIDER_PRIORITY_USER)

        theme_nicker = "GtkEntry {border-radius:30px 0px 0px 30px;}"
        css_provider_nicker = Gtk.CssProvider()
        css_provider_nicker.load_from_data(theme_nicker)

        style_context = self.nicker.get_style_context()
        style_context.add_provider(css_provider_nicker,
                                   Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def create_tags(self):
        self.buffer.create_tag('nick', foreground='#4A90D9')
        self.buffer.create_tag('self', foreground='#FF2020')
        self.buffer.create_tag('message', background='#FFFFFF')
        self.buffer.create_tag('sys-msg', foreground='#AAAAAA')
        self.buffer.create_tag('url', underline=Pango.Underline.SINGLE, foreground='#0000FF')

    def get_entry(self):
        return self.entry


class Field(Gtk.HBox):

    def __init__(self, label, prepopulate):
        Gtk.HBox.__init__(self)

        self.set_size_request(600, -1)

        label = Gtk.Label(label)
        label.modify_fg(Gtk.StateType.NORMAL, style.COLOR_BUTTON_GREY.get_gdk_color())
        label.modify_font(Pango.FontDescription('30'))
        self.pack_start(label, False, False, 50)

        self.entry = Gtk.Entry()
        self.entry.modify_font(Pango.FontDescription('30'))
        self.entry.set_text(str(prepopulate))
        self.pack_end(self.entry, True, True, 0)

        self.show_all()

    def get_value(self):
        return self.entry.get_text()


class AddChannelButton(Gtk.Button):

    def __init__(self, label):
        Gtk.Button.__init__(self, label)

        widget = self.get_children()[0]
        widget.modify_font(Pango.FontDescription('30'))


class AddChannelBox(Gtk.EventBox):

    __gsignals__ = {
        'new-channel': (GObject.SIGNAL_RUN_FIRST, None, [str, str, str, int]),
        'cancel': (GObject.SIGNAL_RUN_FIRST, None, []),
        }

    def __init__(self, nick=None, host=None, channel=None, port=None, init=False):
        Gtk.EventBox.__init__(self)

        box = Gtk.VBox()
        hbox = Gtk.HBox()
        form = Gtk.VBox()
        buttonbox = Gtk.HBox()
        buttonbox.set_spacing(50)

        self.modify_bg(Gtk.StateType.NORMAL,
                       style.COLOR_WHITE.get_gdk_color())

        self.nick = Field('Nick', nick or 'Nickname')
        self.nick.entry.connect('changed', self.__text_changed)
        self.nick.entry.connect('activate', self.__connect_from_widget)
        form.pack_start(self.nick, False, False, 5)

        self.server = Field('Server', host or 'irc.freenode.net')
        self.server.entry.connect('changed', self.__text_changed)
        self.server.entry.connect('activate', self.__connect_from_widget)
        form.pack_start(self.server, False, False, 5)

        self.port = Field('Port', port or '8000')
        self.port.entry.connect('changed', self.__text_changed)
        self.port.entry.connect('activate', self.__connect_from_widget)
        form.pack_start(self.port, False, False, 5)

        self.channels = Field('Channel', channel or '#sugar')
        self.channels.entry.connect('changed', self.__text_changed)
        self.channels.entry.connect('activate', self.__connect_from_widget)
        form.pack_start(self.channels, False, False, 5)

        self.cancel = AddChannelButton('Cancel')
        self.cancel.set_sensitive(not init)
        self.cancel.connect('clicked', self.__cancel)
        buttonbox.add(self.cancel)

        self.enter = AddChannelButton('Connect!')
        self.enter.connect('clicked', self.__connect_from_widget)
        buttonbox.add(self.enter)

        form.pack_start(buttonbox, True, True, 20)
        hbox.pack_start(form, True, False, 0)
        box.pack_start(hbox, True, False, 0)
        self.add(box)
        self.show_all()

    def get_possible(self):
        sensitive = bool(self.nick.get_value()) and \
                    bool(self.server.get_value()) and \
                    bool(self.channels.get_value()) and \
                    bool(self.port.get_value())

        try:
            int(self.port.get_value())

        except ValueError:
            return False

        return sensitive

    def try_connect(self):
        if self.get_possible():
            self.emit('new-channel',
                      self.nick.get_value(),
                      self.server.get_value(),
                      self.channels.get_value(),
                      int(self.port.get_value()))

    def __cancel(self, widget):
        self.emit('cancel')

    def __text_changed(self, *args):
        sensitive = self.get_possible()
        self.enter.set_sensitive(sensitive)

    def __connect_from_widget(self, entry):
        self.try_connect()


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
