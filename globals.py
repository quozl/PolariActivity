import os
from ConfigParser import ConfigParser
from ConfigParser import RawConfigParser

data_file = os.path.join(os.path.dirname(__file__), 'data')

if not os.path.isfile(data_file):
    f = open(data_file, 'w')
    f.write('')
    f.close()


def get_data():
    dic = {}

    config = ConfigParser()
    config.read(data_file)

    for host in config.sections():
        for channel in config.options(host):
            dic[host] = (channel, config.get(host, channel))

    return dic


def set_data(data):
    config = RawConfigParser()
    print 'set data'
    for host, value in data.items():
        print '[%s] %s = %s' % (host, value[0], value[1])
        config.add_section(host)
        config.set(host, value[0], value[1])

    with open(data_file, 'w') as configfile:
        config.write(configfile)

