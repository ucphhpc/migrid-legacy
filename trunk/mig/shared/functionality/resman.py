#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# resman - [insert a few words of module description on this line]
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

"""Resource management back end functionality"""

import shared.returnvalues as returnvalues
from shared.functional import validate_input_and_cert
from shared.init import initialize_main_variables, find_entry
from shared.resource import anon_to_real_res_map
from shared.vgridaccess import user_allowed_resources, get_resource_map, \
     OWNERS, CONF


def signature():
    """Signature of the main function"""

    defaults = {}
    return ['resources', defaults]


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    (configuration, logger, output_objects, op_name) = \
        initialize_main_variables(op_header=False)
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

    allowed = user_allowed_resources(configuration, client_id)
    res_map = get_resource_map(configuration)
    anon_map = anon_to_real_res_map(configuration.resource_home)

    # Iterate through resources and show management for each one requested

    res_list = {'object_type': 'resource_list', 'resources': []}
    fields = ['PUBLICNAME', 'CPUCOUNT', 'MEMORY', 'DISK', 'ARCHITECTURE', 'SANDBOX']
    sorted_names = allowed.keys()
    sorted_names.sort()
    for visible_res_name in sorted_names:
        unique_resource_name = visible_res_name
        if visible_res_name in anon_map.keys():
            unique_resource_name = anon_map[visible_res_name]

        res_obj = {'object_type': 'resource', 'name': visible_res_name}

        if client_id in res_map[unique_resource_name][OWNERS]:

            # Admin of resource when owner

            # TODO: add support for fields in links for id, title, etc (for css img)
            res_obj['rmresownerlink'] = \
                                    {'object_type': 'link',
                                     'destination':
                                     'rmresowner.py?unique_resource_name=%s;cert_id=%s'\
                                     % (unique_resource_name, client_id),
                                     'text': "<img src='/images/icons/cancel.png' title='Remove ownership'>"}
            res_obj['resadminlink'] = \
                                    {'object_type': 'link',
                                     'destination':
                                     'resadmin.py?unique_resource_name=%s'\
                                     % unique_resource_name,
                                     'text': "<img src='/images/icons/wrench.png' title='Administrate'>"}
            
        # fields for everyone: public status
        for name in fields:
            res_obj[name] = res_map[unique_resource_name][CONF].get(name, '')
        # Use allowed nodes in contrast to connected nodes
        res_obj['NODECOUNT'] = len(allowed[visible_res_name])
        res_list['resources'].append(res_obj)

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = 'Resource management'

    # jquery support for tablesorter and confirmation on "leave":

    title_entry['javascript'] = '''
<link rel="stylesheet" type="text/css" href="/images/css/jquery.managers.css" media="screen"/>

<script type="text/javascript" src="/images/js/jquery-1.3.2.min.js"></script>
<script type="text/javascript" src="/images/js/jquery.tablesorter.js"></script>

<script type="text/javascript" >

var confirmDelete = function(name, link) {
    var yes = confirm("Really delete the resource " + name + " ?");
    if (yes) {
         window.location=link;
    }
}

$(document).ready(function() {

          // table initially sorted by col. 2 (admin), then 1 (member), then 0
          var sortOrder = [[2,0],[1,1],[0,0]];

          // use an image title for sorting if there is any inside
          var imgTitle = function(contents) {
              var key = $(contents).find("img").attr("title");
              if (key == null) {
                   key = $(contents).html();
              }
              return key;
          }

          $("#resourcetable").tablesorter({widgets: ["zebra"],
                                        sortList:sortOrder,
                                        textExtraction: imgTitle
                                       });
     }
);
</script>
'''

    output_objects.append({'object_type': 'header', 'text': 'Available Resources'
                          })

    output_objects.append({'object_type': 'sectionheader', 'text'
                          : 'Resources available on this server'})
    output_objects.append({'object_type': 'text', 'text'
                          : '''
All available resources are listed below with overall hardware specifications. Any resources that you own will have a administration icon that you can click to open resource management.
'''
                       })
    output_objects.append(res_list)

    output_objects.append({'object_type': 'sectionheader', 'text'
                          : 'Resource Status'})
    output_objects.append({'object_type': 'text',
                           'text': '''
Live resource status is available in the resource monitor page with all VGrids/resources you can access
'''})
    output_objects.append({'object_type': 'link', 'text'
                          : 'Global resource monitor'
                          , 'destination'
                          : 'showvgridmonitor.py?vgrid_name=ALL'})

    output_objects.append({'object_type': 'sectionheader', 'text': 'Additional Resources'
                          })
    output_objects.append({'object_type': 'text',
                           'text': 'You can sign up spare or dedicated resources to the grid below.'
                           })
    output_objects.append({'object_type': 'link', 'text'
                          : 'Create a new %s resource' % \
                            configuration.short_title, 
                           'destination' : 'resedit.py'})
    output_objects.append({'object_type': 'sectionheader', 'text': ''})

    if configuration.site_enable_sandboxes:
        output_objects.append({'object_type': 'link', 'text'
                               : 'Administrate %s sandbox resources' % \
                               configuration.short_title,
                               'destination': 'ssslogin.py'})
        output_objects.append({'object_type': 'sectionheader', 'text': ''})
        output_objects.append({'object_type': 'link', 'text'
                               : 'Use this computer as One-click %s resource' % \
                               configuration.short_title
                               , 'destination': 'oneclick.py'})

    return (output_objects, status)
