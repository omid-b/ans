
import os
import obspy
import re
import shutil
from . import config
from . import proc

#==== MAIN FUNCTION ====#

regex_mseeds = re.compile('^.*[1-2][0-9][0-9][0-9][0-1][0-9][0-3][0-9]T[0-2][0-9][0-5][0-9][0-5][0-9]Z\.(mseed)$')
regex_events = re.compile('^[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]$')


def mseed2sac_run_all(maindir, input_mseeds_dir, output_sacs_dir):
    conf = config.read_config(maindir)
    input_mseeds_dir = os.path.abspath(input_mseeds_dir)
    output_sacs_dir = os.path.abspath(output_sacs_dir)
    mseeds = generate_mseed_list(input_mseeds_dir)

    initialize_sac_directories(output_sacs_dir, mseeds)

    for mseed in mseeds:
        event_name = get_event_name(mseed)
        sacfile = os.path.join(output_sacs_dir, event_name, get_sac_name(mseed))
        success = True
        for process in conf['mseed2sac']['mseed2sac_procs']:
            pid = process['pid']
            if success and pid == [1,1]:
                # input_mseed_file, output_sac_file,
                # detrend=True, detrend_method='spline', detrend_order=4, dspline=86400,
                # taper=True, taper_type='hann', taper_max_perc=0.050,
                # SAC='/usr/local/sac/bin/sac'
                detrend = is_true(process)

            elif success and pid == [2,1]:
                pass
            elif success and pid == [3,1]:
                pass
            elif success and pid == [4,1]:
                pass
        if not success and os.path.isfile(sacfile):
            os.remove(sacfile)

    # finalize_sac_directories(output_sacs_dir, mseeds)


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


def is_true(value):
    value = int(value)
    if value < 1:
        return False
    else:
        return True



def finalize_sac_directories(sacs_maindir, mseed_list):
    for mseed in mseed_list:
        event_dir = os.path.join(sacs_maindir, get_event_name(mseed))
        if os.path.isdir(event_dir):
            if not len(os.listdir(event_dir)):
                shutil.rmtree(event_dir)
    if not len(os.listdir(sacs_maindir)):
        shutil.rmtree(sacs_maindir)
        print("Error! No sac files were generated!\n")



