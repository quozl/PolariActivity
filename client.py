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

from twisted.internet.error import ReactorAlreadyInstalledError

try:
    from twisted.internet import gtk3reactor
    gtk3reactor.install()
except ReactorAlreadyInstalledError:
    print ("Error doing 'gtk3reactor.install(), may not work properly")

from twisted.words.protocols import irc
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet import ssl

from gi.repository import GObject


class Client(irc.IRCClient, GObject.GObject):

    nickname = "nickname"

    __gsignals__ = {
        "joined": (GObject.SIGNAL_RUN_FIRST, None, [str]),  # Channel
        "system-message": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),  # Channel, Message
        "user-message": (GObject.SIGNAL_RUN_FIRST, None, [str, str, str]),  # Nickname, Channel, Message
        "nickname-changed": (GObject.SIGNAL_RUN_FIRST, None, [str]),  # Nickname
        "user-nickname-changed": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),  # Old nickname, New nickname
        "user-joined": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),  # User, Channel
        "user-left": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),  # User, Channel
        "user-quit": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),  # User, Channel
        "user-kicked": (GObject.SIGNAL_RUN_FIRST, None, [str, str, str, str]),  # User, Channel, Kicker, message
    }

    def start_gobject(self):
        GObject.GObject.__init__(self)

    def signedOn(self):
        for c in self.factory.channels:
            self.join(c)

    def joined(self, channel):
        self.emit("joined", channel)

    def privmsg(self, user, channel, msg):
        self.emit("user-message", user.split("!")[0], channel, msg)

    def nickChanged(self, nickname):
        print "NICKCHANGED", nickname
        self.nickname = nickname
        self.emit("nickname-changed", nickname)

    def irc_NICK(self, prefix, params):
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.emit("user-nickname-changed", old_nick, new_nick)

    def alterCollidedNick(self, nickname):
        return nickname + '^'

    def userJoined(self, user, channel):
        self.emit("user-joined", user, channel)

    def userLeft(self, user, channel):
        self.emit("user-left", user, channel)

    def userQuit(self, user, channel):
        self.emit("user-quit", user, channel)

    def userKicked(self, user, channel, kicker, message):
        self.emit("user-kicked", user, channel, kicker, message)

    def close_channel(self, channel):
        self.leave(channel, "")


class ClientFactory(protocol.ClientFactory, GObject.GObject):

    protocol = Client

    __gsignals__ = {
        "joined": (GObject.SIGNAL_RUN_FIRST, None, [str]),  # Channel
        "system-message": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),  # Channel, Message
        "user-message": (GObject.SIGNAL_RUN_FIRST, None, [str, str, str]),  # User, Channel, Message
        "nickname-changed": (GObject.SIGNAL_RUN_FIRST, None, [str]),  # Nickname
        "user-nickname-changed": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),  # Old nickname, New nickname
        "user-joined": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),  # User, Channel
        "user-left": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),  # User, Channel
        "user-quit": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),  # User, Channel
        "user-kicked": (GObject.SIGNAL_RUN_FIRST, None, [str, str, str, str]),  # User, Channel, Kicker, message
    }

    def __init__(self, channels):
        GObject.GObject.__init__(self)

        self.channels = channels
        self.client = None

    def buildProtocol(self, addr):
        self.client = Client()
        self.client.factory = self
        self.client.start_gobject()

        self.client.connect("joined", self._client_joined)
        self.client.connect("system-message", self._client_system_message)
        self.client.connect("user-message", self._client_user_message)
        self.client.connect("nickname-changed", self._client_nickname_changed)
        self.client.connect("user-nickname-changed", self._client_user_nickname_changed)
        self.client.connect("user-joined", self._client_user_joined)
        self.client.connect("user-left", self._client_left)
        self.client.connect("user-quit", self._client_quit)
        self.client.connect("user-kicked", self._client_kicked)

        return self.client

    def add_channel(self, channel):
        if channel not in self.channels:
            self.channels.append(channel)

            if self.client is not None:
                # TODO: check if client is joined
                self.client.join(channel)

    def remove_channel(self, channel):
        if channel in self.channels:
            self.channels.remove(channel)

            if self.client is not None:
                self.client.close_channel(channel)

    def clientConnectionLost(self, connector, reason):
        self.emit("system-message", "ALLCHANNELS", "Connection lost: %s" % reason)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        self.emit("system-message", "ALLCHANNELS", "Connection failed: %s" % reason)

    def start_connection(self, host, port):
        self.emit("system-message", "ALLCHANNELS", "Connecting to %s:%d" % (host, port))
        reactor.connectTCP(host, port, self)
        reactor.run()

    def _client_joined(self, client, channel):
        self.emit("joined", channel)

    def _client_system_message(self, client, message):
        self.emit("system-message", message)

    def _client_user_message(self, client, nickname, channel, message):
        self.emit("user-message", nickname, channel, message)

    def _client_nickname_changed(self, client, nick):
        # TODO: send "user-nickname-changed" too
        self.emit("nickname-changed", nick)

    def _client_user_nickname_changed(self, client, old_nick, new_nick):
        self.emit("user-nickname-changed", old_nick, new_nick)

    def _client_user_joined(self, client, user, channel):
        self.emit("user-joined", user, channel)

    def _client_left(self, client, user, channel):
        self.emit("user-left", user, channel)

    def _client_quit(self, client, user, channel):
        self.emit("user-quit", user, channel)

    def _client_kicked(self, client, user, channel, kicker, message):
        self.emit("user-kicked", user, channel, kicker, message)
