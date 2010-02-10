#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# mrsltoxrsl: translate MiG job to ARC job
#
# (C) 2009 Jost Berthold, grid.dk
#  adapted to usage inside a MiG framework
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

"""translate a "job" from MiG format to ARC format."""

import string
import random
import math
import os
import sys

# MiG utilities:
from shared.conf import get_configuration_object
config = get_configuration_object()
logger = config.logger

# to make this succeed: 
# install nordugrid-arc-client and nordugrid-arc-python
# set LD_LIBRARY_PATH="$NORDUGRID_LOCATION/lib:$GLOBUS_LOCATION/lib
#     PYTHONPATH="$NORDUGRID_LOCATION/lib/python2.4/site-packages"
try:
    import arclib
except:
    logger.error('problems importing arclib... trying workaround')
    try:
        logger.debug('Current sys.path is %s' % sys.path )
        sys.path.append(os.environ['NORDUGRID_LOCATION'] 
                        + '/lib/python2.4/site-packages')
        import arclib
    except:
        logger.error('arclib not found. Aborting whole execution.')
        sys.exit(255)

# translate :: (checked Dictionary, session_ID) 
#              -> (Xrsl,Job Script,name for Job script)
def translate(mrsl_dict, session_id = None):
    """Translate an (already checked) mRSL dictionary into xRSL,
       suitable for submitting to an ARC resource. 
       
       Returns arclib.Xrsl object.
       Throws exception if errors in the xRSL generation occur."""
       
    logger.debug('to translate:\n%s\n using session ID %s' \
                 % (mrsl_dict, session_id))
    
    try:
        # every xrsl-specified job is a conjunction at the top level
        xrsl = arclib.Xrsl(arclib.operator_and)

        if 'JOB_ID' in mrsl_dict:
            j_name = mrsl_dict['JOB_ID']
        else:
            # random string. should not happen anyway...
            j_name = ''.join(random.choice(string.letters) \
                             for i in xrange(12))
#        j_name = mrsl_dict.get('JOB_ID', 
#                               ''.join(random.choice(string.letters)  \
#                                       for i in xrange(12)))

        # use JOBID as ARC jobname to avoid presenting only ARC IDs
        addRel(xrsl,'jobname', 
               ''.join([mrsl_dict.get('JOBNAME',''),'(',j_name,')']))

        # inputfiles + executables, outputfiles
        if session_id:
            # we have been given a destination to put output files. Insert 
            # MiG server URL (automatic output download, will use PUT)
            destination = '/'.join([config.migserver_https_sid_url
                                   , 'sid_redirect'
                                   , session_id, ''])
        else:
            destination = ''

        # make double lists, 2nd part perhaps empty
        # output files, always including stdout
        tmpoutfiles = map(file_mapping, mrsl_dict.get('OUTPUTFILES',[]))
        outfiles = []
        for [f,target] in tmpoutfiles:
            if target == '':
                target = f # same file name if none given
            if -1 == target.find('://'): # not remote target, should copy
                    # (ARC does not allow local file names as target)
                target = ''.join([destination,target])
                    # means: automatic upload to jobdir on MiG server. 
            outfiles.append([f,target])

        # job output, maybe transfer automatically to MiG server
        destination = destination + '/'.join(['job_output', j_name,''])
        stdout = '.'.join([j_name,'stdout'])
        stderr = '.'.join([j_name,'stderr'])

        # do not merge stdout and stderr
        addRel(xrsl, 'join', 'no')

        addRel(xrsl, 'stdout', stdout)
        outfiles.append([stdout, ''.join([destination, stdout])])
        addRel(xrsl, 'stderr', stderr)
        outfiles.append([stderr, ''.join([destination, stderr])])

        addRel(xrsl, 'outputfiles', outfiles)
        
        # what we want to do: EXECUTE (should be there)
        scriptlines = mrsl_dict['EXECUTE']
        script = '\n'.join(['# generated script from mRSL EXECUTE'] 
                           + scriptlines)
        # the script is expected to be present as an input file,
        # and to have a certain name which we return.
        addRel(xrsl,'executable','/bin/sh')
        # HEADS UP: this is the script name we wire in.
        script_name = '.'.join([j_name,'sh'])
        addRel(xrsl,'arguments', script_name)

        # executable input files, always including the execute script
        execfiles = map(file_mapping, mrsl_dict.get('EXECUTABLES',[]))
        # HEADS UP: the script name again!
        execfiles.append([script_name,''])

        # (non-executable) input files
        infiles = map(file_mapping, mrsl_dict.get('INPUTFILES',[]))

        # both execfiles and infiles are inputfiles for ARC
        addRel(xrsl, 'inputfiles', map(flip_for_input, execfiles + infiles))

        # execfiles are made executable 
        # (specified as the remote name, relative to the session dir)
        def fst(list):
            return list[0]
        addRel(xrsl, 'executables', map(fst, execfiles))

        # more stuff...

        # requested runtime, given in minutes in (user) xrsl ...
        time = mrsl_dict.get('CPUTIME')
        if time:
            addRel(xrsl, 'cputime', str(int(math.ceil(float(time)/60))))

        # simply copy the values for these:
        copy_items = ['MEMORY', 'DISK', 'NODECOUNT'] 
        xrsl_name = {'MEMORY':'memory', 'DISK':'disk', 'NODECOUNT':'count'} 
        # NB: we have to ignore CPUCOUNT, not supported by ARC xrsl

        for x in copy_items: # we ignore the ones which are not there
            if x in mrsl_dict:
                addRel(xrsl,xrsl_name[x],mrsl_dict[x])
                # and these are all single values

        if 'ARCHITECTURE' in mrsl_dict:
            addRel(xrsl,'architecture',
                   translate_arch(mrsl_dict['ARCHITECTURE']))

        if 'ENVIRONMENT' in mrsl_dict:

