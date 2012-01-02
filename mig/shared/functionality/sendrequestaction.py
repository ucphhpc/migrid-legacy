#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# sendrequestaction - send request for e.g. member or ownership action handler
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

"""Send request e.g. for ownership or membership action back end"""

import shared.returnvalues as returnvalues
from shared.defaults import default_vgrid, any_vgrid, any_protocol
from shared.functional import validate_input_and_cert, REJECT_UNSET
from shared.handlers import correct_handler
from shared.init import initialize_main_variables, find_entry
from shared.notification import notify_user_thread
from shared.resource import anon_to_real_res_map
from shared.user import anon_to_real_user_map
from shared.vgrid import vgrid_list, vgrid_is_owner, vgrid_is_member, \
     vgrid_is_resource, user_allowed_vgrids
from shared.vgridaccess import get_user_map, get_resource_map, CONF, OWNERS, \
     USERID


def signature():
    """Signature of the main function"""

    defaults = {'unique_resource_name': [''],
                'vgrid_name': [''], 'cert_id': [''],
                'protocol': [any_protocol],
                'request_type': REJECT_UNSET,
                'request_text': REJECT_UNSET}
    return ['html_form', defaults]


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(client_id, op_header=False)
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

    if not correct_handler('POST'):
        output_objects.append(
            {'object_type': 'error_text', 'text'
             : 'Only accepting POST requests to prevent unintended updates'})
        return (output_objects, returnvalues.CLIENT_ERROR)

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = '%s send request' % \
                            configuration.short_title
    output_objects.append({'object_type': 'header', 'text'
                          : '%s send request' % \
                            configuration.short_title})

    target_id = client_id
    vgrid_name = accepted['vgrid_name'][-1].strip()
    visible_user_name = accepted['cert_id'][-1].strip()
    visible_res_name = accepted['unique_resource_name'][-1].strip()
    request_type = accepted['request_type'][-1].strip().lower()
    request_text = accepted['request_text'][-1].strip()
    protocols = [proto.strip() for proto in accepted['protocol']]
    use_any = False
    if any_protocol in protocols:
        use_any = True
        protocols = configuration.notify_protocols
    protocols = [proto.upper() for proto in protocols]

    valid_request_types = ['resourceowner', 'vgridowner', 'vgridmember',
                           'vgridresource', 'plain']
    if not request_type in valid_request_types:
        output_objects.append({
            'object_type': 'error_text', 'text'
            : '%s is not a valid request_type (valid types: %s)!'
            % (request_type.lower(),
               valid_request_types)})
        return (output_objects, returnvalues.CLIENT_ERROR)

    if not protocols:
            output_objects.append({
                'object_type': 'error_text', 'text':
                'No protocol specified!'})
            return (output_objects, returnvalues.CLIENT_ERROR)

    user_map = get_user_map(configuration)
    reply_to = user_map[client_id][USERID]

    if request_type == "plain":
        if not visible_user_name:
            output_objects.append({
                'object_type': 'error_text', 'text':
                'No user ID specified!'})
            return (output_objects, returnvalues.CLIENT_ERROR)

        user_id = visible_user_name
        anon_map = anon_to_real_user_map(configuration.user_home)
        if anon_map.has_key(visible_user_name):
            user_id = anon_map[visible_user_name]
        if not user_map.has_key(user_id):
            output_objects.append({'object_type': 'error_text',
                                   'text': 'No such user: %s' % \
                                   visible_user_name
                                   })
            return (output_objects, returnvalues.CLIENT_ERROR)
        target_name = user_id
        user_dict = user_map[user_id]
        allow_vgrids = user_allowed_vgrids(configuration, client_id)
        vgrids_allow_email = user_dict[CONF].get('VGRIDS_ALLOW_EMAIL', [])
        vgrids_allow_im = user_dict[CONF].get('VGRIDS_ALLOW_IM', [])
        if any_vgrid in vgrids_allow_email:
            email_vgrids = allow_vgrids
        else:
            email_vgrids = set(vgrids_allow_email).intersection(allow_vgrids)
        if any_vgrid in vgrids_allow_im:
            im_vgrids = allow_vgrids
        else:
            im_vgrids = set(vgrids_allow_im).intersection(allow_vgrids)
        if use_any:
            if not email_vgrids:
                protocols = [i for i in protocols if i != 'EMAIL']
            if not im_vgrids:
                protocols = [i for i in protocols if i == 'EMAIL']
        if not email_vgrids and 'EMAIL' in protocols:
            output_objects.append({
                'object_type': 'error_text', 'text'
                : 'You are not allowed to send emails to %s!' % \
                visible_user_name
                })
            return (output_objects, returnvalues.CLIENT_ERROR)
        if not im_vgrids and [i for i in protocols if i != 'EMAIL']:
            output_objects.append({
                'object_type': 'error_text', 'text'
                : 'You are not allowed to send instant messages to %s!' % \
                visible_user_name
                })
            return (output_objects, returnvalues.CLIENT_ERROR)
        for proto in protocols:
            if not user_dict[CONF].get(proto, False):
                if use_any:
                    protocols = [i for i in protocols if not i == proto]
                else:
                    output_objects.append({
                        'object_type': 'error_text', 'text'
                        : 'User %s does not accept %s messages!' % \
                        (visible_user_name, protocol)
                        })
                    return (output_objects, returnvalues.CLIENT_ERROR)
        if not protocols:
            output_objects.append({
                'object_type': 'error_text', 'text':
                'User %s does not accept requested protocol(s) messages!' % \
                visible_user_name})
            return (output_objects, returnvalues.CLIENT_ERROR)
        target_list = [user_id]
    elif request_type == "resourceowner":
        if not visible_res_name:
            output_objects.append({
                'object_type': 'error_text', 'text':
                'No resource ID specified!'})
            return (output_objects, returnvalues.CLIENT_ERROR)
        
        unique_resource_name = visible_res_name
        anon_map = anon_to_real_res_map(configuration.resource_home)
        if anon_map.has_key(visible_res_name):
            unique_resource_name = anon_map[visible_res_name]
        target_name = unique_resource_name
        res_map = get_resource_map(configuration)
        if not res_map.has_key(unique_resource_name):
            output_objects.append({'object_type': 'error_text',
                                   'text': 'No such resource: %s' % \
                                   visible_res_name
                                   })
            return (output_objects, returnvalues.CLIENT_ERROR)
        target_list = res_map[unique_resource_name][OWNERS]
        if client_id in target_list:
            output_objects.append({
                'object_type': 'error_text', 'text'
                : 'You are already an owner of %s!' % unique_resource_name
                })
            return (output_objects, returnvalues.CLIENT_ERROR)
    elif request_type in ["vgridmember", "vgridowner", "vgridresource"]:
        unique_resource_name = visible_res_name
        if not vgrid_name:
            output_objects.append({
                'object_type': 'error_text', 'text': 'No VGrid specified!'})
            return (output_objects, returnvalues.CLIENT_ERROR)

        # default vgrid is read-only
        
        if vgrid_name.upper() == default_vgrid.upper():
            output_objects.append({
                'object_type': 'error_text', 'text'
                : 'No requests for %s are not allowed!' % \
                default_vgrid
                })
            return (output_objects, returnvalues.CLIENT_ERROR)

        # stop owner or member request if already an owner

        if request_type != 'vgridresource':
            if vgrid_is_owner(vgrid_name, client_id, configuration):
                output_objects.append({
                    'object_type': 'error_text', 'text'
                    : 'You are already an owner of %s or a parent vgrid!' % \
                    vgrid_name})
                return (output_objects, returnvalues.CLIENT_ERROR)

        # only ownership requests are allowed for existing members

        if request_type == 'vgridmember':
            if vgrid_is_member(vgrid_name, client_id, configuration):
                output_objects.append({
                    'object_type': 'error_text', 'text'
                    : 'You are already a member of %s or a parent vgrid.' % \
                    vgrid_name})
                return (output_objects, returnvalues.CLIENT_ERROR)

        # set target to resource and prevent repeated resource access requests

        if request_type == 'vgridresource':
            target_id = unique_resource_name
            if vgrid_is_resource(vgrid_name, unique_resource_name,
                                 configuration):
                output_objects.append({
                    'object_type': 'error_text', 'text'
                    : 'You already have access to %s or a parent vgrid.' % \
                    vgrid_name})
                return (output_objects, returnvalues.CLIENT_ERROR)

        # Find all VGrid owners

        target_name = vgrid_name
        (status, target_list) = vgrid_list(vgrid_name, 'owners', configuration)
        if not status:
            output_objects.append({
                'object_type': 'error_text', 'text'
                : 'Could not load list of current owners for %s vgrid!'
                % vgrid_name})
            return (output_objects, returnvalues.CLIENT_ERROR)

    else:
        output_objects.append({
            'object_type': 'error_text', 'text': 'Invalid request type: %s' % \
            request_type})
        return (output_objects, returnvalues.CLIENT_ERROR)

    # Now send request to all targets in turn
    # TODO: inform requestor if no owners have mail/IM set in their settings
    
    for target in target_list:
        # USER_CERT entry is destination

        notify = []
        for proto in protocols:
            notify.append('%s: SETTINGS' % proto)
        job_dict = {'NOTIFY': notify, 'JOB_ID': 'NOJOBID', 'USER_CERT': target}

        notifier = notify_user_thread(
            job_dict,
            [target_id, target_name, request_type, request_text, reply_to],
            'SENDREQUEST',
            logger,
            '',
            configuration,
            )

        # Try finishing delivery but do not block forever on one message
        notifier.join(30)
    output_objects.append({'object_type': 'text', 'text':
                           'Sent %s message to %d people' % \
                           (request_type, len(target_list))})
    output_objects.append({'object_type': 'text', 'text':
                           """Please make sure you have notifications
configured on your Setings page if you expect a reply to this message"""})
    
    return (output_objects, returnvalues.OK)
