#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# notification - instant message and email notification helpers
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,  MA 02110-1301, USA.
#
# -- END_HEADER ---
#

"""Notification functions"""

import datetime
import os
import smtplib
import threading
from email import Encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.mime.text import MIMEText
from email.Utils import formatdate
from urllib import quote

from shared.base import force_utf8, generate_https_urls
from shared.defaults import email_keyword_list, job_output_dir, \
    transfer_output_dir
from shared.safeinput import is_valid_simple_email
from shared.settings import load_settings

# might be python 2.4, without xml.etree
# ...in which case: better not configure usage_record_dir

try:
    from shared.usagerecord import UsageRecord
except Exception, err:
    pass


def create_notify_message(
    jobdict,
    args_list,
    status,
    statusfile,
    configuration,
):
    """Helper to create notifications"""

    header = ''
    txt = ''
    jobid = jobdict['JOB_ID']
    job_retries = jobdict.get('RETRIES', configuration.job_retries)
    var_dict = {'jobid': jobid, 'retries': job_retries,
                'out_dir': job_output_dir,
                'site': configuration.short_title}

    entity_mapper = {'vgridmember': 'member', 'vgridowner': 'owner',
                     'vgridresource': 'resource', 'resourceowner': 'owner'}
    accept_mapper = {'vgridaccept': 'vgrid', 'resourceaccept': 'resource'}
    reject_mapper = {'vgridreject': 'vgrid', 'resourcereject': 'resource'}

    frame_template = """---

%s

---
"""
    txt += """
*** IMPORTANT: direct replies to this automated message will NOT be read! ***

"""
    if status == 'SUCCESS':
        header = '%s JOB finished' % configuration.short_title
        var_dict['generated_links'] = generate_https_urls(
            configuration,
            '%(auto_base)s/%(auto_bin)s/jobstatus.py?job_id=%(jobid)s;flags=i',
            var_dict)
        txt += \
            '''
Your %(site)s job with JOB ID %(jobid)s has finished and
full status is available at:
%(generated_links)s

The job commands and their exit codes:
''' % var_dict
        try:
            status_fd = open(statusfile, 'r')
            txt += str(status_fd.read())
            status_fd.close()
        except Exception, err:
            txt += 'Could not be read (Internal error?): %s' % err
        var_dict['generated_stdout'] = generate_https_urls(
            configuration,
            '%(auto_base)s/cert_redirect/%(out_dir)s/%(jobid)s/%(jobid)s.stdout',
            var_dict)
        var_dict['generated_stderr'] = generate_https_urls(
            configuration,
            '%(auto_base)s/cert_redirect/%(out_dir)s/%(jobid)s/%(jobid)s.stderr',
            var_dict)
        txt += \
            '''
Link to stdout file (might not be available):
%(generated_stdout)s

Link to stderr file (might not be available):
%(generated_stderr)s
''' % var_dict
    elif status == 'FAILED':

        header = '%s JOB Failed' % configuration.short_title
        var_dict['generated_links'] = generate_https_urls(
            configuration,
            '%(auto_base)s/%(auto_bin)s/jobstatus.py?job_id=%(jobid)s;flags=i',
            var_dict)
        txt += \
            '''
The job with JOB ID %(jobid)s has failed after %(retries)s retries!
This may be due to internal errors, but full status is available at:
%(generated_links)s

Please contact the %(site)s team if the problem occurs multiple times.
''' % var_dict
    elif status == 'EXPIRED':
        header = '%s JOB Expired' % configuration.short_title
        var_dict['generated_links'] = generate_https_urls(
            configuration,
            '%(auto_base)s/%(auto_bin)s/jobstatus.py?job_id=%(jobid)s;flags=i',
            var_dict)
        txt += \
            '''
Your %(site)s job with JOB ID %(jobid)s has expired, after remaining in the queue for too long.
This may be due to internal errors, but full status is available at:
%(generated_links)s

Please contact the %(site)s team for details about expire policies.
''' % var_dict
    elif status == 'SENDREQUEST':
        from_id = args_list[0]
        target_name = args_list[1]
        request_type = args_list[2]
        request_text = args_list[3]
        reply_to = args_list[4]
        # IMPORTANT: We have to be careful to URLencode exotic chars without
        # interfering with generate_https_urls. It must go through a var_dict
        # entry, since putting it directly in URL will result in format string
        # expansion errors (stray '%' chars).
        var_dict['enc_target_name'] = quote(target_name)
        var_dict['enc_reply_to'] = quote(reply_to)
        if request_type == "plain":
            header = '%s user message' % configuration.short_title
            txt += """This is a message sent on behalf of %s:
""" % from_id
            txt += frame_template % request_text
        elif request_type in accept_mapper.keys():
            kind = accept_mapper[request_type]
            header = '%s %s admission note' % (configuration.short_title, kind)
            txt += """This is a %s admission note sent on behalf of %s:
""" % (kind, from_id)
            txt += frame_template % request_text
        elif request_type in reject_mapper.keys():
            kind = reject_mapper[request_type]
            header = '%s %s access rejection note' \
                % (configuration.short_title, kind)
            txt += """This is a %s access rejection note sent on behalf of %s:
""" % (kind, from_id)
            txt += frame_template % request_text
        elif request_type in entity_mapper.keys():
            entity = entity_mapper[request_type]
            header = '%s %s request' \
                % (configuration.short_title, request_type)
            if not request_text:
                request_text = '(no reason provided)'

            if request_type == "vgridresource":
                txt += """This is a %s request sent on behalf of the owners of
%s
who would like it to be added as a %s in %s and included the reason:
%s
""" % (request_type, from_id, entity, target_name, request_text)
            else:
                txt += """This is a %s request sent on behalf of
%s
who would like to be added as a %s in %s and included the reason:
%s
""" % (request_type, from_id, entity, target_name, request_text)

            txt += '''
If you want to handle the %s request please visit:
''' % entity
            if request_type.startswith('vgrid'):
                txt += generate_https_urls(
                    configuration,
                    '%(auto_base)s/%(auto_bin)s/adminvgrid.py?' +
                    'vgrid_name=%(enc_target_name)s',
                    var_dict)
            elif request_type.startswith('resource'):
                txt += generate_https_urls(
                    configuration,
                    '%(auto_base)s/%(auto_bin)s/resadmin.py?' +
                    'unique_resource_name=%(enc_target_name)s',
                    var_dict)
            txt += ''' and add or
reject it.
You can find the request in the Pending Requests table there and either click
the green plus-icon to accept it or the red minus-icon to reject it.

'''
        else:
            txt += 'INVALID REQUEST TYPE: %s\n\n' % request_type

        txt += """
If the message didn't include any contact information you may still be able to
reply to the requestor using one of the message links on the profile page for
the sender:
"""
        txt += generate_https_urls(
            configuration,
            '%(auto_base)s/%(auto_bin)s/viewuser.py?cert_id=%(enc_reply_to)s',
            var_dict)
    elif status == 'TRANSFERCOMPLETE':
        header = '%s background transfer complete' % configuration.short_title
        var_dict.update({'status_code': args_list[1],
                         'status_msg': args_list[2],
                         'out_dir': transfer_output_dir})
        var_dict.update(jobdict)
        var_dict['status_link'] = generate_https_urls(
            configuration,
            '%(auto_base)s/%(auto_bin)s/fileman.py?path=%(out_dir)s/%(transfer_id)s/',
            var_dict)
        txt += \
            '''
Your %(site)s background transfer with ID %(transfer_id)s has finished with
status %(status_code)s and status message:
%(status_msg)s

The full status and output files are available at:
%(status_link)s
''' % var_dict
    elif status == 'INVITESHARE':
        header = '%s share link invitation' % configuration.short_title
        var_dict.update({'auto_msg': args_list[0], 'msg': args_list[1],
                         'admins': configuration.admin_email})
        var_dict.update(jobdict)
        txt += '''
%(auto_msg)s
%(msg)s

****************************************************************************
 Please send any replies EXPLICITLY to the person who invited you using the
 email address included above.
 Feel free to report any abuse of this service to the %(site)s admins
 (%(admins)s)
 e.g. in case you think this is a spam message.
****************************************************************************
        ''' % var_dict
    elif status == 'PASSWORDREMINDER':
        from_id = args_list[0]
        password = args_list[1]
        header = '%s pasword reminder' % configuration.short_title
        txt += """This is an auto-generated password reminder from %s:
%s
""" % (configuration.short_title, password)
        txt += """Feel free to change the password as described in the online
documentation.
"""
    elif status == 'ACCOUNTINTRO':
        from_id = args_list[0]
        user_email = args_list[1]
        user_name = args_list[2]
        short_title = configuration.short_title
        migoid_title = configuration.user_mig_oid_title
        migoid_url = configuration.migserver_https_mig_oid_url
        header = 'Re: %s OpenID request for %s' % (short_title, user_name)
        txt += """This is an auto-generated intro message from %s to inform
about the creation or renewal of your %s user OpenID account.

You can log in with username %s and your chosen password at
%s

Please contact the %s admins in case you should ever loose or forget your
password. The same applies if you suspect or know that someone may have gotten
hold of your login.

Regards,
The %s Admins
""" % (short_title, migoid_title, user_email, migoid_url, short_title,
            short_title)
    elif status == 'ACCOUNTEXPIRE':
        from_id = args_list[0]
        user_email = args_list[1]
        user_name = args_list[2]
        user_dict = args_list[3]
        short_title = configuration.short_title
        migoid_title = configuration.user_mig_oid_title
        auth_migoid_url = configuration.migserver_https_mig_oid_url
        anon_migoid_url = configuration.migserver_https_sid_url
        expire = datetime.datetime.fromtimestamp(user_dict['expire'])
        id_lines = """Full name: %(full_name)s
Email address: %(email)s
Organization: %(organization)s
Two letter country-code: %(country)s
State: %(state)s
""" % user_dict
        header = 'Re: %s OpenID request for %s' % (short_title, user_name)
        txt += """This is an auto-generated account expire warning from %s to
inform you about the need to renew your %s user OpenID account before %s
if you want to preserve that account access.

As long as your account hasn't expired you can always login with your username
%s and request semi-automatic renewal only filling the password and comment
fields at
%s/cgi-bin/reqoid.py
In that way you can also choose a new password if you like.

After account expiry you can only manually renew by opening the
basic account request page at
%s/cgi-sid/reqoid.py
and entering the values you're signed up with:
%s
Importantly you then have to enter your EXISTING password!

In either case please enter a few lines of comment including why you (still)
need access. Mentioning names of project and main collaboration partners
on-site may also be helpful to speed up our verification and renewal process.

Please contact the %s admins in case you should ever loose or forget your
password. The same applies if you suspect or know that someone may have gotten
hold of your login.

Regards,
The %s Admins
""" % (short_title, migoid_title, expire, user_email, auth_migoid_url,
            anon_migoid_url, id_lines, short_title, short_title)
    elif status == 'FORUMUPDATE':
        vgrid_name = args_list[0]
        author = args_list[1]
        url = args_list[2]
        header = "New post in %s %s forum on %s server" \
                 % (vgrid_name, configuration.site_vgrid_label,
                    configuration.short_title)
        txt += """This is an automated notification message from the %s server

User %s
posted a new message in the private %s forum. You may see the details at
%s
The main forum page includes a button to change your subscription state in
case you don't want to receive these notifications in the future.
""" % (configuration.short_title, author, vgrid_name, url)
    else:
        header = '%s Unknown message type' % configuration.short_title
        txt += 'unknown status'
    return (header, txt)


