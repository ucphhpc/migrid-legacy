#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# userscriptgen - Generator backend for user scripts
# Copyright (C) 2003-2015  The MiG Project lead by Brian Vinter
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

# TODO: finish generator for automatic testing of scripts
# TODO: filter exit code from cgi output and use in own exit code?

# TODO: mig-ls.* -r fib.out incorrectly lists entire home recursively
# TODO: ls -r is not recursive -> use -R!

"""Generate MiG user scripts for the specified programming
languages. Called without arguments the generator creates scripts
for all supported languages. If one or more languages are supplied
as arguments, only those languages will be generated.
"""

import sys
import getopt

# Generator version (automagically updated by svn)

__version__ = '$Revision$'

# Save original __version__ before truncate with wild card import

_userscript_version = __version__
from publicscriptgen import *
_publicscript_version = __version__
__version__ = '%s,%s' % (_userscript_version, _publicscript_version)

# ######################################
# Script generator specific functions #
# ######################################
# Generator usage


def usage():
    print 'Usage: userscriptgen.py OPTIONS [LANGUAGE ... ]'
    print 'Where OPTIONS include:'
    print ' -c CURL_CMD\t: Use curl from CURL_CMD'
    print ' -d DST_DIR\t: write scripts to DST_DIR'
    print ' -h\t\t: Print this help'
    print ' -l\t\t: Do not generate shared library module'
    print ' -p PYTHON_CMD\t: Use PYTHON_CMD as python interpreter'
    print ' -s SH_CMD\t: Use SH_CMD as sh interpreter'
    print ' -t\t\t: Generate self testing script'
    print ' -v\t\t: Verbose output'
    print ' -V\t\t: Show version'


def version():
    print 'MiG User Script Generator: %s' % __version__


def version_function(lang):
    s = ''
    s += begin_function(lang, 'version', [], 'Show version details')
    if lang == 'sh':
        s += "    echo 'MiG User Scripts: %s'" % __version__
    elif lang == 'python':
        s += "    print 'MiG User Scripts: %s'" % __version__
    s += end_function(lang, 'version')

    return s


# ##########################
# Script helper functions #
# ##########################


def shared_usage_function(op, lang, extension):
    """General wrapper for the specific usage functions.
    Simply rewrites first arg to function name."""

    return eval('%s_usage_function' % op)(lang, extension)


def cancel_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] JOBID [JOBID ...]'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def cat_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] FILE [FILE ...]'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def cp_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] SRC [SRC...] DST'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def doc_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] [TOPIC ...]' % (mig_prefix,
            op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def filemetaio_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] ACTION PATH [ARG ...]' % (mig_prefix,
            op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    action_usage_string = 'ACTION\t\tlist : List PATH directory meta-data entries'
    action_usage_string2 = '\t\tget_dir : Get PATH directory meta-data for extension=EXT'
    action_usage_string3 = '\t\tget_file : Get meta-data for file PATH'
    action_usage_string4 = '\t\tput_dir : Set PATH directory meta-data for extension=EXT'
    action_usage_string5 = '\t\tput_file : Set meta-data for file PATH'
    action_usage_string6 = '\t\tremove_dir : Remove PATH directory meta-data for extension=[EXT]'
    image_usage_string = '-i\t\tDisplay image meta-data'
    if lang == 'sh':
        s += '\n    echo "%s"' % action_usage_string
        s += '\n    echo "%s"' % action_usage_string2
        s += '\n    echo "%s"' % action_usage_string3
        s += '\n    echo "%s"' % action_usage_string4
        s += '\n    echo "%s"' % action_usage_string5
        s += '\n    echo "%s"' % action_usage_string6
    elif lang == 'python':
        s += '\n    print "%s"' % action_usage_string
        s += '\n    print "%s"' % action_usage_string2
        s += '\n    print "%s"' % action_usage_string3
        s += '\n    print "%s"' % action_usage_string4
        s += '\n    print "%s"' % action_usage_string5
        s += '\n    print "%s"' % action_usage_string6
    s += end_function(lang, 'usage')

    return s


def get_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] FILE [FILE ...] FILE'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    recursive_usage_string = '-r\t\tact recursively'
    if lang == 'sh':
        s += '\n    echo "%s"' % recursive_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % recursive_usage_string

    s += end_function(lang, 'usage')

    return s


def head_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] FILE [FILE ...]'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    lines_usage_string = '-n N\t\tShow first N lines of the file(s)'
    if lang == 'sh':
        s += '\n    echo "%s"' % lines_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % lines_usage_string
    s += end_function(lang, 'usage')

    return s


def jobaction_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] ACTION JOBID [JOBID ...]'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def liveio_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] ACTION JOBID SRC [SRC ...] DST' % \
                (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def ls_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] [FILE ...]' % (mig_prefix,
            op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    all_usage_string = "-a\t\tDo not hide entries starting with '.'"
    long_usage_string = '-l\t\tDisplay long format'
    recursive_usage_string = '-r\t\tact recursively'
    if lang == 'sh':
        s += '\n    echo "%s"' % all_usage_string
        s += '\n    echo "%s"' % long_usage_string
        s += '\n    echo "%s"' % recursive_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % all_usage_string
        s += '\n    print "%s"' % long_usage_string
        s += '\n    print "%s"' % recursive_usage_string

    s += end_function(lang, 'usage')

    return s


def mkdir_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] DIRECTORY [DIRECTORY ...]'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    parents_usage_string = '-p\t\tmake parent directories as needed'
    if lang == 'sh':
        s += '\n    echo "%s"' % parents_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % parents_usage_string
    s += end_function(lang, 'usage')

    return s


def mqueue_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] ACTION QUEUE [MSG]' % \
                (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def mv_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] SRC [SRC...] DST'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def put_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] FILE [FILE ...] FILE' % (mig_prefix,
            op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)

    package_usage_string = \
        '-p\t\tSubmit mRSL files (also in packages if -x is specified) after upload'
    recursive_usage_string = '-r\t\tact recursively'
    extract_usage_string = \
        '-x\t\tExtract package (.zip etc) after upload'
    if lang == 'sh':
        s += '\n    echo "%s"' % package_usage_string
        s += '\n    echo "%s"' % recursive_usage_string
        s += '\n    echo "%s"' % extract_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % package_usage_string
        s += '\n    print "%s"' % recursive_usage_string
        s += '\n    print "%s"' % extract_usage_string

    s += end_function(lang, 'usage')

    return s


def read_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] START END SRC DST'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def resubmit_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] JOBID [JOBID ...]' % (mig_prefix, op,
            extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def rm_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] FILE [FILE ...]'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    recursive_usage_string = '-r\t\tact recursively'
    if lang == 'sh':
        s += '\n    echo "%s"' % recursive_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % recursive_usage_string
    s += end_function(lang, 'usage')

    return s


def rmdir_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] DIRECTORY [DIRECTORY ...]'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    parents_usage_string = '-p\t\tremove parent directories as needed'
    if lang == 'sh':
        s += '\n    echo "%s"' % parents_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % parents_usage_string

    s += end_function(lang, 'usage')

    return s


def stat_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] FILE [...]' % (mig_prefix,
            op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def status_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] [JOBID ...]' % (mig_prefix,
            op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    max_jobs_usage_string = '-m M\t\tShow status for at most M jobs'
    sort_jobs_usage_string = '-S\t\tSort jobs by modification time'
    if lang == 'sh':
        s += '\n    echo "%s"' % max_jobs_usage_string
        s += '\n    echo "%s"' % sort_jobs_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % max_jobs_usage_string
        s += '\n    print "%s"' % sort_jobs_usage_string

    s += end_function(lang, 'usage')

    return s


def submit_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] FILE [FILE ...]' % (mig_prefix, op,
            extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def tail_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] FILE [FILE ...]'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    lines_usage_string = '-n N\t\tShow last N lines of the file(s)'
    if lang == 'sh':
        s += '\n    echo "%s"' % lines_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % lines_usage_string
    s += end_function(lang, 'usage')

    return s


def test_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] [OPERATION ...]'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def touch_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] [FILE ...]' % (mig_prefix,
            op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def truncate_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] FILE [FILE ...]'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    lines_usage_string = '-n N\t\tTruncate file(s) to at most N bytes'
    if lang == 'sh':
        s += '\n    echo "%s"' % lines_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % lines_usage_string
    s += end_function(lang, 'usage')

    return s


def unzip_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] SRC [SRC...] DST'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def wc_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] FILE [FILE ...]'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    bytes_usage_string = '-b N\t\tShow byte count'
    lines_usage_string = '-l N\t\tShow line count'
    words_usage_string = '-w N\t\tShow word count'
    if lang == 'sh':
        s += '\n    echo "%s"' % bytes_usage_string
        s += '\n    echo "%s"' % lines_usage_string
        s += '\n    echo "%s"' % words_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % bytes_usage_string
        s += '\n    print "%s"' % lines_usage_string
        s += '\n    print "%s"' % words_usage_string
    s += end_function(lang, 'usage')

    return s


def write_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] START END SRC DST'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    s += end_function(lang, 'usage')

    return s


