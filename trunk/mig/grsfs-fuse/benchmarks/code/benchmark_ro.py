#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# benchmark_ro - benchmark read-only access
# Copyright (C) 2003-2011  The MiG Project lead by Brian Vinter
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

"""Benchmark with read-only file access"""

import os
import sys
import timeit
import pprint
import getopt

# dd if=/dev/urandom of=readfile bs=1048576 count=100

def default_configuration():
    """Return dictionary with default configuration values"""
    conf = {'repeat': 3, 'number': 1000}
    return conf

def usage():
    """Usage help"""
    print("Usage: %s" % sys.argv[0])
    print("Run read-only benchmark")
    print("Options and default values:")
    for (key, val) in default_configuration().items():
        print("--%s: %s" % (key, val))

def read_mark(size, filehandle):
    """Read size bytes from filehandle"""
    #print "Reading %d from %s" % (size, filehandle)
    #filehandle.seek(0)
    out = filehandle.read(size)
    #assert len(out) == size    

def prepare_files(conf):
    """Set up files used in benchmark"""
    if not os.path.exists("readfile"):
        data = open("/dev/urandom").read(conf['data_bytes'])
        readfile = open("readfile", "wb")
        readfile.write(data)
        readfile.close()

def main(conf):
    """Run timed benchmark"""
    read_sequence = [1, 2, 16, 256, 512, 1024, 2048, 4096, 8192, 16384]
    read_results = []

    prepare_files(conf)

    for i in read_sequence:
        read_results.append((i, max(
            timeit.repeat("read_mark(%s, filehandle)" % i,
                          setup = conf['setup'], repeat=conf['repeat'],
                          number=conf['number']))))

    out = pprint.PrettyPrinter()
    out.pprint(read_results)


if __name__ == '__main__':
    conf = default_configuration()

    # Parse command line

    try:
        (opts, args) = getopt.getopt(sys.argv[1:],
                                     'hn:r:', [
            'help',
            'number=',
            'repeat=',
            ])
    except getopt.GetoptError, err:
        print('Error in option parsing: ' + err.msg)
        usage()
        sys.exit(1)
        
    for (opt, val) in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-n', '--number'):
            try:
                conf["number"] = int(val)
            except ValueError, err:
                print('Error in parsing %s value: %s' % (opt, err))
                sys.exit(1)
        elif opt in ('-r', '--repeat'):
            try:
                conf["repeat"] = int(val)
            except ValueError, err:
                print('Error in parsing %s value: %s' % (opt, err))
                sys.exit(1)
        else:
            print("unknown option: %s" % opt)
            usage()
            sys.exit(1)
    conf['setup'] = """
import os
from __main__ import read_mark
filehandle = open('readfile', 'r')"""
    main(conf)
