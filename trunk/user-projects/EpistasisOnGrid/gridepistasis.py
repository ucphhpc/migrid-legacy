"""

"""

#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import os
import sys

sys.path.append('Configuration/')
import epistasisconfiguration as configuration
sys.path.append('Gridinterface/')

import migsession
sys.path.append('misc/')

from mylogger import log
from jobfragmentation import fragment_epistasis, get_job_specs

class GridEpistasis:
    """Start an epistasis procedure either executed on grid og locally."""
    def __init__(self, debug_mode=False):
        self.jobs_done = []
        self.epistasis_jobs = []
        self.all_jobs = []
        self.epistasis_status = 'idle'
        self.num_jobs = 0
        self.logfile = ""
        self.debug_mode = debug_mode
        self.main_output_dir = ""
        #self.mig_session = ""

########### UPDATE / STATUS ###############
    
    def get_epistasis_status(self):
        """Return the status of the jobs and a progress indicator to be displayed in GUI."""
        self.mig_session.update_jobs(self.epistasis_jobs)
        for j in self.epistasis_jobs:
            if j['status']['STATUS'] == 'FINISHED':
                self.jobs_done.append(j)
                self.epistasis_jobs.remove(j)
                #self.mig_session.handle_output(j)
                output_files = self.mig_session.handle_output(j)
                for f in output_files:
                    self.extract_output(f,  self.main_output_dir+j['results_dir'])

        if self.num_jobs == len(self.jobs_done):
            log(self.logfile, 'All jobs completed', self.debug_mode)
            self.epistasis_status = 'finished'

        progress_str = str(len(self.jobs_done)) + '/'\
             + str(self.num_jobs)
        status_lines = self.create_status_feed(self.epistasis_jobs)
        status_lines.extend(self.create_status_feed(self.jobs_done))
        status = ''
        for line in status_lines:
            status += line + '\n'
        return (status, progress_str)

    def create_status_feed(self, jobs):
        """Return a status string for each job"""
        feed = []
        for j in jobs:
            line = self.create_status_str(j)
            feed.append(line)
        return feed

    def create_status_str(self, job):
        """Return a status string for a job"""
        status_str = 'Epistasis \t - class '
        for val in job['class']:
            status_str += str(val) + ' ' 
        status_str += '\t - genes  '
        for gene in job["gene_list"]:
            status_str += str(gene) + ' ' 
        status_str += '-'+ '\t' + job['status']['STATUS']
        if job['status']['STATUS'] != "EXECUTING":
            status_str += "\t"
        status_str += ' \t started:'+job["started"]+'\t \t ended:'+job["finished"]
        return status_str

    def monitor_epistasis(self):
        """Monitor the epistasis procedure."""
        jobs_done = []
        jobs = self.epistasis_jobs

    # mylogger.logprint(logfile, "Started monitoring")

        while True:
            try:
                self.mig_session.update_jobs(jobs)
                for j in jobs:
                    if j['status']['STATUS'] == 'FINISHED':
                        output_files = self.mig_session.handle_output(j)
                        for f in output_files:
                            self.extract_output(f,  self.main_output_dir+j['results_dir'])
                        
                        jobs_done.append(j)
                        jobs.remove(j)
                        
                        #log(self.logfile, 'Job ' + j['id'] + ' done.', self.debug_mode)
                        print 'Job ' + j['id'] + ' done.'
                if jobs == []:

                # mylogger.logprint(logfile, "All jobs completed")
                    self.print_status(jobs_done)
                    print 'all jobs completed'
                    return
                self.print_status(jobs)
                self.print_status(jobs_done)
                time.sleep(configuration.monitor_polling_frequency)
            except KeyboardInterrupt:
                print 'User initiated cancellation of jobs'
                self.mig_session.cancel_jobs(jobs)
                return
        return jobs_done


    def extract_output(self,tar_file_path, dest_dir):
        import tarfile
        
        new_dir = dest_dir+tar_file_path.split("/")[-1].strip(".tar.gz")
        if not os.path.exists(new_dir):
            os.mkdir(new_dir)
        prog_files = tarfile.open(tar_file_path, "r")
            
        prog_files.extractall(path=new_dir)
        prog_files.close()


# ######### START EPISTASIS ############

    def start_epistasis( 
        self,
        selection_variable_values = configuration.default_variable_values,
        genelist=configuration.default_gene_list,
        traitlist=configuration.default_trait_list,
        selection_variable=configuration.default_selection_variable_index,
        data=configuration.data_file,
        output_dir=configuration.output_dir,
        job_size=configuration.default_job_size,
        local_mode=False,
        ):
        """Start the epistasis procedure."""

        #selection_variable_index = str(select_variable)
 
            #    selection_variable_values = \
        #        configuration.selection_variable_range[selection_variable_index]
        #else:
        #    selection_variable_values = range(int(class1), int(class2) + 1, 1)
        #selection_variable_values = classlist
        #job_size = 1  
        #print 'SVvals: ' + str(selection_variable_values)
        #print 'JS: ' + str(job_size)
        
        #job_size = 1
        epi_jobs, project_dir = create_epistasis_jobs(
            job_size,
            genelist=genelist,
            traitlist=traitlist,
            selection_var=selection_variable,
            variable_values=selection_variable_values,
            data_file=data,
            output_dir=output_dir,
            run_local=local_mode,
            )

        #self.print_jobs(epi_jobs)

        self.main_output_dir = output_dir
        
        if not output_dir[-1] == "/":
            output_dir += "/"
        output_dir = output_dir+project_dir

        self.logfile = output_dir+configuration.logfile_name
            
        os.mkdir(output_dir)
        self.mig_session = \
            migsession.MigSession(output_dir, self.logfile, local_mode, self.debug_mode)
        self.mig_session.create_mig_jobs(epi_jobs, configuration.Epistasis_working_dir)
        self.epistasis_jobs.extend(epi_jobs)
        self.all_jobs.extend(epi_jobs)
        self.num_jobs = len(epi_jobs)