def send_instant_message(
    recipients,
    protocol,
    header,
    message,
    logger,
    configuration,
):
    """Send message to recipients by IM through daemon. Please note
    that this function will *never* return if no IM daemon is running.
    Thus it must be forked/threaded if further actions are pending!
    """

    im_in_path = configuration.im_notify_stdin

    # <BR> used as symbol for newline, because newlines can not
    # be sent to the named pipe im_in_path directly.
    # TODO: Is <BR> a good symbol?.

    message = message.replace('\n', '<BR>')
    message = 'SENDMESSAGE %s %s %s: %s' % (protocol, recipients,
                                            header, message)
    logger.info('sending %s to %s' % (message, im_in_path))
    try:

        # This will block if no process is listening to im input pipe!!

        im_in_fd = open(im_in_path, 'a')
        im_in_fd.write(message + '\n')
        logger.info('%s written to %s' % (message, im_in_path))
        im_in_fd.close()
        return True
    except Exception, err:
        logger.error('could not get exclusive access or write to %s: %s %s'
                     % (im_in_path, message, err))
        print 'could not get exclusive access or write to %s!'\
            % im_in_path
        return False


def send_email(
    recipients,
    subject,
    message,
    logger,
    configuration,
    files=[],
):
    """Send message to recipients by email:
    Force utf8 encoding to avoid accented characters appearing garbled
    """

    if recipients.find(', ') > -1:
        recipients_list = recipients.split(', ')
    else:
        recipients_list = [recipients]

    try:
        mime_msg = MIMEMultipart()
        mime_msg['From'] = configuration.smtp_sender
        mime_msg['To'] = recipients
        mime_msg['Reply-To'] = configuration.smtp_reply_to
        mime_msg['Date'] = formatdate(localtime=True)
        mime_msg['Subject'] = subject
        mime_msg.attach(MIMEText(force_utf8(message), "plain", "utf8"))

        for name in files:
            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(name, "rb").read())
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            'attachment; filename="%s"'
                            % os.path.basename(name))
            mime_msg.attach(part)
        logger.debug('sending email to %s:\n%s' % (recipients,
                                                   mime_msg.as_string()))
        server = smtplib.SMTP(configuration.smtp_server)
        server.set_debuglevel(0)
        errors = server.sendmail(configuration.smtp_sender,
                                 recipients_list, mime_msg.as_string())
        server.quit()
        if errors:
            logger.warning('Partial error(s) sending email: %s'
                           % errors)
            return False
        else:
            logger.debug('Email was sent to %s' % recipients)
            return True
    except Exception, err:
        logger.error('Sending email to %s through %s failed!: %s'
                     % (recipients, configuration.smtp_server,
                         str(err)))
        return False


