#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# --- BEGIN_HEADER ---
#
#
# fixuserdbkeys - update any old NAME:ORG:ST:C:EMAIL keys to DN form in user DB
# Copyright (C) 2003-2017  The MiG Project lead by Brian Vinter
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
#
# --- END_HEADER ---
#

"""Fix any leftover old style user IDs in user database by inserting them with
their (correct) distinguished_name field as their key instead of the old broken
key.
"""

import sys
import getopt

from shared.useradm import init_user_adm, fix_userdb_keys

def usage(name='fixuserdb.py'):
    """Usage help"""

    print """Update user database to replace any leftover old keys to the
    current distinguished_name form.

Usage:
%(name)s [OPTIONS]
Where OPTIONS may be one or more of:
   -c CONF_FILE        Use CONF_FILE as server configuration
   -d DB_FILE          Use DB_FILE as user data base file
   -f                  Force operations to continue past errors
   -h                  Show this help
   -v                  Verbose output
"""\
         % {'name': name}

if '__main__' == __name__:
    (args, app_dir, db_path) = init_user_adm()
    conf_path = None
    force = False
    verbose = False
    opt_args = 'c:d:fhv'
    try:
        (opts, args) = getopt.getopt(args, opt_args)
    except getopt.GetoptError, err:
        print 'Error: ', err.msg
        usage()
        sys.exit(1)

    for (opt, val) in opts:
        if opt == '-c':
            conf_path = val
        elif opt == '-d':
            db_path = val
        elif opt == '-f':
            force = True
        elif opt == '-h':
            usage()
            sys.exit(0)
        elif opt == '-v':
            verbose = True
        else:
            print 'Error: %s not supported!' % opt
            sys.exit(1)

    try:
        fix_userdb_keys(conf_path, db_path, force, verbose)
    except Exception, err:
        print err
        sys.exit(1)
