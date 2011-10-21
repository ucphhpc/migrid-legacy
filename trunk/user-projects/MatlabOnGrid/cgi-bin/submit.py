#!/usr/bin/python 

import subprocess, os
import cgi
import cgitb
import time
import gridmatlab.configuration as config
from gridmatlab.miscfunctions import upload_file, log, load_solver_data


cgitb.enable()

grid_solver = config.grid_application_exec

work_dir = config.working_dir
    
def create_unique_name(name):
    newname = ""
    serialnr = 2
    while True:
        newname = name+"_"+str(serialnr)
        if not os.path.exists(os.path.join(config.jobdata_directory, newname)):
            break
        serialnr += 1
    return newname
            
    
def main(form):
    log(form)
    num_jobs = "2" # default
    start_timestep = 81
    end_timestep = 1
    
    local_mode = False
    local_mode_flag = ""
    name = ""
    if form.has_key("process_name"):
        name = form["process_name"].value
    
    if os.path.exists(os.path.join(config.jobdata_directory, name)):
        name = create_unique_name(name)
    
    if form.has_key("num_jobs"):
        num_jobs = form["num_jobs"].value
    
    if int(num_jobs) > 100 or not int(num_jobs): # max 100 jobs
        return False
    
    
    if form.has_key("start_timestep"):
        start_timestep = form["start_timestep"].value
    
    if form.has_key("end_timestep"):
        end_timestep = form["end_timestep"].value
    
    
    if form.has_key("local_mode"):
        local_mode = form["local_mode"].value
    
    files = []
    for i in range(100):
        tag = "file"+str(i)
        if form.has_key(tag) and form[tag].value:
            file_path = form[tag].filename
            filename = os.path.join(config.upload_directory, os.path.basename(file_path))
            upload_file(form[tag], filename)
            files.append(filename)
        else: 
            break
     
    if local_mode:
        local_mode_flag = "-l"
        log("local mode!")
    
    files.append(config.matlab_binary) # get the bin file launched by the bash file
    
    cmd = "python %s %s %s %s -n %s %s -t %s %s -i %s" % (grid_solver, name, config.matlab_executable, config.matlab_binary , num_jobs, local_mode_flag, start_timestep, end_timestep," ".join(files))#" ".join(index_files))
    
    log("starting : "+cmd)
    
    output_file = config.server_proc_output
    output_handle = open(output_file, "a")
    proc = subprocess.Popen(cmd, cwd=work_dir, shell=True, stdout=output_handle, stderr=output_handle, close_fds=True)
    
    time.sleep(5) # sleep for a short period while process starts 
    return_code = proc.poll()  # check if it terminated already
    output = ""
    if return_code != None: 
        output = "\nProcess terminated. Return code %i. \n " % return_code
    else : 
        
        # wait for the monitor to get ready
        solver_data_file = os.path.join(config.jobdata_directory, name, config.solver_data_file)
        while not os.path.exists(solver_data_file): 
            time.sleep(2)
            
        #monitor_link = "<a target='_blank' href='/cgi-bin/monitor.py?solver_name=%s'>%s</a>" % (name, name)
        monitor_link = "<a target='main' href='/cgi-bin/monitor.py?solver_name=%s'>%s</a>" % (name, name)
        output = "Process started. Click to go to grid process monitor: "+monitor_link
    
    head = "<html><head></head>"
    text = "<body>%s</body>" % output
    text += "</html>"
    print "Content-type: text/html"
    print 
    print head
    print text
    
    
    

main(cgi.FieldStorage())
    
    