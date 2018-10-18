#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# defaults - default constant values used in many locations
# Copyright (C) 2003-2018  The MiG Project lead by Brian Vinter
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


"""Default values for use in other modules"""

from string import ascii_lowercase, ascii_uppercase, digits

# IMPORTANT: do NOT import anything except native python modules/functions here
#            to avoid import loops

user_db_filename = 'MiG-users.db'

keyword_any = 'ANY'
keyword_all = 'ALL'
keyword_auto = 'AUTO'
keyword_never = 'NEVER'
keyword_none = 'NONE'
keyword_unchanged = 'UNCHANGED'
keyword_final = 'FINAL'
keyword_pending = 'PENDING'
keyword_owners = 'OWNERS'
keyword_members = 'MEMBERS'

default_vgrid = 'Generic'
any_vgrid = keyword_any
all_vgrids = keyword_all

all_jobs = keyword_all

any_protocol = keyword_any
any_state = keyword_any

cert_field_order = [
    ('country', 'C'),
    ('state', 'ST'),
    ('locality', 'L'),
    ('organization', 'O'),
    ('organizational_unit', 'OU'),
    ('full_name', 'CN'),
    ('email', 'emailAddress'),
]

sandbox_names = ['sandbox', 'oneclick', 'ps3live']

email_keyword_list = ['mail', 'email']

pending_states = ['PARSE', 'QUEUED', 'EXECUTING', 'RETRY', 'FROZEN']
final_states = ['FINISHED', 'CANCELED', 'EXPIRED', 'FAILED']

maxfill_fields = ['CPUTIME', 'NODECOUNT', 'CPUCOUNT', 'MEMORY', 'DISK']

mqueue_prefix = 'message_queues'
default_mqueue = 'default'
mqueue_empty = 'NO MESSAGES'

# User ID is email or hexlified version of full cert DN.
# Shortest email would have to be something like a@ku.dk
user_id_min_length = 7
user_id_max_length = 256
user_id_charset = ascii_uppercase + ascii_lowercase + digits + '_-@.'

# We hexlify 32 random bytes to get 64 character string
session_id_bytes = 32
session_id_length = session_id_bytes * 2
session_id_charset = digits + 'abcdef'

# 2FA secret tokens are 32 chars (implicitly from base32 charset)
twofactor_key_bytes = 32
# Size of random key generated in 2FA cookies and session life time
twofactor_cookie_bytes = 80
twofactor_cookie_ttl = 24 * 60 * 60

# Sharelink format helpers
# Let mode chars be aAbBcC ... xX (to make splitting evenly into 3 easy)
share_mode_charset = ''.join(['%s%s' % pair for pair in zip(
    ascii_lowercase[:-2], ascii_uppercase[:-2])])
# Let ID chars be aAbBcC ... zZ01..9 (to always yield URL friendly IDs
share_id_charset = ascii_lowercase + ascii_uppercase + digits


default_pager_entries = 25

default_http_port = 80
default_https_port = 443

cert_valid_days = 365
oid_valid_days = 365

auth_openid_mig_db = 'mod_auth_openid-mig-users.db'
auth_openid_ext_db = 'mod_auth_openid-ext-users.db'

exe_leader_name = "execution-leader"

htaccess_filename = '.htaccess'
welcome_filename = 'welcome.txt'
default_mrsl_filename = '.default.mrsl'
default_css_filename = '.default.css'
spell_dictionary_filename = '.personal_dictionary'
ssh_conf_dir = '.ssh'
davs_conf_dir = '.davs'
ftps_conf_dir = '.ftps'
seafile_conf_dir = '.seafile'
duplicati_conf_dir = '.duplicati'
job_output_dir = 'job_output'
transfer_output_dir = 'transfer_output'
cron_output_dir = 'cron_output'
authkeys_filename = 'authorized_keys'
authpasswords_filename = 'authorized_passwords'
authdigests_filename = 'authorized_digests'
settings_filename = 'settings'
widgets_filename = 'widgets'
profile_filename = 'userprofile'
twofactor_filename = 'twofactor'
duplicati_filename = 'duplicati'
freeze_meta_filename = 'meta.pck'
datatransfers_filename = 'transfers'
user_keys_dir = 'keys'
sharelinks_filename = 'sharelinks'
seafile_ro_dirname = 'seafile_readonly'
twofactor_key_name = 'twofactor_key'
# Trash really goes to this location but only accessible through link
trash_destdir = '.trash'
trash_linkname = 'Trash'

