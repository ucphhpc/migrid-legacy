#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# extcert - External certificate account sign up backend
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# -- END_HEADER ---
#

"""Request account sign up with external certificate back end"""

import os

import shared.returnvalues as returnvalues
from shared.accountreq import valid_name_chars, dn_max_len, account_js_helpers
from shared.base import distinguished_name_to_user
from shared.defaults import csrf_field
from shared.handlers import get_csrf_limit, make_csrf_token
from shared.html import themed_styles
from shared.init import initialize_main_variables, find_entry
from shared.functional import validate_input_and_cert


def signature():
    """Signature of the main function"""

    defaults = {}
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
        require_user=False
    )
    if not validate_status:
        return (accepted, returnvalues.CLIENT_ERROR)

    title_entry = find_entry(output_objects, 'title')
    title_entry['text'] = '%s certificate account sign up' % \
                          configuration.short_title
    title_entry['skipmenu'] = True
    form_fields = ['cert_id', 'cert_name', 'organization', 'email', 'country',
                   'state', 'comment']
    title_entry['style'] = themed_styles(configuration)
    title_entry['javascript'] = account_js_helpers(form_fields)
    output_objects.append({'object_type': 'html_form',
                           'text': '''
 <div id="contextual_help">
  <div class="help_gfx_bubble"><!-- graphically connect field with help text--></div>
  <div class="help_message"><!-- filled by js --></div>
 </div>
'''})
    header_entry = {'object_type': 'header', 'text':
                    'Welcome to the %s certificate account sign up page' %
                    configuration.short_title}
    output_objects.append(header_entry)

    # Redirect to reqcert page without certificate requirement but without
    # changing access method (CGI vs. WSGI).

    certreq_url = os.environ['REQUEST_URI'].replace('-bin', '-sid')
    certreq_url = os.path.join(os.path.dirname(certreq_url), 'reqcert.py')
    certreq_link = {'object_type': 'link', 'destination': certreq_url,
                    'text': 'Request a new %s certificate account' %
                            configuration.short_title}
    new_user = distinguished_name_to_user(client_id)

    # If cert auto create is on, add user without admin interaction

    form_method = 'post'
    csrf_limit = get_csrf_limit(configuration)
    fill_helpers = {'valid_name_chars': valid_name_chars,
                    'client_id': client_id,
                    'dn_max_len': dn_max_len,
                    'common_name': new_user.get('full_name', ''),
                    'org': new_user.get('organization', ''),
                    'email': new_user.get('email', ''),
                    'state': new_user.get('state', ''),
                    'country': new_user.get('country', ''),
                    'site': configuration.short_title,
                    'form_method': form_method,
                    'csrf_field': csrf_field,
                    'csrf_limit': csrf_limit}
    if configuration.auto_add_cert_user == False:
        target_op = 'extcertaction'
    else:
        target_op = 'autocreate'
    csrf_token = make_csrf_token(configuration, form_method, target_op,
                                 client_id, csrf_limit)
    fill_helpers.update({'target_op': target_op, 'csrf_token': csrf_token})
    fill_helpers.update({'site_signup_hint': configuration.site_signup_hint})

    output_objects.append({'object_type': 'html_form', 'text': """This page is
used to sign up for %(site)s with an existing certificate from a Certificate
Authority (CA) allowed for %(site)s.
You can use it if you already have a x509 certificate from another accepted CA.
In this way you can simply use your existing certificate for %(site)s access
instead of requesting a new one.
<br />
The page tries to auto load any certificate your browser provides and fill in
the fields accordingly, but in case it can't guess all
<span class=mandatory>mandatory</span> fields, you still need to fill in
those.<br />
Please enter any missing information below and press the Send button to submit
the external certificate sign up request to the %(site)s administrators.
<p class='criticaltext highlight_message'>
IMPORTANT: Please help us verify your identity by providing Organization and
Email data that we can easily validate!
</p>
%(site_signup_hint)s
<hr />
<div class=form_container>
<!-- use post here to avoid field contents in URL -->
<form method='%(form_method)s' action='%(target_op)s.py' onSubmit='return validate_form();'>
<input type='hidden' name='%(csrf_field)s' value='%(csrf_token)s' />
<table>
<!-- NOTE: javascript support for unicode pattern matching is lacking so we
           only restrict e.g. Full Name to words separated by space here. The
           full check takes place in the backend, but users are better of with
           sane early warnings than the cryptic backend errors.
-->
<tr><td class='mandatory label'>Certificate DN</td><td><input id='cert_id_field' type=text size=%(dn_max_len)s maxlength=%(dn_max_len)s name=cert_id value='%(client_id)s' required pattern='(/[a-zA-Z]+=[^/ ]+([ ][^/ ]+)*)+' title='The Distinguished Name field of your certificate, i.e. key=value pairs separated by slashes' /></td><td class=fill_space></td></tr>
<tr><td class='mandatory label'>Full name</td><td><input id='cert_name_field' type=text name=cert_name value='%(common_name)s' required pattern='[^ ]+([ ][^ ]+)+' title='Your full name, i.e. two or more names separated by space' /></td><td class=fill_space></td></tr>
<tr><td class='mandatory label'>Email address</td><td><input id='email_field' type=email name=email value='%(email)s' title='A valid email address that you read' /></td><td class=fill_space></td></tr>
<tr><td class='mandatory label'>Organization</td><td><input id='organization_field' type=text name=org value='%(org)s' required pattern='[^ ]+([ ][^ ]+)*' title='Name of your organisation: one or more abbreviations or words separated by space' /></td><td class=fill_space></td></tr>
<tr><td class='mandatory label'>Two letter country-code</td><td><input id='country_field' type=text name=country minlength=2 maxlength=2 value='%(country)s' required pattern='[A-Z]{2}' title='The two capital letters used to abbreviate your country' /></td><td class=fill_space></td></tr>
<tr><td class='optional label'>State</td><td><input id='state_field' type=text name=state value='%(state)s' pattern='([A-Z]{2})?' maxlength=2 title='Leave empty or enter the capital 2-letter abbreviation of your state if you are a US resident' /></td><td class=fill_space></td></tr>
<tr><td class='optional label'>Comment or reason why you should<br />be granted a %(site)s certificate:</td><td><textarea id='comment_field' rows=4 name=comment title='A free-form comment where you can explain what you need the certificate for'></textarea></td><td class=fill_space></td></tr>
<tr><td class='label'><!-- empty area --></td><td><input id='submit_button' type='submit' value='Send' /></td><td class=fill_space></td></tr>
</table>
</form>
</div>
<!-- Hidden help text -->
<div id='help_text'>
  <div id='cert_id_help'>Must be the exact Distinguished Name (DN) of your certificate</div>
  <div id='cert_name_help'>Your full name, restricted to the characters in '%(valid_name_chars)s'</div>
  <div id='organization_help'>Organization name or acronym  matching email</div>
  <div id='email_help'>Email address associated with your organization if at all possible</div>
  <div id='country_help'>Country code of your organization and on the form DE/DK/GB/US/.. , <a href='https://en.wikipedia.org/wiki/ISO_3166-1'>help</a></div>
  <div id='state_help'>Optional 2-letter ANSI state code of your organization, please just leave empty unless it is in the US or similar, <a href='https://en.wikipedia.org/wiki/List_of_U.S._state_abbreviations'>help</a></div>
  <div id='comment_help'>Optional, but a short informative comment may help us verify your certificate needs and thus speed up our response.</div>
</div>
""" % fill_helpers})

    return (output_objects, returnvalues.OK)
