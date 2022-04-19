# sac and mseed file process functions using SAC and ObsPy

def mseed2sac(input_mseed_file, output_sac_file,
    detrend=True, detrend_method='spline', detrend_order=4, dspline=86400,
    taper=True, taper_type='hann', taper_max_perc=0.050,
    SAC='/usr/local/sac/bin/sac'):
    pass



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