def zip_usage_function(lang, extension):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('_usage_function', '')

    usage_str = 'Usage: %s%s.%s [OPTIONS] SRC [SRC...] DST'\
         % (mig_prefix, op, extension)
    s = ''
    s += begin_function(lang, 'usage', [], 'Usage help for %s' % op)
    s += basic_usage_options(usage_str, lang)
    curdir_usage_string = '-w PATH\t\tUse PATH as remote working directory'
    if lang == 'sh':
        s += '\n    echo "%s"' % curdir_usage_string
    elif lang == 'python':
        s += '\n    print "%s"' % curdir_usage_string
    s += end_function(lang, 'usage')

    return s


# ##########################
# Communication functions #
# ##########################


def shared_op_function(op, lang, curl_cmd):
    """General wrapper for the specific op functions.
    Simply rewrites first arg to function name."""

    return eval('%s_function' % op)(lang, curl_cmd)


def cancel_function(lang, curl_cmd, curl_flags=''):
    relative_url = '"cgi-bin/jobaction.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;action=cancel;$job_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;action=cancel;%s' % (server_flags, job_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'cancel_job', ['job_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'job_list', 'job_id')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'cancel_job')
    return s


def cat_function(lang, curl_cmd, curl_flags='--compressed'):
    relative_url = '"cgi-bin/cat.py"'
    query = '""'
    if lang == 'sh':
        post_data = '"output_format=txt;flags=$server_flags;$path_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;%s' % (server_flags, path_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'cat_file', ['path_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'cat_file')
    return s


def cp_function(lang, curl_cmd, curl_flags='--compressed'):
    """Call the corresponding cgi script with the string 'src_list' as argument. Thus
    the variable 'src_list' should be on the form
    \"src=pattern1[;src=pattern2[ ... ]]\"
    This may seem a bit awkward but it's difficult to do in a better way when
    begin_function() doesn't support variable length or array args.
    """

    relative_url = '"cgi-bin/cp.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;dst=$dst;$src_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;dst=%s;%s' % (server_flags, dst, src_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'cp_file', ['src_list', 'dst'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'src_list', 'src')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'cp_file')
    return s


def doc_function(lang, curl_cmd, curl_flags='--compressed'):
    relative_url = '"cgi-bin/docs.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;search=$search;show=$show"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;search=%s;show=%s' % (server_flags, search, show)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'show_doc', ['search', 'show'],
                        'Execute the corresponding server operation')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'show_doc')
    return s


def expand_function(lang, curl_cmd, curl_flags='--compressed'):
    """Call the expand cgi script with the string 'path_list' as argument. Thus
    the variable 'path_list' should be on the form
    \"path=pattern1[;path=pattern2[ ... ]]\"
    This may seem a bit awkward but it's difficult to do in a better way when
    begin_function() doesn't support variable length or array args.
    """

    relative_url = '"cgi-bin/expand.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;$path_list;with_dest=$destinations"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;%s;with_dest=%s' % (server_flags, path_list, destinations)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'expand_name', ['path_list',
                        'server_flags', 'destinations'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'expand_name')
    return s


def filemetaio_function(lang, curl_cmd, curl_flags='--compressed'):
   
    relative_url = '"cgi-bin/filemetaio.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;action=$action;path=$path;$arg_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;action=%s;path=%s;%s' % (server_flags, action, path, arg_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'filemetaio', ['action', 'path', 'arg_list'],
                        'Execute the corresponding server operation')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'filemetaio')
    return s


def get_function(lang, curl_cmd, curl_flags='--compressed --create-dirs'
                 ):
    post_data = '""'
    query = '""'
    if lang == 'sh':

        # TODO: should we handle below double slash problem here, too?

        relative_url = '"cert_redirect/$src_path"'
        curl_target = '"--output $dst_path"'
    elif lang == 'python':

        # Apache chokes on possible double slash in url and that causes
        # fatal errors in migfs-fuse - remove it from src_path.

        relative_url = '"cert_redirect/%s" % src_path.lstrip("/")'
        curl_target = "'--output %s' % dst_path"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'get_file', ['src_path', 'dst_path'],
                        'Execute the corresponding server operation')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        curl_target,
        )
    s += end_function(lang, 'get_file')
    return s


def head_function(lang, curl_cmd, curl_flags='--compressed'):
    relative_url = '"cgi-bin/head.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;$path_list;lines=$lines"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;%s;lines=%s' % (server_flags, path_list, lines)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'head_file', ['lines', 'path_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'head_file')
    return s


def jobaction_function(lang, curl_cmd, curl_flags=''):
    relative_url = '"cgi-bin/jobaction.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;action=$action;$job_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;action=%s;%s' % (server_flags, action, job_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'job_action', ['action', 'job_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'job_list', 'job_id')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'job_action')
    return s


def liveio_function(lang, curl_cmd, curl_flags='--compressed'):
    relative_url = '"cgi-bin/liveio.py"'
    query = '""'
    if lang == 'sh':
        post_data = '"output_format=txt;flags=$server_flags;action=$action;job_id=$job_id;$src_list;dst=$dst"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;action=%s;job_id=%s;%s;dst=%s' % (server_flags, action, job_id, src_list, dst)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'job_liveio', ['action', 'job_id', 'src_list', 'dst'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'src_list', 'src')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'job_liveio')
    return s


def ls_function(lang, curl_cmd, curl_flags='--compressed'):
    """Call the ls cgi script with the string 'path_list' as argument. Thus
    the variable 'path_list' should be on the form
    \"path=pattern1[;path=pattern2[ ... ]]\"
    This may seem a bit awkward but it's difficult to do in a better way when
    begin_function() doesn't support variable length or array args.
    """

    relative_url = '"cgi-bin/ls.py"'
    query = '""'
    if lang == 'sh':
        post_data = '"output_format=txt;flags=$server_flags;$path_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;%s' % (server_flags, path_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'ls_file', ['path_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'ls_file')
    return s


def mkdir_function(lang, curl_cmd, curl_flags=''):
    """Call the mkdir cgi script with 'path' as argument."""

    relative_url = '"cgi-bin/mkdir.py"'
    query = '""'
    if lang == 'sh':
        post_data = '"output_format=txt;flags=$server_flags;$path_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;%s' % (server_flags, path_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'mk_dir', ['path_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'mk_dir')
    return s


def mqueue_function(lang, curl_cmd, curl_flags='--compressed'):
    relative_url = '"cgi-bin/mqueue.py"'
    query = '""'
    if lang == 'sh':
        post_data = '"output_format=txt;flags=$server_flags;action=$action;queue=$queue;msg=$msg"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;action=%s;queue=%s;msg=%s' % (server_flags, action, queue, msg)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'job_mqueue', ['action', 'queue', 'msg'],
                        'Execute the corresponding server operation')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'job_mqueue')
    return s


def mv_function(lang, curl_cmd, curl_flags='--compressed'):
    """Call the corresponding cgi script with the string 'src_list' as argument. Thus
    the variable 'src_list' should be on the form
    \"src=pattern1[;src=pattern2[ ... ]]\"
    This may seem a bit awkward but it's difficult to do in a better way when
    begin_function() doesn't support variable length or array args.
    """

    relative_url = '"cgi-bin/mv.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;dst=$dst;$src_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;dst=%s;%s' % (server_flags, dst, src_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'mv_file', ['src_list', 'dst'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'src_list', 'src')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'mv_file')
    return s


def put_function(lang, curl_cmd, curl_flags='--compressed'):
    post_data = '""'
    query = '""'
    if lang == 'sh':

        # TODO: should we handle below double slash problem here, too?

        relative_url = '"$dst_path"'
        curl_target = \
            '"--upload-file $src_path --header $content_type -X CERTPUT"'
    elif lang == 'python':

        # Apache chokes on possible double slash in url and that causes
        # fatal errors in migfs-fuse - remove it from src_path.

        relative_url = '"%s" % dst_path.lstrip("/")'
        curl_target = \
            "'--upload-file %s --header %s -X CERTPUT' % (src_path, content_type)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'put_file', ['src_path', 'dst_path',
                        'submit_mrsl', 'extract_package'],
                        'Execute the corresponding server operation')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    if lang == 'sh':
        s += \
            """
    content_type="''"
    if [ $submit_mrsl -eq 1 ] && [ $extract_package -eq 1 ]; then
        content_type='Content-Type:submitandextract'
    elif [ $submit_mrsl -eq 1 ]; then
        content_type='Content-Type:submitmrsl'
    elif [ $extract_package -eq 1 ]; then
        content_type='Content-Type:extractpackage'
    fi
"""
    elif lang == 'python':
        s += \
            """
    content_type = "''"
    if submit_mrsl and extract_package:
        content_type = 'Content-Type:submitandextract'
    elif submit_mrsl:
        content_type = 'Content-Type:submitmrsl'
    elif extract_package:
        content_type = 'Content-Type:extractpackage'
"""
    else:
        print 'Error: %s not supported!' % lang
        return ''
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        curl_target,
        )
    s += end_function(lang, 'put_file')
    return s


def read_function(lang, curl_cmd, curl_flags='--compressed'):
    relative_url = '"cgi-bin/rangefileaccess.py"'
    post_data = '""'
    if lang == 'sh':
        query = \
            '"?output_format=txt;flags=$server_flags;file_startpos=$first;file_endpos=$last;path=$src_path"'
        curl_target = '"--output $dst_path"'
    elif lang == 'python':
        query = \
            "'?output_format=txt;flags=%s;file_startpos=%s;file_endpos=%s;path=%s' % (server_flags, first, last, src_path)"
        curl_target = "'--output %s' % dst_path"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'read_file', ['first', 'last', 'src_path'
                        , 'dst_path'],
                        'Execute the corresponding server operation')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        curl_target,
        )
    s += end_function(lang, 'read_file')
    return s