def notify_user(
    jobdict,
    args_list,
    status,
    logger,
    statusfile,
    configuration,
):
    """Send notification messages about job to user. User settings are
    used if notification fields are left empty or set to 'SETTINGS'.
    Please note that this function may take a long time to deliver
    notifications, or even block forever if an IM is requested and no IM
    daemon is running. Thus it should be run in a separate thread or
    process if blocking is not allowed.
    Please take a look at notify_user_thread() if that is a requirement.
    """

    # Usage records: quickly hacked in here.
    # later, we might want a general plugin / hook interface

    # first of all, write out the usage record (if configured)

    ur_destination = configuration.usage_record_dir
    if ur_destination:

        logger.debug('XML Usage Record directory %s' % ur_destination)
        usage_record = UsageRecord(configuration, logger)
        usage_record.fill_from_dict(jobdict)

        # we use the job_id as a file name (should be unique)

        usage_record.write_xml(ur_destination + os.sep
                               + jobdict['JOB_ID'] + '.xml')

    jobid = jobdict['JOB_ID']
    for notify_line in jobdict['NOTIFY']:
        logger.debug('notify line: %s' % notify_line)
        (header, message) = create_notify_message(jobdict,
                                                  args_list,
                                                  status,
                                                  statusfile,
                                                  configuration)

        supported_protocols = ['jabber', 'msn', 'icq', 'aol', 'yahoo']
        notify_line_colon_split = notify_line.split(':', 1)

        if notify_line_colon_split[0].strip() in supported_protocols:
            protocol = notify_line_colon_split[0]
            recipients = notify_line_colon_split[1].strip()
            all_dest = []

            # Empty or

            if recipients.strip().upper() in ['SETTINGS', '']:

                # read from personal settings

                settings_dict = load_settings(jobdict['USER_CERT'],
                                              configuration)
                if not settings_dict\
                        or not settings_dict.has_key(protocol.upper()):
                    logger.info('Settings dict does not have %s key'
                                % protocol.upper())
                    continue
                all_dest = settings_dict[protocol.upper()]
            else:
                all_dest.append(recipients)
            for single_dest in all_dest:

                logger.debug('notifying %s about %s' % (single_dest,
                                                        jobid))

                # NOTE: Check removed because icq addresses are numbers and not "emails"
                # if not is_valid_simple_email(single_dest):
                # not a valid address (IM account names are on standard email format)
                # continue............................

                if send_instant_message(
                    single_dest,
                    protocol,
                    header,
                    message,
                    logger,
                    configuration,
                ):
                    logger.info('Instant message sent to %s' % single_dest
                                + ' protocol: %s telling that %s %s'
                                % (protocol, jobid,
                                    status))
                else:
                    logger.error('Instant message NOT sent to %s protocol %s jobid: %s'
                                 % (single_dest, protocol, jobid))
        else:
            notify_line_first_part = notify_line_colon_split[0].strip()
            all_dest = []
            if notify_line_first_part in email_keyword_list or \
                    notify_line_first_part == 'SETTINGS':
                logger.info(
                    "'%s' notify_line_first_part found in email_keyword_list"
                    % notify_line_first_part)
                recipients = notify_line.replace(
                    '%s:' % notify_line_first_part, '').strip()
                if recipients.strip().upper() in ['SETTINGS', '']:

                    # read from personal settings

                    settings_dict = load_settings(jobdict['USER_CERT'],
                                                  configuration)
                    if not settings_dict:
                        logger.info('Could not load settings_dict')
                        continue
                    if not settings_dict.has_key('EMAIL'):
                        logger.info('Settings dict does not have EMAIL key'
                                    )
                        continue

                    all_dest = settings_dict['EMAIL']
                else:
                    all_dest.append(recipients)
            elif is_valid_simple_email(notify_line):
                logger.info("fall back to valid plain email %s" % notify_line)
                all_dest.append(notify_line)
            else:
                logger.warning("No valid mail recipient for %s" % notify_line)
                continue

            # send mails

            for single_dest in all_dest:
                logger.info('email destination %s' % single_dest)

                # verify specified address is valid

                if not is_valid_simple_email(single_dest):
                    logger.info('%s is NOT a valid email address!'
                                % single_dest)

                    # not a valid email address

                    continue

                if send_email(single_dest, header, message, logger,
                              configuration):
                    logger.info('email sent to %s telling that %s %s'
                                % (single_dest, jobid, status))
                else:
                    logger.error('email NOT sent to %s, jobid: %s'
                                 % (single_dest, jobid))
    # logger.info("notify_user end")


