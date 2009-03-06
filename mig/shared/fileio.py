#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# fileio - [insert a few words of module description on this line]
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

"""IO operations"""

import time
import os
import pickle as org_pickle
import shutil
import fcntl


def write_file(content, filename, logger):
    logger.debug("writing file: %s" % filename) 
    # create dir if it does not exists
    (head, _) = os.path.split(filename)
    if not os.path.isdir(head):
        try:
            logger.debug("making directory %s" % head)
            os.mkdir(head)
        except Exception, err:
            logger.error("could not create dir %s" % err)
    try:
        filehandle = open(filename, "w")
        filehandle.write(content)
        filehandle.close()
        logger.debug("file written: %s" % filename)
        return True
    except Exception, err:
        logger.error("could not write %s %s" % (filename, err))
        return False

def delete_file(filename, logger):
    logger.debug("deleting file: %s" % filename) 
    if os.path.exists(filename):
        try:
            os.remove(filename)
            result = True
        except Exception, err:
            logger.error("could not delete %s %s" % (filename, err))
            result = False
    else:       
        logger.info("%s does not exist." % (filename))
        result = False

    return result

def make_symlink(dest, src, logger):
    try:
        logger.debug("creating symlink: %s %s" % (dest, src))
        os.symlink(dest, src)
    except Exception, err:
        logger.error("Could not create symlink %s" % err)
        return False
    return True

def unpickle_and_change_status(filename, newstatus, logger):
    try:
        # change status in the MiG server mRSL file
        filehandle = open(filename, "r+")
        job_dict =  org_pickle.load(filehandle)
        job_dict["STATUS"] = newstatus
        job_dict[newstatus + "_TIMESTAMP"] = time.gmtime()
        filehandle.seek(0, 0)
        org_pickle.dump(job_dict, filehandle)
        filehandle.close()
        logger.info("job status changed to %s: %s" % (newstatus, filename))
        return job_dict
    except Exception, err:
        logger.error("could not change job status to %s: %s %s" % (newstatus, filename, err))
        return False
    
def unpickle(filename, logger):
    try:
        filehandle = open(filename, "r")
        job_dict = org_pickle.load(filehandle)
        filehandle.close()
        logger.debug("%s was unpickled successfully" % filename)
        return job_dict
    except Exception, err:
        logger.error("%s could not be opened/unpickled! %s" % (filename, err))
        return False
             
def pickle(job_dict, filename, logger):
    try:
        filehandle = open(filename, "w")
        org_pickle.dump(job_dict, filehandle, 0)
        filehandle.close()
        logger.debug("pickle success: %s" % filename)
        return True
    except Exception, err:
        logger.error("could not pickle: %s %s" % (filename, err))
        return False
    
def send_message_to_grid_script(message, logger, configuration):
    try:
        filehandle = open(configuration.grid_stdin, "a")
        fcntl.flock(filehandle.fileno(), fcntl.LOCK_EX)
        filehandle.write(message)
        filehandle.close()
        return True
    except Exception, err:
        print "could not get exclusive access or write to grid_stdin!"
        logger.error("could not get exclusive access or write to grid_stdin: %s %s" % (message, err))
        return False

def touch(filepath, timestamp=None):
    try:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            filehandle = open(filepath, "r+w")
            i = filehandle.read(1)
            filehandle.seek(0, 0)
            filehandle.write(i)
            filehandle.close()
        else:
            open(filepath, "w").close()
        
        if timestamp != None:
            # set timestamp to supplied value
            os.utime(filepath, (timestamp, timestamp))
            
    except Exception, err:
        logger.error("could not touch file: '%s', Error: %s" % (filepath, err))
        return False