def resubmit_function(lang, curl_cmd, curl_flags=''):
    relative_url = '"cgi-bin/resubmit.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;$job_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;%s' % (server_flags, job_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'resubmit_job', ['job_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'job_list', 'job_id')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'resubmit_job')
    return s


def rm_function(lang, curl_cmd, curl_flags=''):
    """Call the rm cgi script with the string 'path_list' as argument. Thus
    the variable 'path_list' should be on the form
    \"path=pattern1[;path=pattern2[ ... ]]\"
    This may seem a bit awkward but it's difficult to do in a better way when
    begin_function() doesn't support variable length or array args.
    """

    relative_url = '"cgi-bin/rm.py"'
    query = '""'
    if lang == 'sh':
        post_data = '"output_format=txt;flags=$server_flags;$path_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;%s' % (server_flags, path_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'rm_file', ['path_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'rm_file')
    return s


def rmdir_function(lang, curl_cmd, curl_flags=''):
    """Call the rmdir cgi script with 'path' as argument."""

    relative_url = '"cgi-bin/rmdir.py"'
    query = '""'
    if lang == 'sh':
        post_data = '"output_format=txt;flags=$server_flags;$path_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;%s' % (server_flags, path_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'rm_dir', ['path_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'rm_dir')
    return s


def stat_function(lang, curl_cmd, curl_flags='--compressed'):
    """Call the corresponding cgi script with the string 'path_list' as argument. Thus
    the variable 'path_list' should be on the form
    \"path=pattern1[;path=pattern2[ ... ]]\"
    This may seem a bit awkward but it's difficult to do in a better way when
    begin_function() doesn't support variable length or array args.
    """

    relative_url = '"cgi-bin/statpath.py"'
    query = '""'
    if lang == 'sh':
        post_data = '"output_format=txt;flags=$server_flags;$path_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;%s' % (server_flags, path_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'stat_file', ['path_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'stat_file')
    return s


def status_function(lang, curl_cmd, curl_flags='--compressed'):
    relative_url = '"cgi-bin/jobstatus.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;max_jobs=$max_job_count;$job_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;max_jobs=%s;%s' % (server_flags, max_job_count, job_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'job_status', ['job_list', 'max_job_count'
                        ], 'Execute the corresponding server operation')
    s += format_list(lang, 'job_list', 'job_id')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'job_status')
    return s


def submit_function(lang, curl_cmd, curl_flags=''):

    # Simply use Put function

    s = put_function(lang, curl_cmd, curl_flags)
    return s.replace('put_file', 'submit_file')


def tail_function(lang, curl_cmd, curl_flags='--compressed'):
    relative_url = '"cgi-bin/tail.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;lines=$lines;$path_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;lines=%s;%s' % (server_flags, lines, path_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'tail_file', ['lines', 'path_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'tail_file')
    return s


def test_function(lang, curl_cmd, curl_flags=''):

    # TODO: pass original -c and -s options on to tested scripts

    s = ''
    s += begin_function(lang, 'test_op', ['op'],
                        'Execute simple function tests')
    if lang == 'sh':
        s += """
    valid_ops=(%(valid_ops)s)
    mig_prefix='%(mig_prefix)s'
    script_ext='sh'
""" % {'valid_ops': ' '.join(script_ops), 'mig_prefix': mig_prefix}
        s += \
            """
    valid=0
    for valid_op in ${valid_ops[*]}; do
        if [ $op = $valid_op ]; then
            valid=1
            break
        fi
    done

    if [ $valid -eq 0 ]; then
        echo \"Ignoring test of invalid operation: $op\"
        return 1
    fi
       
    path_prefix=`dirname $0`
    echo \"running $op test(s)\"
    cmd=\"${path_prefix}/${mig_prefix}${op}.${script_ext}\"
    put_cmd=\"${path_prefix}/${mig_prefix}put.${script_ext}\"
    submit_cmd=\"${path_prefix}/${mig_prefix}submit.${script_ext}\"
    ls_cmd=\"${path_prefix}/${mig_prefix}ls.${script_ext}\"
    zip_cmd=\"${path_prefix}/${mig_prefix}zip.${script_ext}\"
    rm_cmd=\"${path_prefix}/${mig_prefix}rm.${script_ext}\"
    declare -a cmd_args
    declare -a verify_cmds
    case $op in
        'cancel')
            pre_cmds[1]=\"${submit_cmd} mig-test.mRSL\"
            cmd_args[1]='DUMMY_JOB_ID'
            ;;
        'cat')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt'
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            ;;
        'cp')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt mig-test-new.txt'
            post_cmds[1]=\"${rm_cmd} mig-test.txt mig-test-new.txt\"
            ;;
        'doc')
            cmd_args[1]=''
            ;;
        'get')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt .'
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            ;;
        'head')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt'
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            ;;
        'jobaction')
            pre_cmds[1]=\"${submit_cmd} mig-test.mRSL\"
            cmd_args[1]='cancel DUMMY_JOB_ID'
            ;;
        'ls')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt'
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            ;;
        'mkdir')
            pre_cmds[1]=\"${rm_cmd} -r mig-test-dir\"
            cmd_args[1]='mig-test-dir'
            verify_cmds[1]=\"$path_prefix/migls.sh mig-test-dir\"
            post_cmds[1]=\"${rm_cmd} mig-test-dir\"
            ;;
        'mv')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt mig-test-new.txt'
            post_cmds[1]=\"${rm_cmd} mig-test-new.txt\"
            ;;
        'mqueue')
            cmd_args[1]='show default'
            ;;
        'put')
            pre_cmds[1]=\"${rm_cmd} mig-test.txt\"
            cmd_args[1]='mig-test.txt .'
            verify_cmds[1]=\"$path_prefix/migls.sh mig-test.txt\"
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            cmd_args[2]='mig-test.t*t mig-test.txt'
            verify_cmds[2]=\"${rm_cmd} mig-test.txt\"
            cmd_args[3]='mig-test.txt mig-test.txt'
            verify_cmds[3]=\"${rm_cmd} mig-test.txt\"
            cmd_args[4]='mig-test.txt mig-remote-test.txt'
            verify_cmds[4]=\"${rm_cmd} mig-remote-test.txt\"
            cmd_args[5]='mig-test.txt mig-test-dir/'
            verify_cmds[5]=\"${rm_cmd} mig-test-dir/mig-test.txt\"
            cmd_args[6]='mig-test.txt mig-test-dir/mig-remote-test.txt'
            verify_cmds[6]=\"${rm_cmd} mig-test-dir/mig-remote-test.txt\"

            # Disabled since put doesn't support wildcards in destination (yet?)
            # cmd_args[7]='mig-test.txt 'mig-test-d*/''
            # cmd_args[8]='mig-test.txt 'mig-test-d*/mig-remote-test.txt''
            # verify_cmds[7]=\"${rm_cmd} mig-test-dir/mig-remote-test.txt\"
            # verify_cmds[8]=\"${rm_cmd} mig-test-dir/mig-remote-test.txt\"
            ;;
        'read')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='0 16 mig-test.txt -'
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            ;;
        'rm')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt'
            verify_cmds[1]=\"$path_prefix/migls.sh mig-test.txt\"
            ;;
        'rmdir')
            pre_cmds=[1]\"$path_prefix/migmkdir.sh mig-test-dir\"
            cmd_args[1]='mig-test-dir'
            verify_cmds[1]=\"$path_prefix/migls.sh mig-test-dir\"
            post_cmds=[1]\"${rm_cmd} -r mig-test-dir\"
            ;;
        'stat')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt'
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            ;;
        'status')
            cmd_args[1]=''
            ;;
        'submit')
            cmd_args[1]='mig-test.mRSL'
            ;;
        'tail')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt'
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            ;;
        'touch')
            pre_cmds[1]=\"${rm_cmd} mig-test.txt\"
            cmd_args[1]='mig-test.txt'
            verify_cmds[1]=\"$path_prefix/migls.sh mig-test.txt\"
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            ;;
        'truncate')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt'
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            ;;
        'unzip')
            pre_cmds[1]=\"${zip_cmd} welcome.txt mig-test.zip\"
            cmd_args[1]='mig-test.zip mig-test.txt'
            verify_cmds[1]=\"$path_prefix/migls.sh mig-test.txt\"
            post_cmds[1]=\"${rm_cmd} mig-test.txt mig-test.zip\"
            ;;
        'wc')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt'
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            ;;
        'write')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='4 8 mig-test.txt mig-test.txt'
            post_cmds[1]=\"${rm_cmd} mig-test.txt\"
            ;;
        'zip')
            pre_cmds[1]=\"${put_cmd} mig-test.txt .\"
            cmd_args[1]='mig-test.txt mig-test.zip'
            verify_cmds[1]=\"$path_prefix/migls.sh mig-test.zip\"
            post_cmds[1]=\"${rm_cmd} mig-test.txt mig-test.zip\"
            ;;
        *)
            echo \"No test available for $op!\"
            return 1
            ;;
    esac


    index=1
    for args in \"${cmd_args[@]}\"; do
        echo \"test $index: $cmd $args\"
        pre=\"${pre_cmds[index]}\"
        if [ -n \"$pre\" ]; then
            echo \"setting up with: $pre\"
            $pre >& /dev/null
        fi
        ./$cmd $args >& /dev/null
        ret=$?
        if [ $ret -eq 0 ]; then
            echo \"   $op test $index SUCCEEDED\"
        else
            echo \"   $op test $index FAILED!\"
        fi
        verify=\"${verify_cmds[index]}\"
        if [ -n \"$verify\" ]; then
            echo \"verifying with: $verify\"
            $verify
        fi
        post=\"${post_cmds[index]}\"
        if [ -n \"$post\" ]; then
            echo \"cleaning up with: $post\"
            $post >& /dev/null
        fi
        index=$((index+1))
    done
    return $ret
"""
    elif lang == 'python':
        s += """
    valid_ops = %(valid_ops)s
    mig_prefix = '%(mig_prefix)s'
    script_ext = 'py'
""" % {'valid_ops': script_ops, 'mig_prefix': mig_prefix}
        s += """
    if not op in valid_ops:
        print 'Ignoring test of invalid operation: %s' % op
        return 1
       
    path_prefix = os.path.dirname(sys.argv[0])
    print 'running %s test' % op
    cmd = os.path.join(path_prefix, mig_prefix + op + '.' + script_ext)
    pre_cmds = []
    cmd_args = []
    post_cmds = []
    verify_cmds = []
    submit_cmd = os.path.join(path_prefix, mig_prefix + 'submit.' + script_ext) 
    put_cmd = os.path.join(path_prefix, mig_prefix + 'put.' + script_ext) 
    ls_cmd = os.path.join(path_prefix, mig_prefix + 'ls.' + script_ext) 
    zip_cmd = os.path.join(path_prefix, mig_prefix + 'zip.' + script_ext) 
    rm_cmd = os.path.join(path_prefix, mig_prefix + 'rm.' + script_ext) 
    if op in ('cat', 'head', 'ls', 'stat', 'tail', 'wc'):
            pre_cmds.append('%s mig-test.txt .' % put_cmd)
            cmd_args.append('mig-test.txt')
            post_cmds.append('%s mig-test.txt' % rm_cmd)
    elif op == 'cp':
            pre_cmds.append('%s mig-test.txt .' % put_cmd)
            cmd_args.append('mig-test.txt mig-test-new.txt')
            post_cmds.append('%s mig-test.txt mig-test-new.txt' % rm_cmd)
    elif op == 'get':
            pre_cmds.append('%s mig-test.txt .' % put_cmd)
            cmd_args.append('mig-test.txt .')
            post_cmds.append('%s mig-test.txt' % rm_cmd)
    elif op == 'cancel':
            pre_cmds.append('%s mig-test.mRSL' % submit_cmd)
            cmd_args.append('DUMMY_JOB_ID')
    elif op in ('doc', 'status'):
            cmd_args.append('')
    elif op == 'jobaction':
            pre_cmds.append('%s mig-test.mRSL' % submit_cmd)
            cmd_args.append('cancel DUMMY_JOB_ID')
    elif op == 'mkdir':
            pre_cmds.append('%s -r mig-test-dir' % rm_cmd)
            cmd_args.append('mig-test-dir')
            verify_cmds.append('%s mig-test-dir' % ls_cmd)
            post_cmds.append('%s -r mig-test-dir' % rm_cmd)
    elif op == 'mv':
            pre_cmds.append('%s mig-test.txt .' % put_cmd)
            cmd_args.append('mig-test.txt mig-test-new.txt')
            post_cmds.append('%s mig-test-new.txt' % rm_cmd)
    elif op == 'mqueue':
            cmd_args.append('show default')
    elif op == 'put':
            pre_cmds.append('%s mig-test.txt' % rm_cmd)
            cmd_args.append('mig-test.txt .')
            verify_cmds.append('%s mig-test.txt' % ls_cmd)
            post_cmds.append('%s mig-test.txt' % rm_cmd)
            cmd_args.append('mig-test.t*t mig-test.txt')
            verify_cmds.append('%s mig-test.txt' % rm_cmd)
            cmd_args.append('mig-test.txt mig-test.txt')
            verify_cmds.append('%s mig-test.txt' % rm_cmd)
            cmd_args.append('mig-test.txt mig-test.txt')
            verify_cmds.append('%s mig-test.txt' % rm_cmd)
            cmd_args.append('mig-test.txt mig-remote-test.txt')
            verify_cmds.append('%s mig-remote-test.txt' % rm_cmd)
            cmd_args.append('mig-test.txt mig-test-dir/')
            verify_cmds.append('%s mig-test-dir/mig-test.txt' % rm_cmd)
            cmd_args.append('mig-test.txt mig-test-dir/mig-remote-test.txt')
            verify_cmds.append('%s mig-test-dir/mig-remote-test.txt' % rm_cmd)

            # Disabled since put doesn't support wildcards in destination (yet?)
            # cmd_args.append('mig-test.txt \'mig-test-d*'\')
            # cmd_args.append('mig-test.txt \'mig-test-d*/mig-remote-test.txt\'')
            # verify_cmds.append('%s mig-test-dir/mig-remote-test.txt' % rm_cmd)
            # verify_cmds.append('%s mig-test-dir/mig-remote-test.txt' % rm_cmd)
    elif op == 'read':
            pre_cmds.append('%s mig-test.txt .' % put_cmd)
            cmd_args.append('0 16 mig-test.txt -')
            post_cmds.append('%s mig-test.txt' % rm_cmd)
    elif op == 'rm':
            pre_cmds.append('%s mig-test.txt .' % put_cmd)
            cmd_args.append('mig-test.txt mig-test-new.txt')
            verify_cmds.append('%s mig-test.txt' % ls_cmd)
    elif op == 'rmdir':
            pre_cmds.append('%s -r mig-test-dir' % rm_cmd)
            cmd_args.append('mig-test-dir')
            verify_cmds.append('%s mig-test-dir' % ls_cmd)
            post_cmds.append('%s -r mig-test-dir' % rm_cmd)
    elif op == 'submit':
            cmd_args.append('mig-test.mRSL')
    elif op == 'touch':
            pre_cmds.append('%s mig-test.txt .' % rm_cmd)
            cmd_args.append('mig-test.txt')
            verify_cmds.append('%s mig-test.txt' % ls_cmd)
            post_cmds.append('%s mig-test.txt' % rm_cmd)
    elif op == 'truncate':
            pre_cmds.append('%s mig-test.txt .' % put_cmd)
            cmd_args.append('mig-test.txt')
            verify_cmds.append('%s mig-test.txt' % ls_cmd)
            post_cmds.append('%s mig-test.txt' % rm_cmd)
    elif op == 'unzip':
            pre_cmds.append('%s welcome.txt mig-test.zip' % zip_cmd)
            cmd_args.append('mig-test.zip mig-test.txt')
            verify_cmds.append('%s mig-test.txt' % ls_cmd)
            post_cmds.append('%s mig-test.txt mig-test.zip' % rm_cmd)
    elif op == 'write':
            pre_cmds.append('%s mig-test.txt .' % put_cmd)
            cmd_args.append('4 8 mig-test.txt mig-test.txt')
            post_cmds.append('%s mig-test.txt' % rm_cmd)
    elif op == 'zip':
            pre_cmds.append('%s mig-test.txt .' % put_cmd)
            cmd_args.append('mig-test.txt mig-test.zip')
            verify_cmds.append('%s mig-test.zip' % ls_cmd)
            post_cmds.append('%s mig-test.txt mig-test.zip' % rm_cmd)
    else:
            print 'No test available for %s!' % op
            return False

    index = 0
    for args in cmd_args:
        print 'test %d: %s %s' % (index, cmd, args)
        if pre_cmds[index:]:
            pre = pre_cmds[index]
            print 'setting up with: %s' % pre
            subprocess.call(pre.split(' '), stdout=subprocess.PIPE)
        ret = subprocess.call(('%s %s' % (cmd, args)).split(),
                              stdout=subprocess.PIPE)
        if ret == 0:
            print '   %s test %d SUCCEEDED' % (op, index)
        else:
            print '   %s test %d FAILED!' % (op, index)
        if verify_cmds[index:]:
            verify = verify_cmds[index]
            print 'verifying with: %s' % verify
            subprocess.call(verify.split(' '), stdout=subprocess.PIPE)
        if post_cmds[index:]:
            post = post_cmds[index]
            print 'cleaning up with: %s' % post
            subprocess.call(post.split(' '), stdout=subprocess.PIPE)
        index += 1
    return ret
"""
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s += end_function(lang, 'test_op')
    return s


def touch_function(lang, curl_cmd, curl_flags=''):
    """Call the touch cgi script with 'path' as argument."""

    relative_url = '"cgi-bin/touch.py"'
    query = '""'
    if lang == 'sh':
        post_data = '"output_format=txt;flags=$server_flags;$path_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;%s' % (server_flags, path_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'touch_file', ['path_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'touch_file')
    return s


def truncate_function(lang, curl_cmd, curl_flags='--compressed'):
    relative_url = '"cgi-bin/truncate.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;size=$size;$path_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;size=%s;%s' % (server_flags, size, path_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'truncate_file', ['size', 'path_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'truncate_file')
    return s


def unzip_function(lang, curl_cmd, curl_flags='--compressed'):
    """Call the corresponding cgi script with the string 'src_list' as argument. Thus
    the variable 'src_list' should be on the form
    \"src=pattern1[;src=pattern2[ ... ]]\"
    This may seem a bit awkward but it's difficult to do in a better way when
    begin_function() doesn't support variable length or array args.
    """

    relative_url = '"cgi-bin/unzip.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;dst=$dst;$src_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;dst=%s;%s' % (server_flags, dst, src_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'unzip_file', ['src_list', 'dst'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'src_list', 'src')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'unzip_file')
    return s


def wc_function(lang, curl_cmd, curl_flags=''):
    relative_url = '"cgi-bin/wc.py"'
    query = '""'
    if lang == 'sh':
        post_data = '"output_format=txt;flags=$server_flags;$path_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;%s' % (server_flags, path_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'wc_file', ['path_list'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'path_list', 'path')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'wc_file')
    return s


def write_function(lang, curl_cmd, curl_flags='--compressed'):
    relative_url = '"cgi-bin/rangefileaccess.py"'
    post_data = '""'
    if lang == 'sh':
        query = \
            '"?output_format=txt;flags=$server_flags;file_startpos=$first;file_endpos=$last;path=$dst_path"'
        curl_target = '"--upload-file $src_path"'
    elif lang == 'python':
        query = \
            "'?output_format=txt;flags=%s;file_startpos=%s;file_endpos=%s;path=%s' % (server_flags, first, last, dst_path)"
        curl_target = "'--upload-file %s' % src_path"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'write_file', ['first', 'last', 'src_path'
                        , 'dst_path'],
                        'Execute the corresponding server operation')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        curl_target,
        )
    s += end_function(lang, 'write_file')
    return s


def zip_function(lang, curl_cmd, curl_flags='--compressed'):
    """Call the corresponding cgi script with the string 'src_list' as argument. Thus
    the variable 'src_list' should be on the form
    \"src=pattern1[;src=pattern2[ ... ]]\"
    This may seem a bit awkward but it's difficult to do in a better way when
    begin_function() doesn't support variable length or array args.
    """

    relative_url = '"cgi-bin/zip.py"'
    query = '""'
    if lang == 'sh':
        post_data = \
            '"output_format=txt;flags=$server_flags;current_dir=$current_dir;dst=$dst;$src_list"'
    elif lang == 'python':
        post_data = \
            "'output_format=txt;flags=%s;current_dir=%s;dst=%s;%s' % (server_flags, current_dir, dst, src_list)"
    else:
        print 'Error: %s not supported!' % lang
        return ''

    s = ''
    s += begin_function(lang, 'zip_file', ['current_dir', 'src_list', 'dst'],
                        'Execute the corresponding server operation')
    s += format_list(lang, 'src_list', 'src')
    s += ca_check_init(lang)
    s += password_check_init(lang)
    s += timeout_check_init(lang)
    s += curl_perform(
        lang,
        relative_url,
        post_data,
        query,
        curl_cmd,
        curl_flags,
        )
    s += end_function(lang, 'zip_file')
    return s


# #######################
# Main part of scripts #
# #######################


def expand_list(
    lang,
    input_list,
    expanded_list,
    destinations=False,
    warnings=True,
    ):
    """Inline expansion of remote filenames from a list of patterns possibly
    with wild cards.

    Output from CGI script is on the form:
    Exit code: 0 Description OK (done in 0.012s)
    Title: MiG Files

    ___MIG FILES___

    test.txt test.txt
    """

    s = ''
    if lang == 'sh':
        s += \
            """
declare -a %s
# Save original args
orig_args=(\"${%s[@]}\")

index=1
for pattern in \"${orig_args[@]}\"; do
    expanded_path=$(expand_name \"path=$pattern\" \"$server_flags\" \"%s\" 2> /dev/null)
    set -- $expanded_path
    shift; shift
    exit_code=\"$1\"
    shift; shift; shift; shift; shift; shift; shift; shift; shift; shift; shift
    if [ \"$exit_code\" -ne \"0\" ]; then
"""\
             % (expanded_list, input_list, str(destinations).lower())
        if warnings:
            s += \
                """
        # output warning/error message(s) from expand
        echo \"$0: $@\"
"""
        s += \
            """
        continue
    fi
    while [ \"$#\" -gt \"0\" ]; do
        %s[$index]=$1
        index=$((index+1))
        shift
    done
done
"""\
             % expanded_list
    elif lang == 'python':
        s += \
            """
%s = []
for pattern in %s:
    (status, out) = expand_name('path=' + pattern, server_flags, '%s')
    result = [line.strip() for line in out if line.strip()]
    status = result[0].split()[2]
    src_list = result[3:]
    if status != '0':
"""\
             % (expanded_list, input_list, str(destinations).lower())
        if warnings:
            s += \
                """
        # output warning/error message(s) from expand
        print sys.argv[0] + ": " + ' '.join(src_list)
"""
        s += """
        continue
    %s += src_list
""" % expanded_list
    else:
        print 'Error: %s not supported!' % lang
        return ''

    return s


def shared_main(op, lang):
    """General wrapper for the specific main functions.
    Simply rewrites first arg to function name."""

    return eval('%s_main' % op)(lang)


# TODO: switch to new array/list argument format in all multi target function calls
# (No need to manually build var=a;var=b;.. in main when functions handle lists)


def cancel_main(lang):
    """
    Generate main part of corresponding scripts.
    
    lang specifies which script language to generate in.
    Currently 'sh' and 'python' are supported.
    
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the job_id string used directly:
# 'job_id="$1";job_id="$2";...;job_id=$N'
orig_args=("$@")
job_id_list=\"job_id=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    job_id_list=\"$job_id_list;job_id=$1\"
    shift
done
cancel_job $job_id_list
"""
    elif lang == 'python':
        s += \
            """
# Build the job_id string used directly:
# 'job_id="$1";job_id="$2";...;job_id=$N'
job_id_list = \"job_id=%s\" % \";job_id=\".join(sys.argv[1:])
(status, out) = cancel_job(job_id_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def cat_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
orig_args=("$@")
path_list="path=$1"
shift
while [ $# -gt "0" ]; do
    path_list="$path_list;path=$1"
    shift
done
cat_file $path_list
"""
    elif lang == 'python':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
path_list = \"path=%s\" % \";path=\".join(sys.argv[1:])
(status, out) = cat_file(path_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def cp_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    # cp cgi supports wild cards natively so no need to use
    # expand here

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 2, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the src string used directly:
# 'src="$1";src="$2";...;src=$N'
orig_args=("$@")
src_list="src=$1"
shift
while [ $# -gt 1 ]; do
    src_list="$src_list;src=$1"
    shift
done
dst=$1
cp_file $src_list $dst
"""
    elif lang == 'python':
        s += \
            """
# Build the src string used directly:
# 'src="$1";src="$2";...;src=$N'
src_list = \"src=%s\" % \";src=\".join(sys.argv[1:-1])
dst = sys.argv[-1]
(status, out) = cp_file(src_list, dst)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def doc_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, None, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
if [ $# -gt 0 ]; then
    # SearchList=()
    TopicList=(\"$@\")
else
    SearchList=(\"*\")
    # TopicList=()
fi

for Search in \"${SearchList[@]}\"; do
    show_doc \"$Search\" \"\"
done
for Topic in \"${TopicList[@]}\"; do
    show_doc \"\" \"$Topic\"
done
"""
    elif lang == 'python':
        s += \
            """
if len(sys.argv) - 1 > 0:
    SearchList = ""
    TopicList = sys.argv[1:]
else:
    SearchList = '*'
    TopicList = ""

out = []
for Search in SearchList:
    (status, search_out) = show_doc(Search, "")
    out += search_out
for Topic in TopicList:
    (status, topic_out) = show_doc("", Topic)
    out += topic_out
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def filemetaio_main(lang):
    """
    Generate main part of corresponding scripts.
    
    lang specifies which script language to generate in.
    Currently 'sh' and 'python' are supported.
    
    """

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += parse_options(lang, 'i',
                           '        i)  server_flags="${server_flags}i";;'
                          )
    elif lang == 'python':
        s += parse_options(lang, 'i',
                           '''    elif opt == "-i":
        server_flags += "i"''')
    s += arg_count_check(lang, 2, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the action and argument strings used directly:
# action="$1" path="$2";arg="$3";...;arg="$N"
orig_args=("$@")
action=\"$1\"
shift
path=\"$1\"
shift
arg_list=\"$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    arg_list=\"$arg_list;$1\"
    shift
done
filemetaio $action $path $arg_list
"""
    elif lang == 'python':
        s += \
            """
# Build the action and arg strings used directly:
# action=$1 "$2";"$3";...;"$N"
action = \"%s\" % sys.argv[1]
path = \"%s\" % sys.argv[2]
arg_list = \"%s\" % \";\".join(sys.argv[3:])
(status, out) = filemetaio(action, path, arg_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def get_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += parse_options(lang, 'r',
                           '        r)  server_flags="${server_flags}r";;'
                           )
    elif lang == 'python':
        s += parse_options(lang, 'r',
                           '''    elif opt == "-r":
        server_flags += "r"''')
    s += arg_count_check(lang, 2, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':

        # Advice about parsing taken from:
        # http://www.shelldorado.com/goodcoding/cmdargs.html

        s += \
            """
orig_args=(\"$@\")
src_list=(\"$@\")
raw_dst=\"${src_list[$(($#-1))]}\"
unset src_list[$(($#-1))]
"""
        s += expand_list(lang, 'src_list', 'expanded_list', True)
        s += \
            """
# Use '--' to handle case where no expansions succeeded
set -- \"${expanded_list[@]}\"
while [ $# -gt 0 ]; do
    src=$1
    dest=$2
    shift; shift
    dst=\"$raw_dst/$dest\"
    get_file \"$src\" \"$dst\"
done
"""
    elif lang == 'python':
        s += """
raw_dst = sys.argv[-1]
src_list = sys.argv[1:-1]
"""
        s += expand_list(lang, 'src_list', 'expanded_list', True)
        s += \
            """
# Expand does not automatically split the outputlines, so they are still on
# the src\tdest form
for line in expanded_list:
    src, dest = line.split()
    dst = raw_dst + os.sep + dest
    (status, out) = get_file(src, dst)
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def head_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += 'lines=20\n'
        s += parse_options(lang, 'n:', '        n)  lines="$OPTARG";;')
    elif lang == 'python':
        s += 'lines = 20\n'
        s += parse_options(lang, 'n:',
                           '''    elif opt == "-n":
        lines = val
''')
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
orig_args=("$@")
path_list="path=$1"
shift
while [ $# -gt "0" ]; do
    path_list="$path_list;path=$1"
    shift
done
head_file $lines $path_list
"""
    elif lang == 'python':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
path_list = \"path=%s\" % \";path=\".join(sys.argv[1:])
(status, out) = head_file(lines, path_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def jobaction_main(lang):
    """
    Generate main part of corresponding scripts.
    
    lang specifies which script language to generate in.
    Currently 'sh' and 'python' are supported.
    
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 2, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the action and job_id strings used directly:
# action="$1" job_id="$2";job_id="$3";...;job_id="$N"
orig_args=("$@")
action=\"$1\"
shift
job_id_list=\"job_id=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    job_id_list=\"$job_id_list;job_id=$1\"
    shift
done
job_action $action $job_id_list
"""
    elif lang == 'python':
        s += \
            """
# Build the action and job_id strings used directly:
# action=$1 job_id="$2";job_id="$3";...;job_id="$N"
action = \"%s\" % sys.argv[1]
job_id_list = \"job_id=%s\" % \";job_id=\".join(sys.argv[2:])
(status, out) = job_action(action, job_id_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def liveio_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 4, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the action, job_id, src and dst strings used directly:
# action="$1" job_id="$2" src="$2";src="$3";...;src=$((N-1) dst="$N"
orig_args=("$@")
action=\"$1\"
shift
job_id=\"$1\"
shift
src_list=\"src=$1\"
shift
while [ \"$#\" -gt \"1\" ]; do
    src_list=\"$src_list;src=$1\"
    shift
done
dst=\"$1\"
job_liveio $action $job_id $src_list $dst
"""
    elif lang == 'python':
        s += \
            """
# Build the action, job_id, src and dst strings used directly:
# action="$1" job_id="$2" src="$2";src="$3";...;src=$((N-1) dst="$N"
action = \"%s\" % sys.argv[1]
job_id = \"%s\" % sys.argv[2]
src_list = \"src=%s\" % \";src=\".join(sys.argv[3:-1])
dst = \"%s\" % sys.argv[-1]
(status, out) = job_liveio(action, job_id, src_list, dst)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def ls_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    # ls cgi supports wild cards natively so no need to use
    # expand here

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += parse_options(lang, 'alr',
                           '''        a)  server_flags="${server_flags}a"
            flags="${flags} -a";;
        l)  server_flags="${server_flags}l"
            flags="${flags} -l";;
        r)  server_flags="${server_flags}r"
            flags="${flags} -r";;''')
    elif lang == 'python':
        s += parse_options(lang, 'alr',
                           '''    elif opt == "-a":
        server_flags += "a"
    elif opt == "-l":
        server_flags += "l"
    elif opt == "-r":
        server_flags += "r"''')
    s += arg_count_check(lang, None, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
orig_args=("$@")
if [ $# -gt 0 ]; then
    path_list="path=$1"
    shift
else
    path_list="path=."
fi
while [ $# -gt "0" ]; do
    path_list="$path_list;path=$1"
    shift
done
ls_file $path_list
"""
    elif lang == 'python':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
if len(sys.argv) == 1:
    sys.argv.append(".")
path_list = \"path=%s\" % \";path=\".join(sys.argv[1:])
(status, out) = ls_file(path_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def mkdir_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    # Client side wild card expansion doesn't make sense for mkdir

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += parse_options(lang, 'p',
                           '        p)  server_flags="${server_flags}p"\n            flags="${flags} -p";;'
                           )
    elif lang == 'python':
        s += parse_options(lang, 'p',
                           '    elif opt == "-p":\n        server_flags += "p"'
                           )
    s += arg_count_check(lang, 1, 2)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the path string used directly:
# 'path=$1;path=$2;...;path=$N'
orig_args=(\"$@\")
path_list=\"path=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    path_list=\"$path_list;path=$1\"
    shift
done
mk_dir $path_list
"""
    elif lang == 'python':
        s += \
            """
# Build the path string used directly:
# 'path=$1;path=$2;...;path=$N'
path_list = \"path=%s\" % \";path=\".join(sys.argv[1:])
(status, out) = mk_dir(path_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def mqueue_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 2, 3)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += """
# optional third argument depending on action - add dummy
job_mqueue $@ ''
"""
    elif lang == 'python':
        s += \
            """
# optional third argument depending on action - add dummy
sys.argv.append('')
(status, out) = job_mqueue(*(sys.argv[1:4]))
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def mv_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    # mv cgi supports wild cards natively so no need to use
    # expand here

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 2, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the src string used directly:
# 'src="$1";src="$2";...;src=$N'
orig_args=("$@")
src_list="src=$1"
shift
while [ $# -gt 1 ]; do
    src_list="$src_list;src=$1"
    shift
done
dst=$1
mv_file $src_list $dst
"""
    elif lang == 'python':
        s += \
            """
# Build the src string used directly:
# 'src="$1";src="$2";...;src=$N'
src_list = \"src=%s\" % \";src=\".join(sys.argv[1:-1])
dst = sys.argv[-1]
(status, out) = mv_file(src_list, dst)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def put_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    # TODO: can we support wildcards in destination? (do we want to?)
    #      - destination like somedir*/somefile ?
    #        - when somedir* and somefile exists
    #        - when somedir* exists but somefile doesn't exists there
    #        -> we need to expand dirname alone too for both to work!
    #      - destination like somedir*/somefile* ?
    #      - what about ambiguous expansions?

    # We should handle uploads like this:
    # migput localfile . -> localfile
    # migput localfile remotefile -> remotefile
    # migput localfile remotedir -> remotedir/localfile
    # migput ../localdir/localfile remotedir -> upload as file and expect server ERROR
    # migput ../localdir/localfile remotedir/ -> remotedir/localfile
    # migput ../localdir . -> ERROR?
    # migput -r ../localdir . -> localdir
    # migput -r ../localdir remotedir -> remotedir/localdir
    #                                   -> remotedir/localdir/*

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += 'submit_mrsl=0\n'
        s += 'recursive=0\n'
        s += 'extract_package=0\n'
        s += parse_options(lang, 'prx',
                           '        p)  submit_mrsl=1;;\n        r)  recursive=1;;\n        x)  extract_package=1;;'
                           )
    elif lang == 'python':
        s += 'submit_mrsl = False\n'
        s += 'recursive = False\n'
        s += 'extract_package = False\n'
        s += parse_options(lang, 'prx',
                           '''    elif opt == "-p":
        submit_mrsl = True
    elif opt == "-r":
        recursive = True
    elif opt == "-x":
        extract_package = True''')
    s += arg_count_check(lang, 2, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
src_list=(\"$@\")
raw_dst=\"${src_list[$(($#-1))]}\"
unset src_list[$(($#-1))]

# remove single '.' to avoid problems with missing ending slash
if [ \".\" = \"$raw_dst\" ]; then
    dst=\"\"
else
    dst=\"$raw_dst\"
fi

# The for loop automatically expands any wild cards in src_list
for src in ${src_list[@]}; do
    if [ ! -e \"$src\" ]; then
        echo \"No such file or directory: $src !\"
        continue
    fi
    if [ -d \"$src\" ]; then
        if [ $recursive -ne 1 ]; then
            echo \"Nonrecursive put skipping directory: $src\"
            continue
        fi
        # Recursive dirs may not exist - create them first
        src_parent=`dirname $src`
        src_target=`basename $src`
        dirs=`cd $src_parent && find $src_target -type d`
        # force mkdir -p
        old_flags=\"$server_flags\"
        server_flags=\"p\"
        dir_list=\"\"
        for dir in $dirs; do
            dir_list=\"$dir_list;path=$dst/$dir\"
        done
        mk_dir \"$dir_list\"
        server_flags=\"$old_flags\"
        sources=`cd $src_parent && find $src_target -type f`
        for path in $sources; do
            put_file \"$src_parent/$path\" \"$dst/$path\" $submit_mrsl $extract_package
        done
    else
        put_file \"$src\" \"$dst\" $submit_mrsl $extract_package
    fi
done
"""
    elif lang == 'python':
        s += \
            """
from glob import glob

raw_list = sys.argv[1:-1]

raw_dst = sys.argv[-1]
if \".\" == raw_dst:
    dst = \"\"
else:
    dst = raw_dst

# Expand sources
src_list = []
for src in raw_list:
    expanded = glob(src)
    if expanded:
        src_list += expanded
    else:
        # keep bogus pattern for correct output order
        src_list += [src]

for src in src_list:
    if not os.path.exists(src):
        print \"No such file or directory: %s !\" % src
        continue
    if os.path.isdir(src):
        if not recursive:
            print \"Nonrecursive put skipping directory: %s\" % src
            continue
        src_parent = os.path.abspath(os.path.dirname(src))
        for root, dirs, files in os.walk(os.path.abspath(src)):
            # Recursive dirs may not exist - create them first
            # force mkdir -p
            old_flags = \"$server_flags\"
            server_flags = \"p\"
            rel_root = root.replace(src_parent, '', 1).lstrip(os.sep)
            dir_list = ';'.join(['path=%s' % os.path.join(dst, rel_root, i) for i in dirs])
            # add current root
            dir_list += ';path=%s' % os.path.join(dst, rel_root)
            mk_dir(dir_list)
            server_flags = \"$old_flags\"
            for name in files:
                src_path = os.path.join(root, name)
                dst_path = os.path.join(dst, rel_root, name)
                (status, out) = put_file(src_path, dst_path, submit_mrsl, extract_package)
                print ''.join(out),
    else:
        (status, out) = put_file(src, dst, submit_mrsl, extract_package)
        print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def read_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 4, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += """
read_file $@
"""
    elif lang == 'python':
        s += \
            """
(status, out) = read_file(*(sys.argv[1:]))
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def resubmit_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the job_id string used directly:
# 'job_id="$1";job_id="$2";...;job_id=$N'
orig_args=("$@")
job_id_list=\"job_id=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    job_id_list=\"$job_id_list;job_id=$1\"
    shift
done
resubmit_job $job_id_list
"""
    elif lang == 'python':
        s += \
            """
# Build the job_id_list string used directly:
# 'job_id="$1";job_id="$2";...;job_id=$N'
job_id_list = \"job_id=%s\" % \";job_id=\".join(sys.argv[1:])
(status, out) = resubmit_job(job_id_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def rm_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    # rm cgi supports wild cards natively so no need to use
    # expand here

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += parse_options(lang, 'r',
                           '        r)  server_flags="${server_flags}r"\n           flags="${flags} -r";;'
                           )
    elif lang == 'python':
        s += parse_options(lang, 'r',
                           '    elif opt == "-r":\n        server_flags += "r"'
                           )
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the path string used directly:
# 'path=$1;path=$2;...;path=$N'
orig_args=(\"$@\")
path_list=\"path=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    path_list=\"$path_list;path=$1\"
    shift
done
rm_file $path_list
"""
    elif lang == 'python':
        s += \
            """
# Build the path string used directly:
# 'path=$1;path=$2;...;path=$N'
path_list = \"path=%s\" % \";path=\".join(sys.argv[1:])
(status, out) = rm_file(path_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def rmdir_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    # Client side wild card expansion doesn't make sense for rmdir

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += parse_options(lang, 'p',
                           '        p)  server_flags="${server_flags}p"\n            flags="${flags} -p";;'
                           )
    elif lang == 'python':
        s += parse_options(lang, 'p',
                           '    elif opt == "-p":\n        server_flags += "p"'
                           )
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the path string used directly:
# 'path=$1;path=$2;...;path=$N'
orig_args=(\"$@\")
path_list=\"path=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    path_list=\"$path_list;path=$1\"
    shift
done
rm_dir $path_list
"""
    elif lang == 'python':
        s += \
            """
# Build the path string used directly:
# 'path=$1;path=$2;...;path=$N'
path_list = \"path=%s\" % \";path=\".join(sys.argv[1:])
(status, out) = rm_dir(path_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def stat_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
orig_args=("$@")
path_list=\"path=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    path_list=\"$path_list;path=$1\"
    shift
done
stat_file $path_list
"""
    elif lang == 'python':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
path_list = \"path=%s\" % \";path=\".join(sys.argv[1:])
(status, out) = stat_file(path_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def status_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += "max_job_count=''\n"
        s += parse_options(lang, 'm:S',
                           '''        m)  max_job_count="$OPTARG";;
        S)  server_flags="${server_flags}s"
            flags="${flags} -S";;''')
    elif lang == 'python':
        s += "max_job_count = ''\n"
        s += parse_options(lang, 'm:S',
                           '''    elif opt == "-m":
        max_job_count = val
    elif opt == "-S":
        server_flags += "s"''')
    s += arg_count_check(lang, None, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the job_id string used directly:
# 'job_id="$1";job_id="$2";...;job_id=$N'
orig_args=("$@")
job_id_list=\"job_id=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    job_id_list=\"$job_id_list;job_id=$1\"
    shift
done
job_status $job_id_list $max_job_count
"""
    elif lang == 'python':
        s += \
            """
# Build the job_id string used directly:
# 'job_id="$1";job_id="$2";...;job_id=$N'
job_id_list = \"job_id=%s\" % \";job_id=\".join(sys.argv[1:])
(status, out) = job_status(job_id_list, max_job_count)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def submit_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
extract_package=1
submit_mrsl=1

src_list=(\"$@\")

for src in \"${src_list[@]}\"; do
    dst=`basename \"$src\"`
    submit_file \"$src\" $dst $submit_mrsl $extract_package
done
"""
    elif lang == 'python':
        s += \
            """
extract_package = True
submit_mrsl = True

src_list = sys.argv[1:]

for src in src_list:
    dst = os.path.basename(src)
    (status, out) = submit_file(src, dst, submit_mrsl, extract_package)
    print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def tail_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += 'lines=20\n'
        s += parse_options(lang, 'n:', '        n)  lines="$OPTARG";;')
    elif lang == 'python':
        s += 'lines = 20\n'
        s += parse_options(lang, 'n:',
                           '''    elif opt == "-n":
        lines = val
''')
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
orig_args=("$@")
path_list=\"path=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    path_list=\"$path_list;path=$1\"
    shift
done
tail_file $lines $path_list
"""
    elif lang == 'python':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
path_list = \"path=%s\" % \";path=\".join(sys.argv[1:])
(status, out) = tail_file(lines, path_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def test_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, None, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Prepare for file operations
echo 'this is a test file used by the MiG self test' > mig-test.txt
echo '::EXECUTE::' > mig-test.mRSL
echo 'pwd' >> mig-test.mRSL

echo 'Upload test file used in other tests'
put_file mig-test.txt . 0 0 >& /dev/null
if [ $? -ne 0 ]; then
    echo 'Upload failed!'
    exit 1
else
    echo 'Upload succeeded'
fi

if [ $# -eq 0 ]; then
    op_list=(%s)
else
    op_list=(\"$@\")
fi

for op in \"${op_list[@]}\"; do
    test_op \"$op\"
done
"""\
             % ' '.join(script_ops)
    elif lang == 'python':
        s += \
            """
# Prepare for file operations
txt_fd = open('mig-test.txt', 'w')
txt_fd.write('''this is a test file used by the MiG self test
''')
txt_fd.close()
job_fd = open('mig-test.mRSL', 'w')
job_fd.write('''::EXECUTE::
pwd
''')
job_fd.close()

print 'Upload test file used in other tests'
(ret, out) = put_file('mig-test.txt', '.', False, False)
if ret != 0:
    print 'Upload failed!'
    sys.exit(1)
else:
    print 'Upload succeeded'

if sys.argv[1:]:
    op_list = sys.argv[1:]
else:   
    op_list = %s

for op in op_list:
    test_op(op)
"""\
             % script_ops
    else:
        print 'Error: %s not supported!' % lang

    return s


def touch_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    # touch cgi supports wild cards natively so no need to use
    # expand here
    # Client side wild card expansion doesn't make sense for touch

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the path string used directly:
# 'path=$1;path=$2;...;path=$N'
orig_args=(\"$@\")
path_list=\"path=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    path_list=\"$path_list;path=$1\"
    shift
done
touch_file $path_list
"""
    elif lang == 'python':
        s += \
            """
# Build the path string used directly:
# 'path=$1;path=$2;...;path=$N'
path_list = \"path=%s\" % \";path=\".join(sys.argv[1:])
(status, out) = touch_file(path_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def truncate_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += 'size=0\n'
        s += parse_options(lang, 'n:', '        n)  size="$OPTARG";;')
    elif lang == 'python':
        s += 'size = 0\n'
        s += parse_options(lang, 'n:',
                           '''    elif opt == "-n":
        size = val
''')
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
orig_args=("$@")
path_list=\"path=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    path_list=\"$path_list;path=$1\"
    shift
done
truncate_file $size $path_list
"""
    elif lang == 'python':
        s += \
            """
# Build the path string used directly:
# 'path="$1";path="$2";...;path=$N'
path_list = \"path=%s\" % \";path=\".join(sys.argv[1:])
(status, out) = truncate_file(size, path_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def unzip_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    # unzip cgi supports wild cards natively so no need to use
    # expand here

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 2, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the src string used directly:
# 'src="$1";src="$2";...;src=$N'
orig_args=("$@")
src_list="src=$1"
shift
while [ $# -gt 1 ]; do
    src_list="$src_list;src=$1"
    shift
done
dst=$1
unzip_file $src_list $dst
"""
    elif lang == 'python':
        s += \
            """
# Build the src string used directly:
# 'src="$1";src="$2";...;src=$N'
src_list = \"src=%s\" % \";src=\".join(sys.argv[1:-1])
dst = sys.argv[-1]
(status, out) = unzip_file(src_list, dst)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def wc_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += parse_options(lang, 'blw',
                           '''        b)  server_flags="${server_flags}b"
            flags="${flags} -b";;
        l)  server_flags="${server_flags}l"
            flags="${flags} -l";;
        w)  server_flags="${server_flags}w"
            flags="${flags} -w";;''')
    elif lang == 'python':
        s += parse_options(lang, 'blw',
                           '''    elif opt == "-b":
        server_flags += "b"
    elif opt == "-l":
        server_flags += "l"
    elif opt == "-w":
        server_flags += "w"''')
    s += arg_count_check(lang, 1, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the path string used directly:
# 'path=$1;path=$2;...;path=$N'
orig_args=(\"$@\")
path_list=\"path=$1\"
shift
while [ \"$#\" -gt \"0\" ]; do
    path_list=\"$path_list;path=$1\"
    shift
done
wc_file $path_list
"""
    elif lang == 'python':
        s += \
            """
# Build the path string used directly:
# 'path=$1;path=$2;...;path=$N'
path_list = \"path=%s\" % \";path=\".join(sys.argv[1:])
(status, out) = wc_file(path_list)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def write_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    s = ''
    s += basic_main_init(lang)
    s += parse_options(lang, None, None)
    s += arg_count_check(lang, 4, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += """
write_file $@
"""
    elif lang == 'python':
        s += \
            """
(status, out) = write_file(*(sys.argv[1:]))
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


def zip_main(lang):
    """
    Generate main part of corresponding scripts.

    lang specifies which script language to generate in.
    """

    # zip cgi supports wild cards natively so no need to use
    # expand here

    s = ''
    s += basic_main_init(lang)
    if lang == 'sh':
        s += 'current_dir=""\n'
        s += parse_options(lang, 'w:', '        w)  current_dir="$OPTARG";;')
    elif lang == 'python':
        s += 'current_dir = ""\n'
        s += parse_options(lang, 'w:',
                           '''    elif opt == "-w":
        current_dir = val
''')
    s += arg_count_check(lang, 2, None)
    s += check_conf_readable(lang)
    s += configure(lang)
    if lang == 'sh':
        s += \
            """
# Build the src string used directly:
# 'src="$1";src="$2";...;src=$N'
orig_args=("$@")
src_list="src=$1"
shift
while [ $# -gt 1 ]; do
    src_list="$src_list;src=$1"
    shift
done
dst=$1
# current_dir may be empty
zip_file \"$current_dir\" $src_list $dst
"""
    elif lang == 'python':
        s += \
            """
# Build the src string used directly:
# 'src="$1";src="$2";...;src=$N'
src_list = \"src=%s\" % \";src=\".join(sys.argv[1:-1])
dst = sys.argv[-1]
(status, out) = zip_file(current_dir, src_list, dst)
print ''.join(out),
sys.exit(status)
"""
    else:
        print 'Error: %s not supported!' % lang

    return s


# ######################
# Generator functions #
# ######################


def generate_cancel(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_cat(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_cp(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_doc(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_filemetaio(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)


def generate_get(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += expand_function(lang, curl_cmd)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_head(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_jobaction(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_lib(script_ops, scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate shared lib for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s for %s' % (op, lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += expand_function(lang, curl_cmd)
        for function in script_ops:
            script += shared_op_function(function, lang, curl_cmd)
        script += basic_main_init(lang)
        script += check_conf_readable(lang)
        script += configure(lang)

        write_script(script, dest_dir + os.sep + script_name, mode=0644)

    return True


def generate_liveio(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_ls(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_mkdir(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_mqueue(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_mv(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_put(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)

        # Recursive put requires mkdir

        script += mkdir_function(lang, curl_cmd)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_read(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_resubmit(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_rm(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_rmdir(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_stat(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_status(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_submit(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_tail(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_test(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)

        # use put function for preparation

        script += shared_op_function('put', lang, curl_cmd)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_touch(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_truncate(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_unzip(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_wc(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_write(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


def generate_zip(scripts_languages, dest_dir='.'):

    # Extract op from function name

    op = sys._getframe().f_code.co_name.replace('generate_', '')

    # Generate op script for each of the languages in scripts_languages

    for (lang, interpreter, extension) in scripts_languages:
        verbose(verbose_mode, 'Generating %s script for %s' % (op,
                lang))
        script_name = '%s%s.%s' % (mig_prefix, op, extension)

        script = ''
        script += init_script(op, lang, interpreter)
        script += version_function(lang)
        script += shared_usage_function(op, lang, extension)
        script += check_var_function(lang)
        script += read_conf_function(lang)
        script += shared_op_function(op, lang, curl_cmd)
        script += shared_main(op, lang)

        write_script(script, dest_dir + os.sep + script_name)

    return True


# Defaults

verbose_mode = False
shared_lib = True
test_script = True
include_license = True

# Supported MiG operations (don't add 'test' as it is optional)

# TODO: add find, *freeze, *re, grep, jobfeasible, jobschedule, mrslview
#           settings, vm*, 

script_ops = [
    'cancel',
    'cat',
    'cp',
    'doc',
    'filemetaio',
    'get',
    'head',
    'jobaction',
    'liveio',
    'ls',
    'mkdir',
    'mqueue',
    'mv',
    'put',
    'read',
    'rm',
    'rmdir',
    'stat',
    'status',
    'submit',
    'resubmit',
    'tail',
    'touch',
    'truncate',
    'unzip',
    'wc',
    'write',
    'zip',
    ]

# Script prefix for all user scripts

mig_prefix = 'mig'

# Default commands:

sh_lang = 'sh'
sh_cmd = '/bin/sh'
sh_ext = 'sh'
python_lang = 'python'

# python_cmd is only actually used on un*x so don't worry about path

python_cmd = '/usr/bin/python'
python_ext = 'py'

# curl_cmd must be generic for cross platform support

curl_cmd = 'curl'
dest_dir = '.'

# ###########
# ## Main ###
# ###########
# Only run interactive commands if called directly as executable

if __name__ == '__main__':
    opts_str = 'c:d:hlp:s:tvV'
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], opts_str)
    except getopt.GetoptError, goe:
        print 'Error: %s' % goe
        usage()
        sys.exit(1)

    for (opt, val) in opts:
        if opt == '-c':
            curl_cmd = val
        elif opt == '-d':
            dest_dir = val
        elif opt == '-i':
            include_license = False
        elif opt == '-l':
            shared_lib = False
        elif opt == '-p':
            python_cmd = val
        elif opt == '-s':
            sh_cmd = val
        elif opt == '-t':
            test_script = True
        elif opt == '-v':
            verbose_mode = True
        elif opt == '-V':
            version()
            sys.exit(0)
        elif opt == '-h':
            usage()
            sys.exit(0)
        else:
            print 'Error: %s not supported!' % opt
            usage()
            sys.exit(1)

    verbose(verbose_mode, 'using curl from: %s' % curl_cmd)
    verbose(verbose_mode, 'using sh from: %s' % sh_cmd)
    verbose(verbose_mode, 'using python from: %s' % python_cmd)
    verbose(verbose_mode, 'writing script to: %s' % dest_dir)

    if not os.path.isdir(dest_dir):
        print "Error: destination directory doesn't exist!"
        sys.exit(1)

    argc = len(args)
    if argc == 0:

        # Add new languages here

        languages = [(sh_lang, sh_cmd, sh_ext), (python_lang,
                     python_cmd, python_ext)]
        for (lang, cmd, ext) in languages:
            print 'Generating %s scripts' % lang
    else:
        languages = []

        # check arguments

        for lang in args:
            if lang == 'sh':
                interpreter = sh_cmd
                extension = sh_ext
            elif lang == 'python':
                interpreter = python_cmd
                extension = python_ext
            else:
                print 'Unknown script language: %s - ignoring!' % lang
                continue

            print 'Generating %s scripts' % lang

            languages.append((lang, interpreter, extension))

    # Generate all scripts

    for op in script_ops:
        generator = 'generate_%s' % op
        eval(generator)(languages, dest_dir)

    if shared_lib:
        generate_lib(script_ops, languages, dest_dir)

    if test_script:
        generate_test(languages, dest_dir)

    if include_license:
        write_license(dest_dir)
        
    sys.exit(0)
