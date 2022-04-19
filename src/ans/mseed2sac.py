
import os
import obspy
import re
import shutil
from . import config
from . import proc

#==== MAIN FUNCTION ====#

regex_mseeds = re.compile('^.*[1-2][0-9][0-9][0-9][0-1][0-9][0-3][0-9]T[0-2][0-9][0-5][0-9][0-5][0-9]Z\.(mseed)$')
regex_events = re.compile('^[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]$')


def mseed2sac_run_all(maindir):
    conf = config.read_config(maindir)
    input_mseeds_dir = conf['mseed2sac']['mseed2sac_input_mseeds']
    output_sacs_dir = conf['mseed2sac']['mseed2sac_output_sacs']
    mseeds = generate_mseed_list(input_mseeds_dir)
    initialize_sac_directories(output_sacs_dir, mseeds)

    for mseed in mseeds:
        event_name = get_event_name(mseed)
        sacfile = os.path.join(output_sacs_dir, event_name, get_sac_name(mseed))
        first_proc_pid = conf['mseed2sac']['mseed2sac_procs'][0]['pid']
        if first_proc_pid == [1,1]: # convert mseed to sac
            pass


#========================#



def generate_mseed_list(mseeds_dir):
    mseed_list = []
    if not os.path.isdir(mseeds_dir):
        print()
    for x in os.listdir(mseeds_dir):

        if os.path.isdir(os.path.join(mseeds_dir, x)):
            if regex_events.match(x):
                for xx in os.listdir(os.path.join(mseeds_dir, x)):
                    if regex_mseeds.match(xx):
                        mseed_list.append(os.path.join(mseeds_dir, x, xx)) 
        else:
            if regex_mseeds.match(x):
                mseed_list.append(os.path.join(mseeds_dir, x))
    return mseed_list


def get_sac_name(mseed_file):
    event_name = get_event_name(mseed_file)
    mseed_file = os.path.split(mseed_file)[1]
    sac_name = "%s_%s.%s" %(event_name, mseed_file.split('_')[0].split('.')[1], mseed_file.split('_')[0].split('.')[3])
    return sac_name



def get_event_name(mseed_file):
    mseed_file = os.path.split(mseed_file)[1]
    event_utc_time = obspy.UTCDateTime(mseed_file.split('_')[2])
    event_name = "%02d%03d%02d%02d%02d" %(int(str(event_utc_time.year)[2:]),
                                        event_utc_time.julday,
                                        event_utc_time.hour,
                                        event_utc_time.minute,
                                        event_utc_time.second)
    return event_name



def initialize_sac_directories(sacs_maindir, mseed_list):
    if not os.path.isdir(sacs_maindir):
        os.mkdir(sacs_maindir)
    for mseed in mseed_list:
        event_name = get_event_name(mseed)
        event_dir = os.path.join(sacs_maindir, event_name)
        if not os.path.isdir(event_dir):
            os.mkdir(event_dir)


def sacfile_process_failed(sacfile):
    if os.path.isfile(sacfile):
        os.remove(sacfile)


def finalize_sac_directories(sacs_maindir, mseed_list):
    for mseed in mseed_list:
        event_dir = os.path.join(sacs_maindir, get_event_name(mseed))
        if os.path.isdir(event_dir):
            if not len(os.listdir(event_dir)):
                shutil.rmtree(event_dir)



