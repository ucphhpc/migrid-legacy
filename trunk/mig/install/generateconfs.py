#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# generateconfs - create custom MiG server configuration files
# Copyright (C) 2003-2018  The MiG Project lead by Brian Vinter
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

"""Generate the configurations for a custom MiG server installation.
Creates MiG server and Apache configurations to fit the provided settings.
"""

import datetime
import getopt
import sys

from shared.install import generate_confs


def usage(options):
    """Usage help"""
    lines = ["--%s=%s" % pair for pair in zip(options,
                                              [i.upper() for i in options])]
    print '''Usage:
%s [OPTIONS]
Where supported options include -h/--help for this help or the conf settings:
%s
''' % (sys.argv[0], '\n'.join(lines))


if '__main__' == __name__:
    names = (
        'source',
        'destination',
        'destination_suffix',
        'base_fqdn',
        'public_fqdn',
        'mig_cert_fqdn',
        'ext_cert_fqdn',
        'mig_oid_fqdn',
        'ext_oid_fqdn',
        'sid_fqdn',
        'io_fqdn',
        'jupyter_hosts',
        'jupyter_base_url',
        'user',
        'group',
        'apache_version',
        'apache_etc',
        'apache_run',
        'apache_lock',
        'apache_log',
        'openssh_version',
        'mig_code',
        'mig_state',
        'mig_certs',
        'enable_sftp',
        'enable_sftp_subsys',
        'enable_davs',
        'enable_ftps',
        'enable_wsgi',
        'wsgi_procs',
        'enable_jobs',
        'enable_events',
        'enable_sharelinks',
        'enable_transfers',
        'enable_freeze',
        'enable_sandboxes',
        'enable_vmachines',
        'enable_preview',
        'enable_jupyter',
        'enable_gdp',
        'enable_hsts',
        'enable_vhost_certs',
        'enable_verify_certs',
        'enable_seafile',
        'enable_duplicati',
        'enable_crontab',
        'enable_imnotify',
        'enable_dev_accounts',
        'enable_twofactor',
        'enable_openid',
        'mig_oid_provider',
        'ext_oid_provider',
        'daemon_keycert',
        'daemon_pubkey',
        'daemon_show_address',
        'alias_field',
        'signup_methods',
        'login_methods',
        'hg_path',
        'hgweb_scripts',
        'trac_admin_path',
        'trac_ini_path',
        'public_port',
        'mig_cert_port',
        'ext_cert_port',
        'mig_oid_port',
        'ext_oid_port',
        'sid_port',
        'user_clause',
        'group_clause',
        'listen_clause',
        'serveralias_clause',
        'distro',
        'landing_page',
        'skin',
    )
    settings = {}
    for key in names:
        settings[key] = 'DEFAULT'

    flag_str = 'h'
    opts_str = ["%s=" % key for key in names] + ["help"]
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], flag_str, opts_str)
    except getopt.GetoptError, exc:
        print 'Error: ', exc.msg
        usage(names)
        sys.exit(1)

    for (opt, val) in opts:
        opt_name = opt.lstrip('-')
        if opt in ('-h', '--help'):
            usage(names)
            sys.exit(0)
        elif opt_name in names:
            settings[opt_name] = val
        else:
            print 'Error: %s not supported!' % opt
            usage(names)
            sys.exit(1)

    if args:
        print 'Error: non-option arguments are no longer supported!'
        usage(names)
        sys.exit(1)
    if settings['destination_suffix'] == 'DEFAULT':
        suffix = "-%s" % datetime.datetime.now().isoformat()
        settings['destination_suffix'] = suffix
    print '# Creating confs with:'
    for (key, val) in settings.items():
        print '%s: %s' % (key, val)
        # Remove default values to use generate_confs default values
        if val == 'DEFAULT':
            del settings[key]
    conf = generate_confs(**settings)
    #print "DEBUG: %s" % conf
    instructions_path = "%(destination)s/instructions.txt" % conf
    try:
        instructions_fd = open(instructions_path, "r")
        instructions = instructions_fd.read()
        instructions_fd.close()
        print instructions
    except Exception, exc:
        print "ERROR: could not read generated instructions: %s" % exc
        sys.exit(1)
    sys.exit(0)
