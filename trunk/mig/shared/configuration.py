#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# configuration - [insert a few words of module description on this line]
# Copyright (C) 2003-2009  The MiG Project lead by Brian Vinter
#
# This file is part of MiG.
#
# MiG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# MiG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# -- END_HEADER ---
#

"""Configuration class"""

import sys
import os
import pwd
import socket
import time
from ConfigParser import ConfigParser

from shared.logger import Logger


def fix_missing(config_file, verbose=True):
    config = ConfigParser()
    config.read([config_file])

    fqdn = socket.getfqdn()
    user = os.environ['USER']
    global_section = {
        'enable_server_dist': False,
        'server_fqdn': fqdn,
        'admin_email': '%s@%s' % (user, fqdn),
        'mrsl_files_dir': '~/mRSL_files/',
        're_files_dir': '~/re_files/',
        're_pending_dir': '~/re_pending/',
        're_home': '~/re_home/',
        'grid_stdin': '~/mig/server/server.stdin',
        'im_notify_stdin': '~/mig/server/notify.stdin',
        'gridstat_files_dir': '~/gridstat_files/',
        'mig_server_home': '~/mig/server/',
        'resource_home': '~/resource_home/',
        'resource_pending': '~/resource_pending/',
        'user_pending': '~/user_pending/',
        'vgrid_home': '~/vgrid_home/',
        'vgrid_files_home': '~/vgrid_files_home/',
        'vgrid_public_base': '~/vgrid_public_base/',
        'vgrid_private_base': '~/vgrid_private_base/',
        'user_home': '~/mig/wwwuser/',
        'server_home': '~/mig/wwwserver/',
        'webserver_home': '~/webserver_home/',
        'sessid_to_mrsl_link_home': '~/sessid_to_mrsl_link_home/',
        'mig_system_files': '~/mig_system_files/',
        'wwwpublic': '~/mig/wwwpublic/',
        'server_cert': '~/certs/cert.pem',
        'server_key': '~/certs/key.pem',
        'ca_cert': '~/certs/ca.pem',
        'sss_home': '~/sss_home/',
        'sandbox_home': '~/sandbox_home',
        'public_key_file': '',
        'javabin_home': '~/mig/java-bin',
        'migserver_https_url': 'https://%%(server_fqdn)s',
        'myfiles_py_location': 'https://%%(server_fqdn)s/cgi-bin/ls.py',
        'mig_server_id': '%s.0' % fqdn,
        'empty_job_name': 'no_suitable_job-',
        'smtp_server': fqdn,
        'logfile': 'server.log',
        'loglevel': 'info',
        'sleep_period_for_empty_jobs': '80',
        'cputime_for_empty_jobs': '120',
        'min_seconds_between_live_update_requests': '120',
        'architectures': 'X86 AMD64 IA64 SPARC SPARC64 ITANIUM SUN4U SPARC-T1',
        'scriptlanguages': 'sh python java',
        'jobtypes': 'batch interactive bulk all',
        }
    scheduler_section = {'algorithm': 'FairFit',
                         'expire_after': '99999999999',
                         'job_retries': '4'}
    monitor_section = {'sleep_secs': '60',
                       'sleep_update_totals': '600',
                       'slackperiod': '600'}
    settings_section = {'language': 'English'}

    defaults = {
        'GLOBAL': global_section,
        'SCHEDULER': scheduler_section,
        'MONITOR': monitor_section,
        'SETTINGS': settings_section,
        }
    for section in defaults.keys():
        if not section in config.sections():
            config.add_section(section)

    modified = False
    for (section, settings) in defaults.items():
        for (option, value) in settings.items():
            if not config.has_option(section, option):
                if verbose:
                    print 'setting %s->%s to %s' % (section, option,
                            value)
                config.set(section, option, value)
                modified = True
    if modified:
        backup_path = '%s.%d' % (config_file, time.time())
        print 'Backing up existing configuration to %s as update removes all comments'\
             % backup_path
        fd = open(config_file, 'r')
        backup_fd = open(backup_path, 'w')
        backup_fd.writelines(fd.readlines())
        backup_fd.close()
        fd.close()
        fd = open(config_file, 'w')
        config.write(fd)
        fd.close()


