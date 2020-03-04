#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# job - Core job helper functions
# Copyright (C) 2003-2020  The MiG Project lead by Brian Vinter
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

"""Job functions"""

import fcntl
import os
import time

from glob import glob

from shared.base import client_id_dir
from shared.fileio import send_message_to_grid_script, unpickle
from shared.mrslparser import parse
from shared.vgrid import init_vgrid_script_list
from shared.vgridaccess import get_vgrid_map, OWNERS, MEMBERS, VGRIDS

JOB = 'job'
QUEUE = 'queue'
JOB_TYPES = [
    JOB,
    QUEUE
]

class Job:
    """Job objects"""

    # job_id = None

    def __init__(self):

        # self.job_id = "7239472394"

        pass

    def to_dict(self):
        """Object to dictionary helper"""
        res = {}
        for attr in dir(self):

            # Only CAPITAL ones are job attributes

            if attr == attr.upper():
                res[attr] = eval('self.%s' % attr)
        return res


def get_job_id(configuration):
    """Read current job id from job_id_counter, increment with one 
    and write new value to the file again. Create the file if it 
    does not exist.
    """

    logger = configuration.logger
    filehandle = None
    job_id_counter_path = os.path.join(configuration.mig_system_files,
            'job_id_counter')
    try:
        filehandle = open(job_id_counter_path, 'r+')
    except IOError, ioe:
        logger.error('No job id counter found - creating one (first run?)')

    if filehandle:
        try:
            fcntl.flock(filehandle.fileno(), fcntl.LOCK_EX)
            val = filehandle.readline().strip()
            filehandle.seek(0, 0)
            filehandle.write(str(int(val) + 1))
            filehandle.close()
        except IOError, ioe:
            logger.error('get_job_id: ioerror: %s' % ioe)
            return -1
    else:
        try:

            # Create file if it doesn't exist.

            filehandle = open(job_id_counter_path, 'w')
            fcntl.flock(filehandle.fileno(), fcntl.LOCK_EX)
            val = '0'
            filehandle.write(str(int(val) + 1))
            filehandle.close()
        except IOError, ioe:
            logger.error('get_job_id: Failed to create job id counter file!%s'\
                 % ioe)
            return -1
    return val

def fill_mrsl_template(
    job_template,
    mrsl_fd_or_path,
    trigger_path,
    state_change,
    rule,
    expand_map,
    configuration,
    ):
    """Generate a job description in mrsl_fd_or_path from the job_template,
    using the trigger details in the rule dictionary and the actual (relative)
    trigger_path of the file and what kind of change triggered the event.
    expand_map is a dictionary mapping variables to actual values.
    Please note that mrsl_fd_or_path may be a path or a file-like object.
    """
    logger = configuration.logger
    logger.debug("fill template based on trigger for %s : %s and rule %s" % \
                 (trigger_path, state_change, rule))
    if isinstance(mrsl_fd_or_path, basestring):
        mrsl_fd = open(mrsl_fd_or_path, 'w+b')
        do_close = True
    else:
        mrsl_fd = mrsl_fd_or_path
        do_close = False

    # If rule requires additional environment vars, add them to the job
    # definition here.
    add_env_vars = rule.get('environment_vars', None)
    if add_env_vars:
        env_var_str = ''
        for env_var_key, env_var_val in add_env_vars.items():
            env_var_str \
                += "\n%s=%s" % (env_var_key, env_var_val)
        env_key = '::ENVIRONMENT::'
        if env_key in job_template:
            job_template = \
                job_template[
                :job_template.find(env_key) + len(env_key)] \
                + env_var_str \
                + job_template[
                  job_template.find(env_key) + len(
                      env_key):]
        else:
            job_template += env_key + env_var_str

    filled_template = ''
    try:
        filled_template = "%s" % job_template
        for (key, val) in expand_map.items():
            filled_template = filled_template.replace(key, val)
        logger.info("filled_template is:\n%s" % filled_template)
        mrsl_fd.write(filled_template)
        mrsl_fd.flush()
        if do_close:
            mrsl_fd.close()
    except Exception, exc:
        logger.error("failed to fill template %s:\n%s" % \
                     (exc, job_template))
        return False
    return True

def new_job(
    filename,
    client_id,
    configuration,
    forceddestination,
    returnjobid=False,
    ):
    """This function submits a file to the MiG system by assigning
    a unique name to the new job and sends it to the parser.
    It should be called by all other functions when a job should be submitted.
    New: function can now be called with returnjobid argument so new output
    model can get job_id seperately (instead of the return message string)
    """

    mig_server_id = configuration.mig_server_id

    counter = get_job_id(configuration)
    gmt = time.gmtime()
    timestamp = str(gmt[1]) + '_' + str(gmt[2]) + '_' + str(gmt[0])\
         + '__' + str(gmt[3]) + '_' + str(gmt[4]) + '_' + str(gmt[5])
    job_id = str(counter) + '_' + str(timestamp) + '_'\
         + str(mig_server_id)

    # Call the mRSL parser

    filename_spaces = filename.replace('\\ ', '\\\\\\ ')

    (parseresult, parsemsg) = parse(filename_spaces, job_id, client_id,
                                    forceddestination)

    if parseresult:
        if returnjobid:
            return (True, '%s is the job id assigned.' % job_id, job_id)
        else:
            return (True, '%s is the job id assigned.' % job_id)
    else:
        if returnjobid:
            return (False, '''parse failed, Error in mRSL file - or parser -
or subsystem :)\n%s''' % parsemsg, None)
        else:
            return (False, '''parse failed, Error in mRSL file - or parser -
or subsystem :)\n%s''' % parsemsg)


