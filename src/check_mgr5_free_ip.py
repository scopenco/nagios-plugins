#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Nagios/Icinga plugin for monitoring
free ip in IPmanager 5

example: python check_mgr5_free_ip.py -w 500 -c 300 -u vz

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
    p = OptionParser(description='nagios script for get free '
                                 'ips from IPmanager',
                     prog='check_mgr5_free_ip.py',
                     version='0.1',
                     usage='%prog [-d] -w WARN -c CRIT -u USER')
    p.add_option('-w', '--warning', action='store',
                 help='ip num warning', default=None)
    p.add_option('-c', '--critical', action='store',
                 help='ip num critical', default=None)
    p.add_option('-u', '--user', action='store',
                 help='filter user', default=None)
    p.add_option('-d', '--debug', action='store_true',
                 help='verbose output', default=None)
    options, arguments = p.parse_args()

    defaults = {'warning':15, 'critical':10,
                'user':'vds', 'debug':False}
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

    ip_num = 0
    for line in command('/usr/local/mgr5/sbin/mgrctl -m ipmgr permstat'):
        args = line.strip().split()
        if len(args) < 5:
            continue
        if args[5] == config['user']:
            start_range = int(args[0].split('.')[-1])
            end_range = int(args[2].split('.')[-1])
            ip_num += end_range - start_range

    ip_cur = 0
    for line in command('/usr/local/mgr5/sbin/mgrctl -m ipmgr userstat'):
        args = line.strip().split()
        if len(args) < 3:
            continue
        if args[1].split('=')[1] == config['user']:
            ip_cur = int(args[2].split('=')[1])

    if not ip_cur:
        print 'CRITICAL: user %s has no ip range!' % config['user']
        exit(2)

    ip_diff = ip_num - ip_cur
    warning = int(config['warning'])
    critical = int(config['critical'])

    if ip_diff >= warning:
        print '[OK free ip diff %s > %s]' % (ip_diff, warning)
        exit(0)
    elif ip_diff < warning and ip_diff > critical:
        print '[WARNING free ip diff %s < %s < %s]' % (warning,
                                                       ip_diff, critical)
        exit(1)
    elif ip_diff <= critical:
        print '[CRITICAL free ip diff %s < %s]' % (ip_diff, critical)
        exit(2)


if __name__ == '__main__':
    main()
