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

from gettext import gettext as _

import gi
gi.require_version("Gdk", "3.0")

from gi.repository import Gdk


NICKNAME_USED = _(' is already in use.')
LOST_CONNECTION = _('Lost lost conection with the server...')
CONNECTION_ERROR = _('Error to connecting to the server... closing the socket.')
ALERT_TITLE = _('You already have a session on this host with this channel and whit this nickname.')
ALERT_MSG = _('Automatically is selected session you try to create.')


class Screen:
    CHAT = 0
    NEW_CHANNEL = 1


class Color:
    BLUE = Gdk.color_parse('#4A90D9')
    WHITE = Gdk.color_parse('#FFFFFF')
    GREY = Gdk.Color(32896, 32896, 32896)


class IRCState:
    DISCONNECTED = 0
    CONNECTING = 1
    INITIALIZING = 2
    CONNECTED = 3