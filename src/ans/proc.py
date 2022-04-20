# sac and mseed file process functions using SAC and ObsPy

import os
import sys
import obspy
import numpy as np
import subprocess


def mseed2sac(input_mseed_file, output_sac_file,
    detrend=True, detrend_method='spline', detrend_order=4, dspline=86400,
    taper=True, taper_type='hann', taper_max_perc=0.050,
    SAC='/usr/local/sac/bin/sac'):
    
    try:
        st = obspy.read(input_mseed_file, format="MSEED")

        # start handling data fragmentation issue
        st.sort(['starttime'])
        
        data_starttime = obspy.UTCDateTime(st[0].stats.starttime)
        data_endtime = obspy.UTCDateTime(st[-1].stats.endtime)
        request_starttime = obspy.UTCDateTime(os.path.split(input_mseed_file)[1].split('_')[2]) # obspy.UTCDateTime()
        request_endtime = obspy.UTCDateTime(os.path.split(input_mseed_file)[1].split('_')[4].split('.')[0]) # obspy.UTCDateTime()
        request_length = int(request_endtime - request_starttime)
        begin_data = int(data_starttime.hour*3600 +
                         data_starttime.minute*60 +
                         data_starttime.second)
        begin_request = int(data_starttime.hour*3600 +
                            data_starttime.minute*60 +
                            data_starttime.second)

        if detrend:
            if detrend_method == 'spline':
                try:
                    st.detrend(detrend_method, order=detrend_order, dspline=dspline)
                except:
                    st.detrend('demean')
            elif detrend_method == 'polynomial':
                try:
                    st.detrend(detrend_method, order=detrend_order)
                except:
                    st.detrend('demean')
            else:
                st.detrend(detrend_method)

        if taper:
            st.taper(taper_max_perc)

        if len(st) > 1:# fix data fragmentation issue
            st.merge(method=1, fill_value=0)

        
        # set sac begin time and write to file
        st[0].stats.sac = obspy.core.AttribDict()
        st[0].stats.sac.b = begin_data
        st[0].stats.sac.iztype = 9
        st[0].stats.sac.lovrok = True
        st[0].stats.sac.lcalda = True
        st[0].write(output_sac_file, format='SAC')
        
        # cut to correct b to e and fill with zeros
        shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
        shell_cmd.append(f"cuterr fillz")
        shell_cmd.append(f"cut {begin_request} {begin_request + request_length}")
        shell_cmd.append(f"r {output_sac_file}")
        shell_cmd.append(f"w over")
        shell_cmd.append(f"q")
        shell_cmd.append('EOF')
        shell_cmd = '\n'.join(shell_cmd)
        subprocess.call(shell_cmd, shell=True)

        # reload sac file, set sac begin time to zero, and write to file
        st = obspy.read(output_sac_file, format='SAC')
        st[0].stats.sac = obspy.core.AttribDict()
        st[0].stats.sac.b = 0
        st[0].write(output_sac_file, format='SAC')

        return True
    
    except Exception as e:
        return False




def sac_remove_extra_channels(sacs_event_dir, similar_channels, channel2keep,
    SAC='/usr/local/sac/bin/sac'):
    pass



def sac_decimate(input_sacfile, output_sacfile, final_sampling_freq,
    SAC='/usr/local/sac/bin/sac'):
    pass



def sac_remove_response(input_sacfile, output_sacfile, xml_file,
    unit='VEL', prefilter=[0.001, 0.005, 45, 50]):
    pass



def sac_bandpass_filter(input_sacfile, output_sacfile,
    cp1, cp2, n=3, p=2,
    SAC='/usr/local/sac/bin/sac'):
    pass


