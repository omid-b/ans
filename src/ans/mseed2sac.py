
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
    SAC = conf['setting']['le_sac']
    if not os.path.isfile(SAC):
        print(f"Error! could not find SAC software in the following path:\n{SAC}")
        exit(1)
    input_mseeds_dir = os.path.abspath(input_mseeds_dir)
    output_sacs_dir = os.path.abspath(output_sacs_dir)
    mseeds = generate_mseed_list(input_mseeds_dir)

    initialize_sac_directories(output_sacs_dir, mseeds)

    num_success = 0
    for mseed in mseeds:
        event_name = get_event_name(mseed)
        sacfile = os.path.join(output_sacs_dir, event_name, get_sac_name(mseed))
        if not os.path.isfile(sacfile):
            print(f"\nsac file: {os.path.split(sacfile)[1]}")
            success = True
            for i, process in enumerate(conf['mseed2sac']['mseed2sac_procs']):
                pid = process['pid']
                if success and pid == [1,1]:
                    print(f"    Process #{i+1}: MSEED to SAC")
                    detrend = is_true(process['chb_mseed2sac_detrend'])
                    taper = is_true(process['chb_mseed2sac_taper'])
                    detrend_method = process['cmb_mseed2sac_detrend_method']
                    detrend_order = int(process['sb_mseed2sac_detrend_order'])
                    dspline = int(process['le_mseed2sac_dspline'])
                    taper_type = process['cmb_mseed2sac_taper_method']
                    taper_max_perc = float(process['dsb_mseed2sac_max_taper'])
                    
                    if detrend_method == 0:
                        detrend_method = "demean"
                    elif detrend_method == 1:
                        detrend_method = "linear"
                    elif detrend_method == 2:
                        detrend_method = "polynomial"
                    elif detrend_method == 3:
                        detrend_method = "spline"
                    
                    if taper_type == 0:
                        taper_type = 'hann'

                    success = proc.mseed2sac(mseed, sacfile,
                    detrend=detrend, detrend_method=detrend_method,
                    detrend_order=detrend_order, dspline=dspline,
                    taper=taper, taper_type=taper_type, taper_max_perc=taper_max_perc,
                    SAC=SAC)

                elif success and pid == [2,1]:
                    print(f"    Process #{i+1}: Remove extra channel")
                elif success and pid == [3,1]:
                    print(f"    Process #{i+1}: Decimate")
                elif success and pid == [4,1]:
                    print(f"    Process #{i+1}: Remove instrument response")
                elif success and pid == [5,1]:
                    print(f"    Process #{i+1}: Bandpass filter")

            if not success and os.path.isfile(sacfile):
                os.remove(sacfile)
                print("* Process failed! Output file was removed.")
            else:
                num_success += 1

    print(f"\nTotal number of MSEED files: {len(mseeds)}\nNumber of successfully processed SAC files: {num_success}\n\nDone!\n")

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



