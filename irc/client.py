from gi.repository import GObject

import socket
import thread


class Client(GObject.GObject):

    __gsignals__ = {
        'new-user-message': (GObject.SIGNAL_RUN_FIRST, None, [object]),
        'system-message': (GObject.SIGNAL_RUN_FIRST, None, [object]),
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

        if not self.channel.startswith('#'):
            self.channel = '#' + self.channel

        self.socket.connect((self.host, self.port))

        if not self.connected:
            self.start()

    def set_nickname(self, nickname):
        self.last_nickname = self.nickname
        self.nickname = nickname
        self.send('NICK %s' % self.nickname)
        self.send('USER %(nick)s %(nick)s %(nick)s :%(nick)s' % {
            'nick': self.nickname})

    def start(self):
        thread.start_new_thread(self.__start, ())

    def check_sys_msg(self, *args):
        if self.system_messages:
            for x in self.system_messages:
                self.emit('system-message', x)

        self.system_messages = []

    def __start(self, *args):
        print '\n\n'

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

                print data

                if data.find('PING') != -1:
                    n = data.split(':')[1]
                    self.send('PONG :' + n)

                    if not self.connected:
                        self.perform()
                        self.connected = True

                if len(data.split(' ')) == 4:
                    args = data.split(' ')
                    if args[0].startswith(':') and \
                            '!' in args[0] and 'ip' in args[0]:

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
                    message = ''
                    channel = ''

                    if not data.startswith(':'):
                        continue

                    if len(data.split(' ')) == 3 and 'JOIN' in data.split(' '):
                        # Any joined to the channel
                        sender = data[1:].split('!')[0]
                        channel = data.split(' ')[-1]
                        message = sender + ' joined to ' + channel

                    if len(data.split(' ')) == 9 and \
                            ':Nickname is already in use.' in data and \
                            self.nickname in data:

                        # New nickname in use
                        message = self.nickname + ' is already in use.'
                        self.nickname = self.last_nickname

                    if len(data.split(' ')) == 3 and 'NICK' in data.split(' '):
                        # Any has changed nick
                        last_nick = data[1:].split('!')[0]
                        new_nick = data.split(' ')[-1][1:]
                        message = last_nick + ' has changed nick to '
                        message += new_nick

                    if len(data.split(' ')) >= 4 and 'QUIT' in data.split(' '):
                        nick = data[1:].split('!')[0]
                        message = nick + ' has withdrawn from the canal.'

                    if message:
                        if message == self.nickname + ' joined to ' + channel:
                            self.emit('connected')

                        self.emit('system-message', message)

    def send(self, msg):
        # Any message
        self.socket.send(msg + '\r\n')

    def say(self, msg):
        # Speak with others members of the channel
        self.send('PRIVMSG %s :%s' % (self.channel, msg))

    def perform(self):
        self.send('PRIVMSG R : Login <>')
        self.send('MODE %s +x' % self.nickname)
        self.send('JOIN %s' % self.channel)

    def close(self):
        self.active = False
        self.socket.close()
