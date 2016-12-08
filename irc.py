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

import sys
import thread
import socket

from utils import parse_irc
from consts import IRCState

from gi.repository import Gdk
from gi.repository import GObject


def default_nicks():
    return ["Nickname"]


class EventData(GObject.GObject):

    def __init__(self, raw, msg, text):
        self.raw = raw
        self.msg = msg
        self.text = text
        self.source = None
        self.address = None

    def get_data(self):
        return {
            "raw": self.raw,
            "msg": self.msg,
            "text": self.text,
            "source": self.source,
            "address": self.address
        }.values()

    def set_data(self, raw, msg, text):
        self.raw = raw
        self.msg = msg
        self.text = text


class Source(object):
    __slots__ = ['enabled']
    def __init__(self):
        self.enabled = True
    def unregister(self):
        self.enabled = False

class GtkSource(object):
    __slots__ = ['tag']
    def __init__(self, tag):
        self.tag = tag
    def unregister(self):
        GObject.source_remove(self.tag)


def register_idle(f, *args, **kwargs):
    priority = kwargs.pop("priority",200)
    def callback():
        Gdk.threads_enter()
        try:
            return f(*args, **kwargs)
        finally:
            Gdk.threads_leave()

    return GtkSource(GObject.idle_add(callback, priority=priority))


def fork(cb, f, *args, **kwargs):
    is_stopped = Source()
    def thread_func():
        try:
            result, error = f(*args, **kwargs), None
        except Exception, e:
            result, error = None, e
            
        if is_stopped.enabled:
            def callback():           
                if is_stopped.enabled:
                    cb(result, error)

            register_idle(callback)

    thread.start_new_thread(thread_func, ())
    return is_stopped