# ######### STOP /CANCEL ##############

    def stop_epistasis(self):
        """Stop the epistasis procedure."""
        self.mig_session.cancel_jobs(self.epistasis_jobs)

# ##### PRINT ###########

    def print_jobs(self, jobs):
        """Print jobs."""
        for i in range(len(jobs)):
            print 'job ' + str(i) + ' : ' + str(jobs[i])

    def print_status(self, jobs):
        """Print job status."""
        full_str = []
        for j in jobs:
            status_str = 'Job : ' + j['id'] + '\t' + j['status'
                    ]['STATUS']
            print status_str
            full_str.append(status_str)
        return full_str

# ### CLEAN UP ########

    def clean_up_epistasis(self):
        """Delete files used in the epistasis procedure that are no longer needed."""
        self.mig_session.clean_up(self.all_jobs)

# ##### CREATE JOBS#############

def create_epistasis_jobs(
    job_size,
    genelist,
    traitlist,
    selection_var,
    variable_values,
    data_file,
    output_dir,
    run_local=False,
    ):
    """Return epistasis jobs that execute the epistasis procedure."""
    #values = configuration.selection_variable_range[str(selection_var)]
    #job_fragments = fragment_epistasis(classes=variable_values, genes=genelist, traits=traitlist, job_size=job_size)
    job_fragments = fragment_epistasis(job_size, values=variable_values)
    #print 'classes ' + str(job_classes), job_size, vals
    jobs = []
    ser_number = 1

    time_list = time.localtime(time.time())
    project_tag = str(time_list[2]) + '_' + str(time_list[1]) + '_'\
         + str(time_list[0]) + '_' + str(time_list[3])\
         + str(time_list[4]) + str(time_list[5])

    for j in job_fragments:
       
        job = create_init_job()
        classes = j
        #genes = 
        #, traits 
        #= j #get_job_specs(j)
        #print  classes, genes, traits 
        job['project_tag'] = project_tag
        job['class'] = classes
        #job['gene_index_1'] = gene1
        #job['gene_index_2'] = gene2
        #job['trait_index_1'] = trait1
        #job['trait_index_2'] = trait2
               #job["input_args_file"] = job_args_file
        job['gene_list'] = genelist
        job['trait_list'] = traitlist
        job['user_output_dir'] = output_dir
        job['data_file'] = data_file.split('/')[-1]
        job['selection_variable'] = selection_var
        job['selection_var_values'] = variable_values
        output_filename = 'epifiles' + str(ser_number) + '.tar.gz'
        job_directory = configuration.tmp_local_job_dir\
             + str(ser_number) + '_' + project_tag + '/'
        job['job_dir'] = configuration.Epistasis_working_dir\
             + job_directory
        job['output_files'] = [output_filename]
        job_results_dir = configuration.resultsdir_prefix_name + project_tag +"/"
        job['results_dir'] = job_results_dir

        job_cmds = ['python '+ job['main_script']]

        # mig settings

        job['commands'] = job_cmds
        input_files = list(configuration.program_files)
        input_files.append(data_file)
        job['input_files'] = input_files
        job['resource_specs'] = configuration.resource_specs

        # job test DELETE
       # job['output_files'] = ["testfil.txt"]
        #job['commands'] =  ['cd ' + job['job_dir'], "echo testinhold > testfil.txt"]
        
        #os.mkdir(job_results_dir)
        #os.mkdir(job['job_dir'])
        if run_local:
            job['r_bin'] = 'R'
        else:
            job['r_bin'] = '$R_HOME/bin/R'

        #print job
        jobs.append(job)
        ser_number += 1
    
    return jobs, job_results_dir


def create_init_job():
    """Return an initial epistasis job."""
    init_job = {}
    init_job["main_r_file"] = configuration.main_r_file
    init_job['r_files'] = configuration.r_files
    init_job['main_script'] = configuration.main_script
    init_job['output_dir'] = configuration.output_dir
    init_job["started"] = "---"
    init_job["finished"] = "---"
    return init_job

"""
def mig_call(func,*args):
    #print args
    #funct = "miglib."+func
    #print func, args
    try:
        out = func(*args)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise
        

        return out
#print out
    #exit_code = get_exit_code(out)
    
    #print "exit code", exit_code
    #if exit_code != 0:
    #   raise Exception("MiG Error: \n"+str(func)+":"+str(args)+"\n"+"".join(out))
"""


# ##### MAIN ###############

    # Arguments are entered in the order: selectionvariableindex jobsize

if __name__ == '__main__':
    local = False
    debug = False
    if '-local' in sys.argv or '-l' in sys.argv:
        local = True
    if '-debug' in sys.argv or '-d' in sys.argv:
        debug = True

    NEW_EPISTASIS = GridEpistasis(debug_mode=debug)
    NEW_EPISTASIS.start_epistasis(local_mode=local)
    NEW_EPISTASIS.monitor_epistasis()
    NEW_EPISTASIS.clean_up_epistasis()