# The htaccess file prevents illegal http access to user files. We completely
# hide it to not confuse users and to prevent all modification. It is 'only'
# a matter of users not accidentally giving away file privacy, though.
# The .vgrid* dirs contain wsgi/cgi dirs with executable code, etc. and we
# can't let users edit them because it would result in arbitrary code execution
# holes.
#
# IMPORTANT: please use the invisible_{path,file,dir} helpers from shared.base
#            instead of using these variables directly.
_dot_vgrid = ['.vgrid%s' % i for i in ['wiki', 'scm', 'tracker', 'forum']]
_protected_dirs = [trash_destdir]
_user_invisible_dirs = _dot_vgrid + _protected_dirs
_user_invisible_files = [htaccess_filename]
_user_invisible_paths = _user_invisible_files + _user_invisible_dirs
_vgrid_xgi_scripts = ['.vgridscm/cgi-bin/hgweb.cgi',
                      '.vgridscm/wsgi-bin/hgweb.wsgi',
                      '.vgridtracker/cgi-bin/trac.cgi',
                      '.vgridtracker/wsgi-bin/trac.wsgi',
                      '.vgridwiki/cgi-bin/moin.cgi',
                      '.vgridwiki/wsgi-bin/moin.wsgi']

profile_img_max_kb = 128
profile_img_extensions = ['png', 'jpg']

max_software_entries = 40
max_environment_entries = 40
# This is an arbitrarily selected cap to prevent exhausting resources
max_freeze_files = 1048576
max_upload_files = 65535
max_upload_chunks = 10
# Checksum in 32kb blocks and default to first 32 MB
default_chunk_size = 32768
default_max_chunks = 1024

# 64M = 67108864
upload_block_size = 67108864
upload_tmp_dir = '.upload-cache'
# Please read the chunk note in wsgi handler before tuning this value above 1G!
# 256M = 268435456
download_block_size = 268435456
wwwpublic_alias = 'public'
public_archive_dir = 'archives'
public_archive_index = 'published-archive.html'

edit_lock_suffix = '.editor_lock__'
edit_lock_timeout = 600

# Valid trigger actions - with the first one as default action

valid_trigger_changes = ['created', 'modified', 'deleted']
valid_trigger_actions = ['submit', 'command'] + ['trigger-%s' % i for i in
                                                 valid_trigger_changes]
img_trigger_prefix = 'system_imagesettings'

workflows_log_name = 'workflow.log'
# 64M = 67108864
workflows_log_size = 67108864
workflows_log_cnt = 2

atjobs_name = 'atjobs'
crontab_name = 'crontab'
cron_log_name = 'cron.log'
# 64M = 67108864
cron_log_size = 67108864
cron_log_cnt = 2

# 64M = 67108864
transfers_log_size = 67108864
transfers_log_cnt = 2

dav_domain = "/"

# Interactive jobs use a password which should at least be hard to brute-force
# Yet the VNC server ignores all but the first 8 chars so it is no use with
# longer password unfortunately.
vnc_pw_len = 8

# TODO: change to something that doesn't interfere if filename contains spaces
# Seperator used in job src/dst file lines
src_dst_sep = " "

# Seperator used in file expansion - must be easily parsable by user scripts
file_dest_sep = "    ::    "

# For webdavs rfc compliance testing with litmus - use expected email format
litmus_id = 'litmus@nowhere.org'

# VGrid and resource request file name helpers
request_prefix = 'access-'
request_ext = '.req'

