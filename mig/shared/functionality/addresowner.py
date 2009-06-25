#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# addresowner - Add resource owner
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

# Minimum Intrusion Grid

"""Add a user ID to the list of administrators for a given
resource. 
"""

import os
import sys

from shared.listhandling import add_item_to_pickled_list
from shared.findtype import is_user, is_owner
from shared.init import initialize_main_variables
from shared.functional import validate_input_and_cert, REJECT_UNSET
import shared.returnvalues as returnvalues


def signature():
    """Signature of the main function"""

    defaults = {'unique_resource_name': REJECT_UNSET,
                'cert_id': REJECT_UNSET}
    return ['text', defaults]


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables()
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
    unique_resource_name = accepted['unique_resource_name'][-1]
    cert_id = accepted['cert_id'][-1]

    if not is_owner(client_id, unique_resource_name,
                    configuration.resource_home, logger):
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'You must be an owner of %s to add a new owner!'
                               % unique_resource_name})
        return (output_objects, returnvalues.CLIENT_ERROR)

    # is_owner incorporates unique_resource_name verification - no need to
    # specifically check for illegal directory traversal

    if not is_user(cert_id, configuration.user_home):
        output_objects.append({'object_type': 'error_text', 'text'
                              : '%s is not a valid MiG user!'
                               % cert_id})
        return (output_objects, returnvalues.CLIENT_ERROR)

    # Please note that base_dir must end in slash to avoid access to other
    # resource dirs when own name is a prefix of another user name

    base_dir = os.path.abspath(os.path.join(configuration.resource_home,
                                            unique_resource_name)) + os.sep

    # Add owner

    owners_file = base_dir + 'owners'
    (status, msg) = add_item_to_pickled_list(owners_file, cert_id,
            logger)

    if not status:
        output_objects.append({'object_type': 'error_text', 'text'
                              : 'Could not add new owner, reason: %s'
                               % msg})
        return (output_objects, returnvalues.SYSTEM_ERROR)

    output_objects.append({'object_type': 'text', 'text'
                          : 'New owner %s successfully added to %s!'
                           % (cert_id, unique_resource_name)})
    return (output_objects, returnvalues.OK)