class Configuration:

    mig_server_id = None
    mrsl_files_dir = ''
    RE_files_dir = ''
    RE_pending_dir = ''
    re_home = ''
    grid_stdin = ''
    im_notify_stdin = ''
    gridstat_files_dir = ''
    mig_server_home = ''
    server_fqdn = ''
    admin_email = ''
    resource_home = ''
    vgrid_home = ''
    vgrid_public_base = ''
    vgrid_private_base = ''
    vgrid_files_home = ''
    resource_pending = ''
    user_pending = ''
    webserver_home = ''
    user_home = ''
    sss_home = ''
    sandbox_home = ''
    javabin_home = ''
    smtp_server = ''
    server_home = ''
    sessid_to_mrsl_link_home = ''
    mig_system_files = ''
    empty_job_name = ''
    migserver_https_url = ''
    sleep_period_for_empty_jobs = ''
    min_seconds_between_live_update_requests = 0
    cputime_for_empty_jobs = 0
    myfiles_py_location = ''
    public_key_file = ''
    wwwpublic = ''
    enable_server_dist = False
    sleep_secs = 0
    sleep_update_totals = 0
    slackperiod = 0
    architectures = []
    scriptlanguages = []
    jobtypes = []
    server_cert = ''
    server_key = ''
    passphrase_file = ''
    ca_file = ''
    ca_dir = ''
    sched_alg = 'FirstFit'
    expire_after = 86400
    job_retries = 10
    logfile = ''
    loglevel = ''
    logger_obj = None
    logger = None
    peers = None

    # Max number of jobs to migrate in each migration batch

    migrate_limit = 3

    # seconds before peer data expires

    expire_peer = 600
    language = ['English']

    # constructor

    def __init__(self, config_file, verbose=True):
        self.reload_config(config_file, verbose)

    def reload_config(self, config_file, verbose):
        """Re-read and parse configuration file"""

        try:
            self.logger.info('reloading configuration and reopening log'
                             )
        except:
            pass

        if not os.path.isfile(config_file):
            print 'Could not find your configuration file (', \
                config_file, ').'
            print 'Are you missing a symlink from server/MiGserver.conf pointing to server/MiGserver-{server}.conf?'
            raise IOError

        config = ConfigParser()
        config.read([config_file])

        # print "expanding config paths"

        # Expand all paths once and for all to allow '~' in config paths
        # NB! expanduser does not properly honor seteuid - must force it to

        os.environ['HOME'] = pwd.getpwuid(os.geteuid())[5]

        for (key, val) in config.items('GLOBAL'):
            expanded_val = os.path.expanduser(val)
            config.set('GLOBAL', key, expanded_val)

        try:
            self.logfile = config.get('GLOBAL', 'logfile')
            self.loglevel = config.get('GLOBAL', 'loglevel')
        except:

            # Fall back to file in current dir

            self.logfile = 'MiGserver.log'
            self.loglevel = 'info'

        if verbose:
            print 'logging to:', self.logfile, '; level:', self.loglevel

        # reopen or initialize logger

        if self.logger_obj:

            # hangup reopens log file

            self.logger_obj.hangup()
        else:
            self.logger_obj = Logger(self.logfile, self.loglevel)

        logger = self.logger_obj.logger
        self.logger = logger

        # print "logger initialized (level " + logger_obj.loglevel() + ")"
        # logger.debug("logger initialized")

        try:
            self.mig_server_id = config.get('GLOBAL', 'mig_server_id')
            self.mrsl_files_dir = config.get('GLOBAL', 'mRSL_files_dir')
            self.RE_files_dir = config.get('GLOBAL', 'RE_files_dir')
            self.RE_pending_dir = config.get('GLOBAL', 'RE_pending_dir')
            self.re_home = config.get('GLOBAL', 're_home')
            self.grid_stdin = config.get('GLOBAL', 'grid_stdin')
            self.im_notify_stdin = config.get('GLOBAL',
                    'im_notify_stdin')
            self.gridstat_files_dir = config.get('GLOBAL',
                    'gridstat_files_dir')
            self.mig_server_home = config.get('GLOBAL',
                    'mig_server_home')

            # logger.info("grid_stdin = " + self.grid_stdin)

            self.server_fqdn = config.get('GLOBAL', 'server_fqdn')
            self.admin_email = config.get('GLOBAL', 'admin_email')
            self.resource_home = config.get('GLOBAL', 'resource_home')
            self.vgrid_home = config.get('GLOBAL', 'vgrid_home')
            self.vgrid_private_base = config.get('GLOBAL',
                    'vgrid_private_base')
            self.vgrid_public_base = config.get('GLOBAL',
                    'vgrid_public_base')
            self.vgrid_files_home = config.get('GLOBAL',
                    'vgrid_files_home')
            self.resource_pending = config.get('GLOBAL',
                    'resource_pending')
            self.user_pending = config.get('GLOBAL', 'user_pending')
            self.webserver_home = config.get('GLOBAL', 'webserver_home')
            self.user_home = config.get('GLOBAL', 'user_home')
            self.server_home = config.get('GLOBAL', 'server_home')
            self.sss_home = config.get('GLOBAL', 'sss_home')
            self.sandbox_home = config.get('GLOBAL', 'sandbox_home')
            self.javabin_home = config.get('GLOBAL', 'javabin_home')
            self.smtp_server = config.get('GLOBAL', 'smtp_server')
            self.wwwpublic = config.get('GLOBAL', 'wwwpublic')
            self.architectures = config.get('GLOBAL', 'architectures'
                    ).split(' ')
            self.scriptlanguages = config.get('GLOBAL',
                    'scriptlanguages').split(' ')
            self.jobtypes = config.get('GLOBAL', 'jobtypes').split(' ')
            self.sessid_to_mrsl_link_home = config.get('GLOBAL',
                    'sessid_to_mrsl_link_home')
            self.mig_system_files = config.get('GLOBAL',
                    'mig_system_files')
            self.empty_job_name = config.get('GLOBAL', 'empty_job_name')
            self.migserver_https_url = config.get('GLOBAL',
                    'migserver_https_url')
            self.sleep_period_for_empty_jobs = config.get('GLOBAL',
                    'sleep_period_for_empty_jobs')
            self.min_seconds_between_live_update_requests = \
                config.get('GLOBAL',
                           'min_seconds_between_live_update_requests')
            self.cputime_for_empty_jobs = config.get('GLOBAL',
                    'cputime_for_empty_jobs')
            self.myfiles_py_location = config.get('GLOBAL',
                    'myfiles_py_location')
            self.sleep_secs = config.get('MONITOR', 'sleep_secs')
            self.sleep_update_totals = config.get('MONITOR',
                    'sleep_update_totals')
            self.slackperiod = config.get('MONITOR', 'slackperiod')
            self.language = config.get('SETTINGS', 'language').split(' '
                    )
        except Exception, err:

            # logger.info("done reading settings from config")

            try:
                self.logger.error('Error in reloading configuration: %s'
                                   % err)
            except:
                pass
            raise Exception('Failed to parse configuration: %s' % err)

        if config.has_option('GLOBAL', 'public_key_file'):
            self.public_key_file = config.get('GLOBAL',
                    'public_key_file')

        logger.debug('starting scheduler options')
        if config.has_option('SCHEDULER', 'algorithm'):
            self.sched_alg = config.get('SCHEDULER', 'algorithm')
        else:
            self.sched_alg = 'FirstFit'
        if config.has_option('SCHEDULER', 'expire_after'):
            self.expire_after = config.getint('SCHEDULER',
                    'expire_after')

        if config.has_option('SCHEDULER', 'job_retries'):
            self.job_retries = config.getint('SCHEDULER', 'job_retries')

        # set test modes if requested

        if config.has_option('GLOBAL', 'enable_server_dist'):
            try:
                self.enable_server_dist = config.getboolean('GLOBAL',
                        'enable_server_dist')
            except:
                logger.error('enable_server_dist: expected True or False!'
                             )
                pass

        # Only parse server dist options if actually enabled

        if self.enable_server_dist:
            logger.info('enabling server distribution')

            if config.has_option('GLOBAL', 'peerfile'):
                peerfile = config.get('GLOBAL', 'peerfile')
                self.peers = self.ParsePeers(peerfile)

            if config.has_option('GLOBAL', 'migrate_limit'):
                self.migrate_limit = config.get('GLOBAL',
                        'migrate_limit')

            if config.has_option('GLOBAL', 'expire_peer'):
                self.expire_peer = config.getint('GLOBAL', 'expire_peer'
                        )

            # configure certs and keys

            if config.has_option('GLOBAL', 'server_cert'):
                self.server_cert = config.get('GLOBAL', 'server_cert')
            if config.has_option('GLOBAL', 'server_key'):
                self.server_key = config.get('GLOBAL', 'server_key')
            if config.has_option('GLOBAL', 'passphrase_file'):
                self.passphrase_file = config.get('GLOBAL',
                        'passphrase_file')
            ca_path = ''
            if config.has_option('GLOBAL', 'ca_path'):
                ca_path = config.get('GLOBAL', 'ca_path')
                if os.path.isdir(ca_path):
                    self.ca_dir = ca_path
                elif os.path.isfile(ca_path):
                    self.ca_file = ca_path
                else:
                    logger.error('ca_path is neither a file or directory!'
                                 )

    def parse_peers(self, peerfile):

        # read peer information from peerfile

        logger = self.logger
        peers_dict = {}
        peer_conf = ConfigParser()

        try:
            peer_conf.read([peerfile])
            for section in peer_conf.sections():

                # set up defaults

                peer = {
                    'protocol': 'https',
                    'fqdn': 'no-such-mig-host.net',
                    'port': '443',
                    'migrate_cost': '1.0',
                    'rel_path': 'status',
                    }
                for (key, val) in peer_conf.items(section):
                    peer[key] = val

                    peers_dict[section] = peer
                    logger.debug('Added peer: %s', peer['fqdn'])
        except:

            logger.error('parsing peer conf file: %s', peerfile)

            # Show exception details

            logger.error('%s: %s', sys.exc_type, sys.exc_value)

        logger.info('Added %d peer(s) from %s', len(peers_dict.keys()),
                    peerfile)
        return peers_dict