# CSRF helper for client scripts
CSRF_MINIMAL, CSRF_WARN = "MINIMAL", "WARN"
CSRF_MEDIUM, CSRF_FULL = "MEDIUM", "FULL"
csrf_token_header = 'HTTP_CSRF_TOKEN'

# form field
csrf_field = "_csrf"

# List of backend targets that may require a CSRF token to work
# Can be generated with the command:
# 0|~/mig > ./codegrep.py safe_handler|grep import|sort|awk '{ print $1; }'| \
#               sed 's@.*/functionality/\(.*\).py:from@\\"\1\\",@g'|xargs
csrf_backends = ["addresowner", "addvgridmember", "addvgridowner", "addvgridres", "addvgridtrigger", "autocreate", "chksum", "cleanallstores", "cleanexe", "cleanfe", "cleanstore", "cp", "createfreeze", "createre", "createvgrid", "datatransfer", "deletefreeze", "deletere", "delres", "editfile", "extcertaction", "extoidaction", "imagepreview", "jobaction", "jobfeasible", "jobobjsubmit", "jobschedule", "liveio", "mkdir", "mqueue", "mv", "pack", "rejectresreq", "rejectvgridreq", "reqcertaction", "reseditaction", "restartallexes", "restartallstores", "restartexe", "restartfe", "restartstore", "resubmit", "rmdir", "rm", "rmresowner", "rmvgridmember", "rmvgridowner", "rmvgridres", "rmvgridtrigger", "scripts", "sendrequestaction", "settingsaction", "sharelink", "sssadmin", "ssscreateimg", "stopallexes", "stopallstores", "stopexe", "stopfe", "stopstore", "submitfields", "submit", "tar", "testresupport", "textarea", "touch", "truncate", "unpack", "untar", "unzip", "updateresconfig", "updatevgrid", "uploadchunked", "upload", "vgridforum", "vgridsettings", "vmachines", "zip",
                 ]

# freeze archive flavor
# NOTE: order in states list is used to set default state for new archives
freeze_flavors = {
    'freeze': {'adminfreeze_title': 'Freeze Archive',
               'createfreeze_title': 'Create Freeze Archive',
               'showfreeze_title': 'Show Freeze Archive Details',
               'deletefreeze_title': 'Delete Freeze Archive',
               'states': [keyword_pending, keyword_final]},
    'phd': {'adminfreeze_title': 'PhD Thesis Archival',
            'createfreeze_title': 'Create Thesis Archive',
            'showfreeze_title': 'Show Thesis Archive Details',
            'deletefreeze_title': 'Delete Thesis Archive',
            'states': [keyword_pending, keyword_final]},
    'backup': {'adminfreeze_title': 'Backup Archival',
               'createfreeze_title': 'Create Backup Archive',
               'showfreeze_title': 'Show Backup Archive Details',
               'deletefreeze_title': 'Delete Backup Archive',
               'states': [keyword_pending, keyword_final]}
}

# Default value for ALL integer limits in vgrid settings
# NOTE: spamming more than 10 owners about reqs is rarely popular, but
# balancing participation management rights is tricky. Owners should at least
# be urged to consider security implications of allowing too many co-owners.
# TODO: split into two values and remove default limit on management rights?
default_vgrid_settings_limit = 10

# Seperator used in flat vgrid structure for read-only support
vgrid_nest_sep = ':'

# Password policy helpers
POLICY_NONE, POLICY_WEAK = "NONE", "WEAK"
POLICY_MEDIUM, POLICY_HIGH = "MEDIUM", "HIGH"
POLICY_CUSTOM = "CUSTOM"

# Prioritized protocol choices and internal values
duplicati_protocol_choices = [('SFTP', 'sftp'), ('FTPS', 'ftps'),
                              ('WebDAVS', 'davs')]
# Prioritized schedule backup frequency choices and json values
duplicati_schedule_choices = [('Daily', '1D'), ('Weekly', '1W'),
                              ('Monthly', '1M'), ('Never', '')]

# Session timeout in seconds for IO services,
io_session_timeout = {'davs': 60}


