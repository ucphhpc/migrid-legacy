#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# breakpoint - Python GDB breakpoint
# Copyright (C) 2003-2019  The MiG Project lead by Brian Vinter
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

"""Python GNU debugger (GDB) breakpoint
https://devguide.python.org/gdb/
https://wiki.python.org/moin/DebuggingWithGdb
https://sourceware.org/gdb/onlinedocs/gdb/Python-API.html

USAGE:
import pygdb.breakpoint
pygdb.breakpoint.enable()
pygdb.breakpoint.set()

This will block the executing thread (at the pygdb.breakpoint.set() call)
until 'pygdb.console.extension.console_connected' is called
from the gdb console.
"""

import os
import logging
import time
import threading
import _pygdb

enabled = False
gdb_logger = None
console_connected = None
breakpoint_lock = None


def enable(logger=None):
    """Enable breakpoint"""
    global enabled
    global console_connected
    global breakpoint_lock

    enabled = True
    console_connected = False
    breakpoint_lock = threading.Lock()
    set_logger(logger)
    log("enabled")


def log(msg):
    """log info messages"""
    if not enabled:
        return

    pid = os.getpid()
    tid = threading.current_thread().ident
    log_msg = "(PID: %d, TID: 0x%0.x): %s" \
        % (pid, tid, msg)

    if isinstance(gdb_logger, logging.Logger):
        gdb_logger.info(log_msg)
    else:
        print "pygdb: %s" % log_msg


def set_logger(logger):
    """set logger to used by the log function"""
    if not enabled:
        return False

    global gdb_logger

    result = False
    if isinstance(logger, logging.Logger):
        gdb_logger = logger
        result = True

    return result


def set():
    """Used to set breakpoint, busy-wait until gdb console is connected"""
    if not enabled:
        return

    global console_connected

    # Wait for gdb console
    breakpoint_lock.acquire()
    while not console_connected:
        log("breakpoint.set: waiting for gdb console")
        breakpoint_lock.release()
        time.sleep(1)
        breakpoint_lock.acquire()
    breakpoint_lock.release()

    # Set breakpoint mark for GDB
    log("breakpoint.set: breakpoint_mark")
    _pygdb.breakpoint_mark()


def set_console_connected():
    """NOTE: This function should only be called from the GNU Debugger (GDB)
    while execution is in 'interruption mode'.
    Therefore applying locks is not needed and might cause deadlocks
    in the GNU Debugger helper functions"""
    global console_connected
    console_connected = True