def failed_restart(
    unique_resource_name,
    exe,
    job_id,
    configuration,
    ):
    """Helper for notifying grid_script when a exe restart failed"""

    # returns a tuple (bool status, str msg)

    send_message = 'RESTARTEXEFAILED %s %s %s\n'\
         % (unique_resource_name, exe, job_id)
    status = send_message_to_grid_script(send_message,
            configuration.logger, configuration)
    if not status:
        return (False,
                'Fatal error: Could not write message to grid_script')
    return (True, 'Notified server about failed restart')


def finished_job(
    session_id,
    unique_resource_name,
    exe,
    job_id,
    configuration,
    ):
    """Helper for notifying grid_script when a job finishes"""

    # returns a tuple (bool status, str msg)

    send_message = 'RESOURCEFINISHEDJOB %s %s %s %s\n'\
         % (unique_resource_name, exe, session_id, job_id)
    status = send_message_to_grid_script(send_message,
            configuration.logger, configuration)
    if not status:
        return (False,
                'Fatal error: Could not write message to grid_script')
    return (True, 'Notified server about finished job')


def create_job_object_from_pickled_mrsl(filepath, logger,
        external_dict):
    """Helper for submit from pickled mRSL"""
    job_dict = unpickle(filepath, logger)
    if not job_dict:
        return (False, 'could not unpickle mrsl file %s' % filepath)
    jobo = Job()
    for (key, value) in job_dict.iteritems():
        if str(type(value)) == "<type 'time.struct_time'>":

            # time.struct_time objects cannot be marshalled in the xmlrpc
            # version we use

            value = str(value)
        if external_dict.has_key(key):

            # ok, this info can be shown to the user (avoid leaking info that
            # break anonymity)

            setattr(jobo, key, value)
    return (True, jobo)


def get_job_ids_with_specified_project_name(
    client_id,
    project_name,
    mrsl_files_dir,
    logger,
    ):
    """Helper for finding a job with a given project field"""

    client_dir = client_id_dir(client_id)

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(os.path.join(mrsl_files_dir, client_dir)) \
         + os.sep

    # this is heavy :-/ we must loop all the mrsl files submitted by the user
    # to find the job ids belonging to the specified project

    matching_job_ids = []
    all_files = os.listdir(base_dir)

    for mrsl_file in all_files:
        job_dict = unpickle(base_dir + os.sep + mrsl_file, logger)
        if not job_dict:
            continue
        if job_dict.has_key('PROJECT'):
            if job_dict['PROJECT'] == project_name:
                matching_job_ids.append(job_dict['JOB_ID'])
    return matching_job_ids


def get_job_with_id(configuration, job_id, vgrid, client_id,
                    only_user_jobs=True):
    """Retrieves the job mrsl definition of a given job id. If only_user_jobs
    is true then only the clients job files are searched, otherwise the jobs
    of other users in the given vgrid are also used, provided the client is a
    user in that vgrid."""

    # This will try and retrieve a jobs mrsl file as efficiently as possible
    # depending on what help the function caller can provide. If a caller
    # already knows the client_id then we can attempt to go straight to the
    # job file, otherwise we will need to search through all users in a vgrid.
    # This should only be used as a last resort as this will be an extremely
    # costly action.

    if only_user_jobs and not client_id:
        return (False, "Cannot retrieve a job without 'client_id' being set. ")

    success, msg, _ = init_vgrid_script_list(vgrid, client_id,
                                             configuration)
    if not success:
        return (False, msg)

    job_file = job_id
    if not job_file.endswith('.mRSL'):
        job_file += '.mRSL'

    # First search given users directory.
    path = os.path.abspath(
        os.path.join(configuration.mrsl_files_dir,
                     client_id_dir(client_id), job_file)
    )

    if os.path.exists(path):
        job_dict = unpickle(path, configuration.logger)

        if job_dict:
            return (True, job_dict)

    if only_user_jobs:
        return (False, "Could not locate job file '%s' for user '%s'"
                % (job_file, client_id))

    users = []
    # If vgrid is known we can just search through the users on that vgrid.
    if vgrid:
        vgrid_map = get_vgrid_map(configuration)[VGRIDS][vgrid]

        users += vgrid_map[OWNERS]
        users += vgrid_map[MEMBERS]
        for user in users:
            path = os.path.abspath(
                os.path.join(configuration.mrsl_files_dir, user, job_file)
            )

            matches = glob(path)
            if not matches:
                break
            if len(matches) > 1:
                break

            job_dict = unpickle(matches[0], configuration.logger)

            if job_dict:
                return (True, job_dict)

    return (False, "Could not locate job file for job '%s'." % job_file)


def fields_to_mrsl(configuration, user_arguments_dict, external_dict):
    """Generate mRSL from fields"""
    spec = []
    for key in external_dict.keys():
        attr_name = key
        if user_arguments_dict.has_key(attr_name):
            spec.append('::%s::' % attr_name)
            attr = user_arguments_dict[attr_name]

            # FIXME: this type check is not perfect... I should be
            # able to extend on any sequence...

            if isinstance(attr, list):
                spec.extend(attr)
            elif isinstance(attr, tuple):
                spec.extend(attr)
            else:
                spec.append(attr)
            spec.append('')
    mrsl = '\n'.join(spec)
    return mrsl
