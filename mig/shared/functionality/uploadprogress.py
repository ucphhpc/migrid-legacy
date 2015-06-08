#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# uploadprogress - Plain file upload progress monitor back end
# Copyright (C) 2003-2014  The MiG Project lead by Brian Vinter
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

"""Plain file upload progress monitor back end (obsoleted by fancyupload)"""

import os

import shared.returnvalues as returnvalues
from shared.base import client_id_dir
from shared.functional import validate_input_and_cert, REJECT_UNSET
from shared.init import initialize_main_variables, find_entry
from shared.validstring import valid_user_path

block_size = 1024 * 1024


def signature():
    """Signature of the main function"""

    defaults = {
        'path': REJECT_UNSET,
        'size': REJECT_UNSET,
        }
    return ['html_form', defaults]


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(client_id, op_header=False)
    client_dir = client_id_dir(client_id)
    status = returnvalues.OK
    defaults = signature()[1]
    (validate_status, accepted) = validate_input_and_cert(
        user_arguments_dict,
        defaults,
        output_objects,
        client_id,
        configuration,
        allow_rejects=False,
        )
    if not validate_status:
        return (accepted, returnvalues.CLIENT_ERROR)

    path_list = accepted['path']
    size_list = [int(size) for size in accepted['size']]

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = '%s Upload Progress Monitor' % configuration.short_title

    if not configuration.site_enable_griddk:
        output_objects.append({'object_type': 'text', 'text':
                               '''Grid.dk features are disabled on this site.
Please contact the Grid admins %s if you think they should be enabled.
''' % configuration.admin_email})
        return (output_objects, returnvalues.OK)

    refresh_secs = 5
    meta = '<meta http-equiv="refresh" content="%s" />' % refresh_secs
    
    title_entry['meta'] = meta

    # Please note that base_dir must end in slash to avoid access to other
    # user dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(os.path.join(configuration.user_home,
                               client_dir)) + os.sep

    output_objects.append({'object_type': 'header', 'text'
                          : 'Upload progress'})

    done_list = [False for _ in path_list]
    progress_items = []
    index = -1
    for path in path_list:
        index += 1

        # Check directory traversal attempts before actual handling to avoid
        # leaking information about file system layout while allowing
        # consistent error messages

        real_path = os.path.abspath(os.path.join(base_dir, path))
        if not valid_user_path(real_path, base_dir, True):
            # out of bounds - save user warning for later to allow
            # partial match:
            # ../*/* is technically allowed to match own files.

            logger.warning('%s tried to %s restricted path %s ! (%s)'
                           % (client_id, op_name, real_path, path))
            output_objects.append({'object_type': 'file_not_found',
                                  'name': path})
            status = returnvalues.FILE_NOT_FOUND
            continue
        if not os.path.isfile(real_path):
            output_objects.append({'object_type': 'error_text', 'text'
                                   : "no such upload: %s" % path})
            status = returnvalues.CLIENT_ERROR
            continue

        relative_path = real_path.replace(base_dir, '')
        try:
            logger.info('Checking size of upload %s' % real_path)

            cur_size = os.path.getsize(real_path)
            total_size = size_list[index]
            percent = round(100.0 * cur_size / total_size, 1)
            done_list[index] = (cur_size == total_size)
            progress_items.append({'object_type': 'progress', 'path': path,
                                   'cur_size': cur_size, 'total_size':
                                   total_size, 'percent': percent,
                                   'done': done_list[index], 'progress_type':
                                   'upload'})
        except Exception, exc:

            # Don't give away information about actual fs layout

            output_objects.append({'object_type': 'error_text', 'text'
                                   : '%s upload could not be checked! (%s)'
                                   % (path, str(exc).replace(base_dir, ''
                                                             ))})
            status = returnvalues.SYSTEM_ERROR
            continue

    # Stop reload when all done
    
    if not False in done_list:
        title_entry['meta'] = ''
        
    output_objects.append({'object_type': 'progress_list',
                           'progress_list': progress_items})

    return (output_objects, status)