# these have already been mangled into pairs (name,value) before
#            var_val = []
#            for definition in mrsl_dict['ENVIRONMENT']:
#                vv = definition.strip().split('=')
#                var_val.append(vv.strip())
#            addRel(xrsl,'environment',var_val)
            
            addRel(xrsl,'environment',map(list,mrsl_dict['ENVIRONMENT']))
            
        if 'RUNTIMEENVIRONMENT' in mrsl_dict:
            for line in mrsl_dict['RUNTIMEENVIRONMENT']:
                addRel(xrsl,'runTimeEnvironment', line.strip())

        if 'NOTIFY' in mrsl_dict:
            addresses = []
            for line in filter(is_mail, mrsl_dict['NOTIFY'])[:3]: # max 3
                # remove whites before, then "email:" prefix, then strip
                address = line.lstrip()[6:].strip()
                if address != 'SETTINGS':
                    addresses.append(address)
#                else:
#                    # this should be replaced already, but...
#                    # FIXME: get it from the settings :-P
#                    addresses.append('*FROM THE SETTINGS*') 
            if addresses:
                addRel(xrsl,'notify', 'ec ' + ' '.join(addresses))

        logger.debug('XRSL:\n%s\nScript (%s):\n%s\n)' % (xrsl,script_name,script))
    except arclib.XrslError, err:
        logger.error( 'Error generating Xrsl: %s' % err )
        raise err
    return (xrsl,script,script_name)

# helper functions and constants used:

# write_pair :: (String,a)       -> arclib.XrslRelation
# and is polymorphic in a: a = String, a = List(String), a = List(List(String))
# the C version of XrslRelation is... so we emulate it here:
def write_pair(name, values):
    if isinstance(values,list):
        if isinstance(values[0],list):
            con = arclib.XrslRelationDoubleList
            val = values # should cast all to strings, but only used with them
        else:
            con = arclib.XrslRelationList
            val = values # should cast all to strings, but only used with them
    else:
        con = arclib.XrslRelation
        val = values.__str__()
    return con(name,arclib.operator_eq,val)

# used all the time... shortcut.
def addRel(xrsl,name,values):
    # sometimes we receive empty stuff from the caller. 
    # No point writing it out at all.
    if isinstance(values,list) and len(values) == 0:
        return
    if values == '':
        return
    xrsl.AddRelation(write_pair(name,values))

# architectures
architectures = {'X86':'i686', 'AMD64':'x86-64', 'IA64':'ia64', 
                  'SPARC':'sparc64', 'SPARC64':'sparc64', 
                  # 'ITANIUM':'???ia64???', 
                  'SUN4U':'sun4u', 'SPARC-T1':'sparc64', 'SPARC-T2':'sparc64', 
                  # 'PS3':'??unknown??', 
                  'CELL':'cell'}
def translate_arch(mig_arch):

    if mig_arch in architectures:
        return architectures[mig_arch]
    else:
        return ''

def is_mail(str):
    return str.lstrip().startswith('email:')

def file_mapping(line):
    """Splits the given line of the expected format 
          local_name <space> remote_name
       into a 2-element list [local_name,remote_name]
       If remote_name is empty, the empty string is returned as the 2nd part.
       No additional checks are performed.
       TODO should perhaps also check for valid path characters."""
    line = line.strip()
    parts = line.split()
    local = parts[0]
    if len(parts) < 2:
        remote = ''
    else:
        remote = parts[1]
    return [local,remote]

def flip_for_input(list):
    if list[1] == '':
        return[list[0],'']
    else:   
        return [list[1],list[0]]

if __name__ == '__main__':
    print 'starting translation test. Args: ' , len(sys.argv)
    logger.debug('translation for file ' + sys.argv[1] + ' starts')
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        parsed = '.'.join([fname,'parsed'])
        translated = '.'.join([parsed,'xrsl'])

        try:
            import shared.mrslparser as p
            import shared.fileio as fileio

            (presult,errors) = p.parse(fname, 'test-id',
                                       '+No+Client+Id',None,parsed)
            if not presult:
                print('Errors: \n',errors)
            else:
                print 'Parsing OK, now translating'
                mrsl_dict = fileio.unpickle(parsed,logger)
                (xrsl,script,name) = translate(mrsl_dict,'test-name')
                print '\n'.join(['Job name',name,'script',script,'XRSL'])
                print xrsl
                print (str(xrsl).replace('(', '\t').replace(')', '\n'))
                print 'done'
        except Exception, err:
            print 'Error.'
            print err.__str__()

