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

from new_channel_screen import NewChannelScreen
from channels_listbox import ChannelsListBox
from chat_box import ChatBox
from consts import Screen
from client import ClientFactory

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import GObject


class PolariCanvas(Gtk.VBox):

    def __init__(self):
        Gtk.VBox.__init__(self)

        self.screen = None

        self.factory = ClientFactory([])
        self.factory.connect("joined", self._joined)
        self.factory.connect("system-message", self._system_message)
        self.factory.connect("user-message", self._user_message)
        self.factory.connect("nickname-changed", self._nickname_changed)
        self.factory.connect("user-nickname-changed", self._user_nickname_changed)
        self.factory.connect("user-joined", self._user_joined)
        self.factory.connect("user-left", self._user_left)
        self.factory.connect("user-quit", self._user_quit)

        self.channel_screen = NewChannelScreen()
        self.channel_screen.connect("log-in", self._log_in)
        self.channel_screen.connect("new-channel", self._new_channel)
        self.channel_screen.connect("cancel", self._screen_changed, Screen.CHAT)
        self.chat_screen = Gtk.HBox()

        self.channels_listbox = ChannelsListBox()
        self.channels_listbox.connect("channel-selected", self._channel_selected)
        self.channels_listbox.connect("channel-removed", self._channel_removed)
        self.chat_screen.pack_start(self.channels_listbox, False, False, 0)

        self.chat_box = ChatBox()
        self.chat_box.connect("send-message", self._send_message)
        self.chat_box.connect("command", self.run_command)
        self.chat_box.connect("change-nickname", self._change_nickname)
        self.chat_screen.pack_start(self.chat_box, True, True, 0)

        self.set_screen(Screen.NEW_CHANNEL)

    def set_screen(self, screen):
        if screen == self.screen:
            return

        self.screen = screen

        if self.screen == Screen.CHAT:
            if self.channel_screen.get_parent() == self:
                self.remove(self.channel_screen)

            self.pack_start(self.chat_screen, True, True, 0)

        elif self.screen == Screen.NEW_CHANNEL:
            if self.chat_screen.get_parent() == self:
                self.remove(self.chat_screen)

            self.pack_start(self.channel_screen, True, True, 0)

        self.show_all()

    def _send_message(self, widget, channel, message):
        self.send_message(channel, message)

    def send_message(self, channel, message):
        self.factory.client.msg(channel, message)

    def _change_nickname(self, widget, new_nickname):
        self.change_nickname(new_nickname)

    def change_nickname(self, new_nickname):
        self.factory.client.set_nickname(new_nickname)

    def run_command(self, widget, channel, command, parameters=""):
        if command == "/join":
            for channel in parameters.split(" "):
                if channel.strip() != "":
                    self.new_channel(channel)

        elif command == "/msg":
            nickname = parameters.split(" ")[0]
            message = parameters[len(nickname) + 1:]
            self.new_channel(nickname, add_hash=False)
            self.send_message(nickname, message)
            self.chat_box.add_message_to_view(nickname, self.factory.protocol.nickname, message, force=True)

        elif command == "/nick":
            self.change_nickname(parameters)

    def _log_in(self, widget, nick, host, channel, port):
        self.set_screen(Screen.CHAT)
        self.chat_box.set_nickname(nick)
        self.channel_screen.set_logged(True)

        self.factory.protocol.nickname = nick
        self.new_channel(channel)
        self.factory.start_connection(host, port)

    def _new_channel(self, widget, channel):
        self.new_channel(channel)

    def _channel_removed(self, widget, channel):
        self.factory.remove_channel(channel)
        self.chat_box.remove_channel(channel)

        if len(self.factory.channels) == 0:
            self.set_screen(Screen.NEW_CHANNEL)

    def new_channel(self, channel, add_hash=True, show=None):
        self.set_screen(Screen.CHAT)

        if add_hash and not channel.startswith("#"):
            channel = "#" + channel

        self.chat_box.add_channel(channel)
        self.channels_listbox.add_channel(channel, show=show)
        self.factory.add_channel(channel)
        self.chat_box.switch_channel(channel)

    def _channel_selected(self, listbox, channel):
        self.chat_box.switch_channel(channel)

    def _screen_changed(self, widget, screen):
        self.set_screen(screen)

    def _joined(self, factory, channel):
        if channel not in self.chat_box.channels:
            channel = channel[1:]  # Isn't a channel, is a user (removing #)

        else:
            self.chat_box.add_system_message(channel, "Joined to: %s" % channel)

        self.channels_listbox.change_spinner(channel, False)
        self.chat_box.entry.set_sensitive(True)
        self.chat_box.nicker.set_sensitive(True)

    def _system_message(self, factory, channel, message):
        if channel == "ALLCHANNELS":
            for channel in self.chat_box.channels:
                self.chat_box.add_system_message(channel, message)

        else:
            self.chat_box.add_system_message(channel, message)

    def _user_message(self, factory, channel, nickname, message):
        if channel == self.factory.protocol.nickname and nickname not in self.chat_box.channels:
            self.new_channel(nickname, add_hash=False, show=nickname)

        if channel != self.factory.protocol.nickname:
            self.chat_box.message_recived(channel, nickname, message)

        else:
            self.chat_box.message_recived(nickname, nickname, message)

    def _nickname_changed(self, factory, nickname):
        self.chat_box.set_nickname(nickname)

    def _user_nickname_changed(self, factory, old_nick, new_nick):
        # TODO: show message only in connecteds channels
        for channel in self.chat_box.channels:
            self.chat_box.add_system_message(channel, "%s has changed nick to %s" % (old_nick, new_nick))

    def _user_joined(self, factory, channel, nickname):
        self.chat_box.add_system_message(channel, "%s joined." % nickname)

    def _user_left(self, factory, channel, nickname):
        self.chat_box.add_system_message(channel, "%s has left." % nickname)

    def _user_quit(self, factory, nickname, message):
        # TODO: show message only in connecteds channels
        for channel in self.chat_box.channels:
            self.chat_box.add_system_message(channel, "%s has quit. [%s]" % (nickname, message))


if __name__ == "__main__":
    def _quit(win):
        from twisted.internet import reactor
        from twisted.internet.error import ReactorNotRunning

        Gtk.main_quit()

        try:
            reactor.stop()
        except ReactorNotRunning:
            pass

    def _clicked(button, polari):
        polari.set_screen(Screen.NEW_CHANNEL)

    win = Gtk.Window()
    win.set_title("Polari for Sugar")
    win.connect("destroy", _quit)

    polari = PolariCanvas()
    win.add(polari)

    button = Gtk.Button.new_with_label("Add channel")
    button.connect("clicked", _clicked, polari)
    polari.pack_end(button, False, False, 0)

    win.show_all()

    Gtk.main()
