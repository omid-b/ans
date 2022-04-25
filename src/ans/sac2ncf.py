
import os
import obspy
import re
import shutil
from . import config
from . import proc

#==== MAIN FUNCTION ====#

regex_events = re.compile('^[1-2][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]$')
regex_sacs = re.compile('^[1-2][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]\_.*\..*$')


def sac2ncf_run_all(maindir, input_sacs_dir, output_ncfs_dir):
    input_sacs_dir = os.path.abspath(input_sacs_dir)
    output_ncfs_dir = os.path.abspath(output_ncfs_dir)
    conf = config.read_config(maindir)
    SAC = conf['setting']['le_sac']

    if not os.path.isdir(output_ncfs_dir):
        os.mkdir(output_ncfs_dir)
    
    events = get_events(input_sacs_dir)
    for event in events:
        inp_event = os.path.join(input_sacs_dir, event)
        out_event = os.path.join(output_ncfs_dir, event)
        copy_event(inp_event, out_event)
        for sacfile in get_sacs(out_event):
            print(f"\nsac file: {sacfile}")
            sacfile = os.path.join(out_event, sacfile)
            success = True
            for i, process in enumerate(conf['sac2ncf']['sac2ncf_procs']):
                pid = process['pid']
                if success and pid == [1,1]:
                    print(f"    Process #{i+1}: Decimate (SAC method)")

                    final_sampling_freq = process['cmb_sac2ncf_final_sf']
                    if final_sampling_freq == 1:
                        final_sampling_freq = 2
                    elif final_sampling_freq == 2:
                        final_sampling_freq = 5
                    elif final_sampling_freq == 3:
                        final_sampling_freq = 10
                    elif final_sampling_freq == 4:
                        final_sampling_freq = 20
                    else:
                        final_sampling_freq = 1

                    success = proc.sac_decimate(sacfile, sacfile, final_sampling_freq,
                    SAC=SAC)

                    if not success and os.path.isfile(sacfile):
                        os.remove(sacfile)

                elif success and pid == [1,2]:
                    print(f"    Process #{i+1}: Decimate (ObsPy method)")

                    final_sampling_freq = process['cmb_sac2ncf_final_sf']
                    if final_sampling_freq == 1:
                        final_sampling_freq = 2
                    elif final_sampling_freq == 2:
                        final_sampling_freq = 5
                    elif final_sampling_freq == 3:
                        final_sampling_freq = 10
                    elif final_sampling_freq == 4:
                        final_sampling_freq = 20
                    else:
                        final_sampling_freq = 1


                    success = proc.obspy_decimate(sacfile, sacfile, final_sampling_freq, SAC=SAC)

                    if not success and os.path.isfile(sacfile):
                        os.remove(sacfile)

                elif success and pid == [2,1]:
                    print(f"    Process #{i+1}: Remove instrument response")
                    mseeds = conf['download']['le_mseeds']
                    xmldir = process['le_sac2ncf_stametadir']
                    xmldir_2 = os.path.join(maindir, mseeds, event)
                    unit = process['cmb_sac2ncf_resp_output']
                    prefilter = process['cmb_sac2ncf_resp_prefilter']
                    if unit == 0:
                        unit = 'DISP'
                    elif unit == 1:
                        unit = 'VEL'
                    elif unit == 2:
                        unit = 'ACC'

                    if prefilter == 0:
                        prefilter = None
                    elif prefilter == 1:
                        prefilter = [0.001, 0.005, 45, 50]

                    st = obspy.read(sacfile, headonly=True)
                    net = st[0].stats.network
                    sta = st[0].stats.station
                    chn = st[0].stats.channel
                    xml_fname = f"{net}.{sta}.{chn}"
                    if os.path.isfile(os.path.join(xmldir, xml_fname)):
                        xml_file = os.path.join(xmldir, xml_fname)
                    elif os.path.isfile(os.path.join(xmldir_2, xml_fname)):
                        xml_file = os.path.join(xmldir_2, xml_fname)
                    else:
                        print(f"    Error! Meta data was not found: {xml_fname}")
                        success = False
                        continue

                    success = proc.sac_remove_response(sacfile, sacfile, xml_file,
                                                       unit=unit, prefilter=prefilter,
                                                       SAC=SAC)

                    if not success and os.path.isfile(sacfile):
                        os.remove(sacfile)

                elif success and pid == [3,1]:
                    print(f"    Process #{i+1}: Bandpass filter")

                    cp1 = process['le_sac2ncf_bp_cp1']
                    cp2 = process['le_sac2ncf_bp_cp2']
                    n = process['sb_sac2ncf_bp_poles']
                    p = process['sb_sac2ncf_bp_passes']
                    
                    success = proc.sac_bandpass_filter(sacfile, sacfile,
                                        cp1=cp1, cp2=cp2, n=n, p=p,
                                        SAC=SAC)

                    if not success and os.path.isfile(sacfile):
                        os.remove(sacfile)

                elif success and pid == [4,1]:
                    print(f"    Process #{i+1}: Cut seismograms")

                    try:
                        cut_begin = float(process['le_sac2ncf_cut_begin'])
                        cut_end = float(process['le_sac2ncf_cut_end'])
                    except Exception as e:
                        print(f"    Error! Cut begin/end values are not set properly!")
                        success = False

                    success = proc.sac_cut_fillz(sacfile, sacfile, cut_begin, cut_end, SAC=SAC)

                    if not success and os.path.isfile(sacfile):
                        os.remove(sacfile)

                elif success and pid == [5,1]:
                    print(f"    Process #{i+1}: Remove extra channels")

                    similar_channels = process['le_sac2ncf_similar_channels'].split()
                    channels2keep = process['le_sac2ncf_channels2keep'].split()

                    proc.sac_remove_extra_channels(sacs_event_dir=out_event,
                                                   similar_channels=similar_channels,
                                                   channels2keep=channels2keep)

                elif success and pid == [6,1]:
                    print(f"    Process #{i+1}: One-bit normalization")

                    if not success and os.path.isfile(sacfile):
                        os.remove(sacfile)
                elif success and pid == [7,1]:
                    print(f"    Process #{i+1}: Spectral whitening")

                    if not success and os.path.isfile(sacfile):
                        os.remove(sacfile)
                elif success and pid == [8,1]:
                    print(f"    Process #{i+1}: Cross-correlation")

        # remove input sac files
        # remove_event_sacs(out_event)
        

#=======================#

def get_events(dataset_dir):
    event_list = []
    for x in os.listdir(dataset_dir):
        if regex_events.match(x):
            event_list.append(x)
    return event_list


def get_sacs(event_dir):
    sac_files = []
    for x in os.listdir(event_dir):
        if regex_sacs.match(x):
            sac_files.append(x)
    return sac_files


def copy_event(src_event, dst_event):
    if not os.path.isdir(dst_event):
        os.mkdir(dst_event)
    sac_files = get_sacs(src_event)
    for sac_file in sac_files:
        src_sac = os.path.join(src_event, sac_file)
        dst_sac = os.path.join(dst_event, sac_file)
        shutil.copyfile(src_sac, dst_sac)


def remove_event_sacs(event_dir):
    sac_files = get_sacs(event_dir)
    for sac_file in sac_files:
        os.remove(os.path.join(event_dir, sac_file))

