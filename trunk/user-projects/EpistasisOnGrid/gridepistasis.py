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


class GridEpistasis:
    """Start an epistasis procedure either executed on grid og locally."""
    def __init__(self):
        self.jobs_done = []
        self.epistasis_jobs = []
        self.all_jobs = []
        self.epistasis_status = 'idle'
        self.num_jobs = 0
        self.mig_session = ""

# ########## UPDATE / STATUS ###############

    def get_epistasis_status(self):
        """Return the status of the jobs and a progress indicator to be displayed in GUI."""
        self.mig_session.update_jobs(self.epistasis_jobs)
        for j in self.epistasis_jobs:
            if j['status']['STATUS'] == 'FINISHED':
                self.jobs_done.append(j)
                self.epistasis_jobs.remove(j)
                self.mig_session.handle_output(j)

        if self.num_jobs == len(self.jobs_done):
            print 'all jobs completed'
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
        status_str = 'Epistasis for class '
        for val in job['class']:
            status_str += str(val) + ' ' 
        status_str += '\t' + '\t' + job['status']['STATUS']
        status_str += '\t started:'+job["started"]+'\t ended:'+job["finished"]
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
                        self.mig_session.handle_output(j)
                        jobs_done.append(j)
                        jobs.remove(j)
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

# ######### START EPISTASIS ############

    def start_epistasis( 
        self,
        class1=0,
        class2=0,
        gene1=configuration.gene_first_index,
        gene2=configuration.gene_last_index,
        trait1=configuration.trait_first_index,
        trait2=configuration.trait_last_index,
        select_variable=configuration.selection_variable_index,
        data=configuration.data_file,
        output_dir=configuration.output_dir,
        local_mode=False
        ):
        """Start the epistasis procedure."""
                
        selection_variable_index = str(select_variable)
        if class2 == 0:
            selection_variable_values = \
                configuration.selection_variable_range[selection_variable_index]
        else:
            selection_variable_values = range(int(class1), int(class2) + 1, 1)
        job_size = 1  
        print 'SVvals: ' + str(selection_variable_values)
        print 'JS: ' + str(job_size)

        epi_jobs = create_epistasis_jobs(
            job_size,
            gene1=gene1,
            gene2=gene2,
            trait1=trait1,
            trait2=trait2,
            selection_var=select_variable,
            variable_values=selection_variable_values,
            data_file=data,
            output_dir=output_dir,
            run_local=local_mode,
            )

        self.print_jobs(epi_jobs)
        
        self.mig_session = \
            migsession.MigSession(configuration.main_results_dir,
                                  local_mode)
        self.mig_session.create_mig_jobs(epi_jobs)
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

# fragments the epistasis procedure into jobs of classes


def fragment_epistasis(job_size, values):
    """Return a list of sub jobs of size job_size."""
    value_range = []
    current_size = 0
    job_classes = []
    for i in range(len(values)):
        value_range.append(values[i])
        current_size += 1
        if current_size == job_size:
            job_classes.append(value_range)
            value_range = []
            current_size = 0
    if value_range != []:
        job_classes.append(value_range)
    print job_classes

    return job_classes

def create_epistasis_jobs(
    job_size,
    gene1=configuration.gene_first_index,
    gene2=configuration.gene_last_index,
    trait1=configuration.trait_first_index,
    trait2=configuration.trait_last_index,
    selection_var=configuration.selection_variable_index,
    variable_values=configuration.default_variable_values,
    data_file=configuration.data_file,
    output_dir=configuration.output_dir,
    run_local=False,
    ):
    """Return epistasis jobs that execute the epistasis procedure."""
    #values = configuration.selection_variable_range[str(selection_var)]
    job_classes = fragment_epistasis(job_size, variable_values)
    #print 'classes ' + str(job_classes), job_size, vals
    jobs = []
    ser_number = 1

    time_list = time.localtime(time.time())
    project_tag = str(time_list[2]) + '_' + str(time_list[1]) + '_'\
         + str(time_list[0]) + '_' + str(time_list[3])\
         + str(time_list[4]) + str(time_list[5])

    for j in job_classes:
        job = create_init_job()
        job['project_tag'] = project_tag
        job['class'] = j
        job['gene_index_1'] = gene1
        job['gene_index_2'] = gene2
        job['trait_index_1'] = trait1
        job['trait_index_2'] = trait2
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
        job['results_dir'] = \
            configuration.resultsdir_prefix_name + project_tag\
             + '/'

        job_cmds = ['cd ' + job['job_dir'], 'python '
                     + job['main_script']]

        # mig settings

        job['commands'] = job_cmds
        input_files = list(configuration.program_files)
        input_files.append(data_file)
        job['input_files'] = input_files
        
        job['resource_specs'] = configuration.resource_specs

        os.mkdir(job['job_dir'])
        if run_local:
            job['r_bin'] = 'R'
        else:
            job['r_bin'] = '$R_HOME/bin/R'

        print job
        jobs.append(job)
        ser_number += 1
    return jobs


def create_init_job():
    """Return an initial epistasis job."""
    init_job = {}
    init_job['r_files'] = configuration.r_files
    init_job['main_script'] = configuration.main_script
    init_job['output_dir'] = configuration.output_dir
    init_job["started"] = "---"
    init_job["finished"] = "---"
    return init_job


# ##### MAIN ###############

    # Arguments are entered in the order: selectionvariableindex jobsize

if __name__ == '__main__':
    local = False
    if '-local' in sys.argv or '-l' in sys.argv:
        local = True


    NEW_EPISTASIS = GridEpistasis()
    NEW_EPISTASIS.start_epistasis(local_mode=local)
    NEW_EPISTASIS.monitor_epistasis()
    NEW_EPISTASIS.clean_up_epistasis()

