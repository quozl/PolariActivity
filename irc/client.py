from gi.repository import GObject

import socket
import thread


class Client(GObject.GObject):

    __gsignals__ = {
        'connected': (GObject.SIGNAL_RUN_FIRST, None, [bool]),
        'new-user-message': (GObject.SIGNAL_RUN_FIRST, None, [object]),
        'system-message': (GObject.SIGNAL_RUN_FIRST, None, [object]),
        }

    def __init__(self):
        
        GObject.GObject.__init__(self)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.nickname = 'WitoutNick'
        self.channels = []
        self.host = 'irc.freenode.org'
        self.port = 6667
        self.max_characters = 4096
 
    def set_channels(self, channels):
        self.channels = channels
 
    def add_channel(self, channel):
        self.channels.append(channel)
 
    def remove_channel(self, channel):
        if channel in self.channels:
            self.channels.remove(channel)
 
    def set_nickname(self, nickname):
        self.nickname = nickname

    def set_host(self, host):
        self.host = host

    def set_port(self, port):
        self.port = port

    def set_max_characters(self, max_characters):
        self.max_characters = max_characters

    def login(self):
        self.socket.connect((self.host, self.port))
        self.send('NICK %s\r\n' % self.nickname)
        self.send('USER %(nick)s %(nick)s %(nick)s :%(nick)s' % {'nick':self.nickname})
 
    def start(self):
        thread.start_new_thread(self.__start, ())

    def __start(self):
        while True:
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

                if len(data.split(' ')) >= 4:
                    args = data.split(' ')
                    if args[0].startswith(':') and '!' in args[0] and 'ip' in args[0]:
                        system_message = False
                        # A message of a user

                        name = args[0][1:].split('!')[0]
                        _type = args[1]
                        channel = args[2]
                        message = data.split(':')[-1]

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
                    self.emit('system-message', data)

    def send(self, msg):
        self.socket.send(msg + '\r\n')
 
    def say(self, msg, channel=None):
        if not channel:
            channel = self.channels[0]

        if self.connected:
            self.send('PRIVMSG %s :%s' % (channel, msg))
 
    def perform(self):
        self.send('PRIVMSG R : Login <>')
        self.send('MODE %s +x' % self.nickname)
        for c in self.channels:
            self.send('JOIN %s' % c)
        
        self.connected = True
        self.emit('connected', True)
 