def notify_user_wrap(jobdict, args_list, status, logger, statusfile,
                     configuration):
    """Wrap the sending of notification messages to user in try/except to
    catch and log any errors outside the fragile thread context.
    """
    try:
        notify_user(jobdict, args_list, status, logger, statusfile,
                    configuration)
    except Exception, exc:
        logger.error("notify_user failed: %s" % exc)


def notify_user_thread(
    jobdict,
    args_list,
    status,
    logger,
    statusfile,
    configuration,
):
    """Run notification in a separate thread to avoid delays or hangs
    in caller. Launches a new daemon thread to avoid waiting issues.
    We still must join thread if we want to assure delivery.
    """

    notify_thread = threading.Thread(target=notify_user_wrap, args=(
        jobdict,
        args_list,
        status,
        logger,
        statusfile,
        configuration,
    ))
    notify_thread.setDaemon(True)
    notify_thread.start()
    return notify_thread


def send_resource_create_request_mail(
    client_id,
    hosturl,
    pending_file,
    logger,
    configuration,
):
    """Send request for new resource to admins"""

    recipients = configuration.admin_email

    msg = "Sending the resource creation information for '%s' to '%s'"\
        % (hosturl, recipients)

    subject = '%s resource creation request on %s'\
        % (configuration.short_title, configuration.server_fqdn)
    txt = \
        """
Cert. ID: '%s'

Hosturl: '%s'

Configfile: '%s'

Resource creation command to run from mig/server/ directory:
./createresource.py '%s' '%s' '%s'
"""\
         % (
        client_id,
        hosturl,
        pending_file,
        hosturl,
        client_id,
        os.path.basename(pending_file),
    )

    status = send_email(recipients, subject, txt, logger, configuration)
    if status:
        msg += '\nEmail was sent to admins'
    else:
        msg += '\nEmail could not be sent to one or more recipients!'
    return (status, msg)


def parse_im_relay(path):
    """Parse path name and contents in order to generate
    message parameters for send_instant_message. This is
    used for IM relay support.
    """

    status = ''
    filename = os.path.basename(path)
    protocol = filename.lower().replace('.imrelay', '')
    (address, header, msg) = ('', '', '')
    try:

        # Parse message (address\nheader\nmsg)

        im_fd = open(path, 'r')
        address = im_fd.readline().strip()
        header = im_fd.readline().strip()
        msg = im_fd.read()
        im_fd.close()
        if not (protocol and address and header and msg):
            status += 'Invalid contents: %s;%s;%s;%s' % (protocol,
                                                         address, header, msg)
    except StandardError, err:
        status += 'IM relay parsing failed: %s' % err

    return (status, protocol, address, header, msg)