class Network(GObject.GObject):

    __gsignals__ = {
        "socket-connect": (GObject.SIGNAL_RUN_FIRST, None, []),
        "own-raw": (GObject.SIGNAL_RUN_FIRST, None, [str]),
        ###"raw": (GObject.SIGNAL_RUN_FIRST, None, [list]),
        "connecting": (GObject.SIGNAL_RUN_FIRST, None, []),
        "disconnect": (GObject.SIGNAL_RUN_FIRST, None, [str]),
        "nick": (GObject.SIGNAL_RUN_FIRST, None, [str, str]),
        "own-text": (GObject.SIGNAL_RUN_FIRST, None, [str, str, str]),
        "own-notice": (GObject.SIGNAL_RUN_FIRST, None, [str, str, str]),
        "text": (GObject.SIGNAL_RUN_FIRST, None, [str]),
        "unregister": (GObject.SIGNAL_RUN_FIRST, None, []),
    }

    def __init__(self, server, port, channel, nicks):
        GObject.GObject.__init__(self)

        self.socket = None
        self.server = server
        self.port = port
        self.channel = channel

        self.nicks = nicks or default_nicks()
        self.me = self.nicks[0]
        
        self.isupport = {
            'NETWORK': server, 
            'PREFIX': '(ohv)@%+',
            'CHANMODES': 'b,k,l,imnpstr',
        }

        self.prefixes = { 'o': '@', 'h': '%', 'v': '+',
                          '@': 'o', '%': 'h', '+': 'v' }

        self.state = IRCState.DISCONNECTED
        self.failedhosts = [] #hosts we've tried and failed to connect to
        self.channel_prefixes = '&#+$'   # from rfc2812

        self.requested_joins = set()
        self.requested_parts = set()
        
        self.buffer = ''
    
    #called when we get a result from the dns lookup
    def on_dns(self, result, error):
        if error:
            self._disconnect(error=error[1])
        else:
            if socket.has_ipv6: #prefer ipv6
                result = [(f, t, p, c, a) for (f, t, p, c, a) in result if f == socket.AF_INET6] + result

            elif hasattr(socket,"AF_INET6"): #ignore ipv6
                result = [(f, t, p, c, a) for (f, t, p, c, a) in result if f != socket.AF_INET6]
            
            self.failedlasthost = False
            
            for f, t, p, c, a in result:
                if (f, t, p, c, a) not in self.failedhosts:
                    try:
                        self.socket = socket.socket(f, t, p)
                    except:
                        continue

                    self.source = fork(self.on_connect, self.socket.connect, a)
                    self.failedhosts.append((f, t, p, c, a))
                    if set(self.failedhosts) >= set(result):
                        self.failedlasthost = True
                    break
            else:
                self.failedlasthost = True
                if len(result):
                    self.failedhosts[:] = (f, t, p, c, a),
                    f, t, p, c, a = result[0]
                    try:
                        self.socket = socket.socket(f, t, p)
                        self.source = fork(self.on_connect, self.socket.connect, a)
                    except:
                        self._disconnect(error="Couldn't find a host we can connect to")
                else:
                    self._disconnect(error="Couldn't find a host we can connect to")
    
    #called when socket.open() returns
    def on_connect(self, result, error):
        if error:
            self._disconnect(error=error[1])
            #we should immediately retry if we failed to open the socket and there are hosts left
            if self.state == IRCState.DISCONNECTED and not self.failedlasthost:
                self.emit("text", "* Retrying with next available host")
                self._connect()

        else:
            self.source = source = Source()
            self.state = IRCState.INITIALIZING
            self.failedhosts[:] = ()
            
            self.emit("socket-connect")
            
            if source.enabled:
                self.source = fork(self.on_read, self.socket.recv, 8192)
        
    #called when we read data or failed to read data
    def on_read(self, result, error):
        if error:
            self._disconnect(error=error[1])
        elif not result:
            self._disconnect(error="Connection closed by remote host")
        else:
            self.source = source = Source()
            
            self.buffer = (self.buffer + result).split("\r\n")
            
            for line in self.buffer[:-1]:
                self.got_msg(line)
            
            if self.buffer:
                self.buffer = self.buffer[-1]
            else:
                self.buffer = ''
            
            if source.enabled:
                self.source = fork(self.on_read, self.socket.recv, 8192)    
    
    def raw(self, msg):
        self.emit("own-raw", msg)
        
        if self.state >= IRCState.INITIALIZING:
            self.socket.send(msg + "\r\n")
        
    def got_msg(self, msg):
        pmsg = parse_irc(msg, self.server)
    
        e_data = EventData(msg, pmsg, pmsg[-1])

        if "!" in pmsg[0]:
            e_data.source, e_data.address = pmsg[0].split('!',1)            

        else:
            e_data.source, e_data.address = pmsg[0], ''
        
        if len(pmsg) > 2:
            e_data.target = pmsg[2]

        else:
            e_data.target = pmsg[-1]
        
        ###self.emit("raw", e_data.get_data())
    
    def _connect(self):
        if not self.state:
            self.state = IRCState.CONNECTING
            
            self.source = fork(self.on_dns, socket.getaddrinfo, self.server, self.port, 0, socket.SOCK_STREAM)
            self.emit("connecting")
    
    def _disconnect(self, error=None):
        if self.socket:
            self.socket.close()
        
        if self.source:
            self.emit("unregister")
            self.source = None
        
        self.socket = None
        
        self.state = IRCState.DISCONNECTED
        
        #note: connecting from onDisconnect is probably a Bad Thing
        self.emit("disconnect", error)
        
        #trigger a nick change if the nick we want is different from the one we
        # had.
        if self.me != self.nicks[0]:
            self.emit("nick", self.me, self.nicks[0])
            self.me = self.nicks[0]
        
    def norm_case(self, string):
        return string.lower()
    
    def quit(self, msg=None):
        if self.state:
            if msg == None:
                msg = "Bye bye"

            self.raw("QUIT :%s" % msg)

        self._disconnect()
        
    def join(self, target, requested=True):
        self.raw("JOIN %s" % target)

        def _b():
            self.raw("/join " + target)
            return False

        def _a():
            self.raw("/nick " + self.nicks[0])
            GObject.timeout_add(1000, _b)
            return False

        GObject.timeout_add(1000, _a)

    def part(self, target, msg="", requested=True):
        if msg:
            msg = " :" + msg

        self.raw("PART %s%s" % (target, msg))
        if requested:
            for chan in target.split(' ',1)[0].split(','):
                self.requested_parts.add(self.norm_case(target))

    def msg(self, target, msg):
        self.raw("PRIVMSG %s :%s" % (target, msg))
        self.emit("own-text", self.me, str(target), msg)

    def notice(self, target, msg):
        self.raw("NOTICE %s :%s" % (target, msg))
        self.emit("own-notice", self.me, str(target), msg)
