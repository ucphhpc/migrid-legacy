#!/bin/sh
#
# Submit supplied job script using all supplied MiG environmnets
# Please note that MiG will automatically append JOB_SCRIPT argument to the call

if [ -z "$MIG_JOBNAME" -o -z "$MIG_SUBMITUSER" -o -z "$MIG_JOBDIR" -o -z "$MIG_JOBNODECOUNT" -o -z "$MIG_JOBCPUCOUNT" -o -z "$MIG_JOBCPUTIME" -o -z "$MIG_JOBMEMORY" -o -z "$MIG_JOBDISK" -o -z "$MIG_EXENODE" -o -z "$MIG_LRMS_OUT" -o -z "$MIG_LRMS_ERR" ]; then
    echo "Usage: $0 [QUEUE_ARGS] JOB_SCRIPT"
    echo "where the environment should provide values for at least:"
    echo "MIG_JOBNAME, MIG_SUBMITUSER, MIG_JOBDIR, MIG_JOBNODECOUNT, MIG_JOBCPUCOUNT,"
    echo "MIG_JOBCPUTIME, MIG_JOBMEMORY, MIG_JOBDISK, MIG_EXENODE, MIG_LRMS_OUT and MIG_LRMS_ERR."
    echo "The optional QUEUE_ARGS are passed directly to the queue command(s)."
    exit 1
fi

if [ -z "$MIG_ADMINEMAIL" ]; then
    mail_opt=""
else
    mail_opt="--mail-user=$MIG_ADMINEMAIL"
fi

# mig cputime uses seconds but sbatch uses minutes
mins=$(($MIG_JOBCPUTIME/60))
secs=$(($MIG_JOBCPUTIME%60))

# Require exclusive node use and ignore cpu count since it breaks if slurm is
# configured with multiple sockets and cores (i.e. --mincpus=32 fails with 
# 2 sockets of 16 cores each). Otherwise we would request the right number
# with --mincpus=${MIG_JOBCPUCOUNT} . We don't want multiple jobs on the same
# node anyway.
# 
# NOTE: --mem="""$MIG_JOBMEMORY""" is disabled for now as MiG jobs enforces virtual
#    memory due to the usage of ulimit where slurm enforces real memory

cmd="sbatch --time="""$mins:$secs""" --nodes="""$MIG_JOBNODECOUNT""" --exclusive \
    --no-requeue --job-name="""$MIG_JOBNAME""" \
    -o """$MIG_LRMS_OUT""" -e """$MIG_LRMS_ERR""" --workdir="""$MIG_JOBDIR""" \
    $mail_opt -p """$MIG_EXENODE""" $@"
$cmd
if [ $? -ne 0 ]; then
    echo "Submit command: $cmd"
    echo "Failed to submit to SLURM - try again later"
    exit 1 
fi
