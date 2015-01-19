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

from gi.repository import GObject

import socket
import thread


class Client(GObject.GObject):

    __gsignals__ = {
        'new-user-message': (GObject.SIGNAL_RUN_FIRST, None, [object]),
        'system-message': (GObject.SIGNAL_RUN_FIRST, None, [str]),
        'connected': (GObject.SIGNAL_RUN_FIRST, None, []),
        }

    def __init__(self, data):
        GObject.GObject.__init__(self)

        self.connected = False
        self.active = True
        self.last_nickname = None

        self.socket = socket.socket()
        self.set_data(data)

    def set_data(self, data):
        self.nickname = data['nickname']
        self.channel = data['channel']
        self.port = data['port']
        self.host = data['host']
        self.max_characters = data['max-characters']

        print '\n******** Data setted ********'
        print 'nickname:', self.nickname
        print 'channel:', self.channel
        print 'port:', self.port
        print 'host:', self.host, '\n'

        if not self.channel.startswith('#'):
            self.channel = '#' + self.channel

        try:
            self.socket.connect((self.host, self.port))

        except:
            self.__send_connecting_error()
            print '******** Error to connect to server... ********'

    def set_nickname(self, nickname):
        print '\n******** Setting nickname ********'
        print 'nickname:', nickname, '\n'

        self.last_nickname = self.nickname
        self.nickname = nickname

        try:
            self.send('NICK %s' % self.nickname)
            self.send('USER %(nick)s %(nick)s %(nick)s :%(nick)s' % {'nick': self.nickname})
        except:
            self.__send_connecting_error()

    def start(self):
        print '******** Starting a new thread ********\n'

        try:
            thread.start_new_thread(self.__start, ())

        except:
            self.emit('system-message', G.LOST_CONNECTION)
            self.close()

    def check_sys_msg(self, *args):
        if self.system_messages:
            for x in self.system_messages:
                self.emit('system-message', x)

        self.system_messages = []

    def __start(self, *args):
        print '******** Starting to receive data ********'

        self.set_nickname(self.nickname)

        self.system_messages = []
        GObject.timeout_add_seconds(1, self.check_sys_msg, ())

        while self.active:
            buf = self.socket.recv(self.max_characters)
            lines = buf.split('\n')
            for data in lines:
                data = str(data).strip()

                if data == '':
                    continue

                if data.find('PING') != -1:
                    n = data.split(':')[1]
                    self.send('PONG :' + n)
                    if self.connected == False:
                        self.perform()
                        self.connected = True

                print 'Data received:   ', data

                if len(data.split(' ')) >= 4 and 'PRIVMSG' in data.split(' '):
                    args = data.split(' ')
                    if args[0].startswith(':') and '!':
                        system_message = False
                        message_started = False
                        message = ''
                        # A message of a user

                        name = args[0][1:].split('!')[0]
                        _type = args[1]
                        channel = args[2]
                        #message = data.split(':')[-1]

                        for x in data[1:]:
                            if message_started:
                                message += x

                            if x == ':':
                                message_started = True

                        _dict = {'sender': name,
                                 'type': _type,
                                 'channel': channel,
                                 'message': message}

                        self.emit('new-user-message', _dict)

                    else:
                        system_message = True

                else:
                    system_message = True

                if system_message:
                    message = ''
                    channel = ''

                    if not data.startswith(':'):
                        continue

                    if len(data.split(' ')) == 3 and 'JOIN' in data.split(' '):
                        # Any joined to the channel
                        sender = data[1:].split('!')[0]
                        channel = data.split(' ')[-1]
                        message = sender + _(' joined to ') + channel

                    if len(data.split(' ')) == 9 and ':Nickname is already in use.' in data and self.nickname in data:
                        # New nickname in use
                        message = self.nickname + _(' is already in use.')
                        self.nickname = self.last_nickname

                    if len(data.split(' ')) == 3 and 'NICK' in data.split(' '):
                        # Any has changed nick
                        last_nick = data[1:].split('!')[0]
                        new_nick = data.split(' ')[-1][1:]
                        message = last_nick + _(' has changed nick to ') + new_nick

                    if len(data.split(' ')) >= 4 and 'QUIT' in data.split(' '):
                        nick = data[1:].split('!')[0]
                        message = nick + _(' has withdrawn from the canal.')

                    if message:
                        if message == self.nickname + _(' joined to ') + channel:
                            self.emit('connected')

                        print '******** %s ********\n' % message
                        self.emit('system-message', message)

    def send(self, msg):
        # Any message
        self.socket.send(msg + '\r\n')

    def say(self, msg):
        # Speak with others members of the channel
        self.send('PRIVMSG %s :%s' % (self.channel, msg))

    def perform(self):
        print '******** Establishing contact with the server ********\n'
        self.send('PRIVMSG R : Login <>')
        self.send('MODE %s +x' % self.nickname)
        self.send('JOIN %s' % self.channel)

    def __send_connecting_error(self):
        self.emit('system-message', G.CONNECTION_ERROR)

        self.active = False

    def close(self):
        print '******** Closing contact with the server ********\n'
        self.active = False
        self.send('QUIT')
        self.socket.close()
