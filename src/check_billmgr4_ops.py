#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Nagios/Icinga plugin for monitoring
hung operations in BILLmanager 4

examples: 
    ./check_billmgr4_ops.py -n 'Shared hosting' -t 3
    ./check_billmgr4_ops.py -n 'Virtual server' -t 3

Andrey Skopenko <andrey@skopenko.net> @ 2014
'''

from optparse import OptionParser
import logging
from sys import exit
import subprocess as sp


def command(cmd):
    '''run rsync cmd'''

    p = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    st = p.wait()
    logging.debug('command (%s) return %s' % (cmd, st))
    if st > 0:
        logging.error(p.stderr.read().strip())
        print 'CRITICAL: plugin error!'
        exit(2)
    return p.stdout


def main():
    p = OptionParser(description='nagios script to get hung '
                                 'operations in BILLmanager 4',
                     prog='check_billmgr4_ops.py',
                     version='0.1',
                     usage='%prog [-d]')
    p.add_option('-n', '--item', action='store',
                 help='operation type', default=None)
    p.add_option('-t', '--trycount', action='store',
                 help='max try count for operation', default=None)
    p.add_option('-d', '--debug', action='store_true',
                 help='verbose output', default=None)
    options, arguments = p.parse_args()

    defaults = {'item':'Domain names', 'trycount':3, 'debug':False}
    config = {}
    config.update(defaults)
    # options override config
    config.update(dict([(k, v) for k, v in vars(options).items()
                  if v is not None]))

    level = logging.INFO
    debug = config.get('debug')
    if debug:
        level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(message)s', level=level)
    logging.debug('config: %r', config)
    logging.debug('options: %r', vars(options))

    out = ''
    for line in command('/usr/local/ispmgr/sbin/mgrctl -m billmgr rerunoperation'):
        if config['item'] in line:
            args = line.strip().split()
            for arg in args:
                arg_types = arg.split('=')
                if len(arg_types) != 2:
                    continue
                logging.debug(arg_types)
                if arg_types[0] == 'trycount' and int(arg_types[1]) > int(config['trycount']):
                    out += 'item="%s" trycount=%s; ' % (config['item'], arg_types[1])
    if out:
        print 'CRITICAL: %s' % out
        exit(2)

    print 'OK: all operations for itname="%s" are OK' % config['item']


if __name__ == '__main__':
    main()