# Strong SSL/TLS ciphers and curves to allow in Apache and other SSL/TLS-based
# daemons (on Apache/OpenSSL format).
# NOTE: harden in line with Mozilla recommendations:
# https://wiki.mozilla.org/Security/Server_Side_TLS#Apache
# Use ciphers and order recommended for 'Intermediate compatibility' as a base
# to get a good balance between strength and legacy support. We further prune
# the list from Mozilla to explicitly disable a handful of possibly weak
# ciphers, not really needed to support all the common platforms (only still
# maintained ones).
# In short it makes sure TLSv1.2 and secure but light-weight elliptic curve
# ciphers are preferred and then gracefully falls back to only other secure
# ciphers.
# On older versions of OpenSSL, unavailable ciphers will be discarded
# automatically.
STRONG_TLS_CIPHERS = "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES:CAMELLIA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!SEED:!IDEA:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA:!DES-CBC3-SHA:!AES128-GCM-SHA256:!AES256-GCM-SHA384:!AES128-SHA256:!AES256-SHA256:!AES128-SHA:!AES256-SHA:!CAMELLIA256-SHA:!CAMELLIA128-SHA"
# TODO: enforce curve order in Apache (2.4.8+), too?
#       https://superuser.com/questions/964907/apache-and-ecc-curve-order
# TODO: add curve 'X25519' as first choice once we reach openssl-1.1?
STRONG_TLS_CURVES = "prime256v1:secp384r1:secp521r1"

# Strong SSH key-exchange (Kex), cipher and message auth code (MAC) settings to
# allow in OpenSSH and native Paramiko SFTP daemons (on OpenSSH format).
# NOTE: harden in line with Mozilla recommendations for modern versions:
# https://wiki.mozilla.org/Security/Guidelines/OpenSSH#Configuration
# Additional hardening based on https://github.com/arthepsy/ssh-audit
# Please note that the DH GroupX KexAlgorithms require OpenSSH 7.3+, but that
# older versions can relatively safely fall back to instead use the
# diffie-hellman-group-exchange-sha256 as long as the moduli tuning from
# https://infosec.mozilla.org/guidelines/openssh is applied.
# Tested to work with popular recent clients on the main platforms:
# OpenSSH-6.6.1+, LFTP-4.4.13+, FileZilla-3.24+, WinSCP-5.13.3+ and PuTTY-0.70+
# NOTE: CentOS-6 still comes with OpenSSH-5.3 without strong Kex+MAC support
# thus it's necessary to force legacy ssh to support any such clients.
STRONG_SSH_KEXALGOS = "curve25519-sha256@libssh.org,diffie-hellman-group18-sha512,diffie-hellman-group14-sha256,diffie-hellman-group16-sha512"
STRONG_SSH_LEGACY_KEXALGOS = "curve25519-sha256@libssh.org,diffie-hellman-group-exchange-sha256"
STRONG_SSH_CIPHERS = "chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr"
# NOTE: strong cipher support go way back - just reuse
STRONG_SSH_LEGACY_CIPHERS = STRONG_SSH_CIPHERS
STRONG_SSH_MACS = "hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,umac-128-etm@openssh.com"
# NOTE: extend strong MACS with the best possible alterantives on old paramiko
#       to avoid falling back to really bad ones
STRONG_SSH_LEGACY_MACS = "%s,hmac-sha2-512,hmac-sha2-256" % STRONG_SSH_MACS

# A pattern to match usernames unambiguously identifying cracking attempts
CRACK_USERNAME_REGEX = '(root|bin|daemon|adm|admin|administrator|lp|operator|ftp|irc|nobody|sys|pi|guest|www|www-data|mysql|postgres|oracle|mongodb|redis|hadoop|cpanel|plesk|tomcat|exim|postfix|sendmail|mailnull|postmaster|mail|news|teamspeak|git|svn|cvs|user|ftpuser|ubuntu|supervisor|csgoserver|device|deploy|test|1234|0101|0)'
