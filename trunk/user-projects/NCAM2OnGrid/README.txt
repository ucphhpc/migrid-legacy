= Introduction =
The NCAM2 project is driven by a group of people from Biostructural
Research, Department of Medicinal Chemistry, Faculty of Pharmaceutical
Sciences at the University of Copenhagen.
It investigates structure and dynamics of neural cell adhesion molecule 2 (NCAM2).
As Farma are the experts on the molecular dynamics they take care of all the
work in that domain and only rely on us for the actual Grid execution.
The investigation mainly uses the AMBER software (http://ambermd.org/) to
simulate the molecular dynamics.
A more detailed description of the project is available in
DCSC-NCAM2.doc in this folder.


= Grid preparations =
The total amount of computations associated with the NCAM2 project is
significantly higher than what their local resources can provide in a
reasonable time frame, so they have been granted a so-called 'sandkasse'-slot
on the DCSC resources.
The individual simulations are CPU bound and single node multicore execution is
the most efficient approach. Each simulation requires only limited memory and
disk so most multi core resources will do.
AMBER is not free software but we have received permission to install it on the
DCSC resources in accordance with the 'site license'. Thus we install it on a
resource by resource basis on the DCSSC locations where we can obtain the
necessary compute time.
Initially the Grid execution will be handled solely by Patrik from Farma, but
in the longer run more users are expected. Therefore we decided to create a
Farma-BR virtual organization (VGrid) for the project, to ease resource access
control and project collaboration.


= AMBER jobs on MiG =
AMBER is not generally available on all resources and we must limit access due
to the license restrictions. Therefore we created a runtime environment used to
direct jobs onto the suitable resources and limited access to resources with
AMBER installed with the Farma-BR VGrid. 


== Building AMBER ==
Please refer to the amber directory for details about the actual installation.


== Running AMBER jobs ==
In genereal jobs must specify the AMBER10 and OPENMPI runtime
environments to run on suitable resources. For this particular setup
they additionally need to be sent to the Farma-BR VGrid.
Apart from that it is just a matter of specifying input and output along
with resource hardware requirements and walltime.

Jobs are prepared by creating input files just like if the execution was
not on Grid. First generate topology and coordinate files using tleap
(or xleap, sleap) on your local system. 
Create an input file for sander or pmemd using your favourite text
editor.

MiG execution requires upload of these three files to your MiG home.
When you submit the job make sure to include the following in your mRSL
(replace all file names with your file names).
The execute line is for a 8 cpu job with sander, replace sander.MPI with
pmemd when using pmemd. Pmemd scales much better with multiple cpu's.

::EXECUTE::
$MPI_HOME/bin/mpirun -np 8 $AMBER_BIN_DIR/sander.MPI -i inputfile -o outputfile -r restartfile -c coordinatefile

::INPUTFILES::
inputfile
coordinatefile
topologyfile

::OUTPUTFILES::
outputfile
restartfile

::RUNTIMEENVIRONMENT::
AMBER10
OPENMPI


With few jobs to run these mRSL contents are simply submitted to MiG
through the web interface and the results are then analysed one by one
as they come in. For projects with a lot of jobs the command line
scripts combined with scripted pre and post processing may be more
suitable.


= Contacts =
Our technical reference at Farma is Patrik Rydberg <pry AT farma.ku.dk>
and Jonas Bardino <bardino AT diku.dk> is the MiG representative.

 
