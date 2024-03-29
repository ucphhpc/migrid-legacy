#!/bin/bash

# Setting MIG_HOST, some gives full hostname
# others gives only machinename
if [ `hostname | grep -c "\."` -eq 0 ]; then
   MIG_HOST="`hostname`"
else
   MIG_HOST="`hostname | awk -F '.' '{print $1}'`"
fi

MIG_DOMAIN="`domainname`"
MIG_HOST_IDENTIFIER="0"
MIG_RESOURCE_PATH="/usr/local/mig_xsss"
MIG_RESOURCE_START_EXE="./start_resource_exe.sh"

cd $MIG_RESOURCE_PATH
$MIG_RESOURCE_START_EXE $MIG_HOST.$MIG_DOMAIN.$MIG_HOST_IDENTIFIER $MIG_HOST $1 2>/dev/null

