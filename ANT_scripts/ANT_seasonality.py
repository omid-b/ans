#!/usr/local/bin/python

about = 'This script carries out seasonality analysis of seismic ambient noise cross-correlograms.\n'

usage = '''
# Usage 1: generate season-stacked cross-correlograms
> python3 ANT_seasonality.py  daily_xcorrs_dir  season_stack_dir  num_months

# Usage 2: group season-stacked cross-correlograms into four azimuthal groups
          (S-N, SW-NE, W-E, NW-SE) based on the azimuths of the interstation pairs
> python3 ANT_seasonality.py  season_stack_dir

# Usage 3: perform the seasonality analysis on the previously processed
          season-stacked cross-correlograms (usage 1 and 2)
> python3 ANT_seasonality.py  season_stack_dir  analysis_dir

---------------------------------------------------------------------
# daily_xcorrs_dir: path to the directory that contains cross-correlation 
                  daily record folders with "YYJJJ000000" naming format

# season_stack_dir: The results for season-stacked cross correlograms 
             containing (or will contain) folders with "??-??" naming format 
             where ?? are from 01 (January) to 12 (December)

# num_months: an integer that should be in [1, 2, 3, 4, 6]

# analysis_dir: This script will generate final results of the seasonality
                analysis into this directory; two directories
                will be generated in this folder:
                1) "seasonality_analysis_EGFs": 
                    analysis of individual EGFs
                2) "seasonality_analysis_region":
                    analysis of the entire region
'''

# Note: This script first symmetrizes EGFs before calculation of SNR values (usage 3)

# UPDATE: 27 Oct 2020
# CODED BY: omid.bagherpur@gmail.com
#====Adjustable Parameters=====#
SAC = "/usr/local/sac/bin/sac"  # path to SAC software

xcorr_dir_regex = '(^[0-9]{11})'
sacfile_regex = 'sac$'  # regular expression for sac files

# Usage 3 parameters:
seism_cut = 800 # xcorr limits in the plots (s)
signal_vel = [2, 5] # signal window velocity range (km/s)
bandpass_prd = [11, 20] # a list of two bandpass corner periods (s); empty list for no bandpass
correct_snr = True # True/False; correct snr values for number of stacks in xcorrs

# plot parameters:
figsize = 12 # a list of two numbers; [xSize, ySize]
figure_dpi = 150 # dpi = dot per inch
seismogram_amp_factor = 0.5 # affects the amplitude of EGFs in the EGF plots
seismogram_line_width = 0.5 # seismogram line width (pixels) in the EGF plots
sns_context = "talk" # seaborn context (paper, notebook, poster, talk); affects annotation size
#==============================#
import os
os.system('clear')
print(about)

# import required modules
try:
    import sys
    import re
    import obspy
    import shutil
    import subprocess
    import numpy as np
    import seaborn as sns
    import pandas as pd
    from glob import glob
    from datetime import datetime
    import matplotlib.pyplot as plt
except ImportError as e:
    print(f'Import Error!\n{e}\n')
    exit()

bp = False
if len(bandpass_prd) == 2:
    if bandpass_prd[0] < bandpass_prd[1]:
        bp = True
        cf1 = 1/bandpass_prd[1]
        cf2 = 1/bandpass_prd[0]
    else:
        print("Error in 'bandpass_prd' parameter; check 'Adjustable Parameters' section\n\n")
        exit()

#----FUNCTIONS----#

def get_seasons(num_months):
    season_months = []
    seasons_names = []
    for i in range(1,13):
        seas = []
        for j in range(num_months):
            if (i+j) < 13:
                seas.append(i+j)
            else:
                seas.append(i+j-12)
        season_months.append(seas)
        seasons_names.append(f'%02d-%02d' %(seas[0], seas[-1]))
    return season_months, seasons_names


def get_month(strDate):
    strDate = strDate[0:5]
    month = datetime.strptime(strDate, '%y%j').date().strftime('%m')
    return int(month)


def stack(stacklist, outsac):
    nStacked = 0
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    shell_cmd.append("fg line 0 0 delta 1 npts 172801 begin -86400")
    for xcorr in stacklist:
        nStacked += 1
        if nStacked == 1:
            sf = obspy.read(xcorr, format='SAC', headonly=True)
            kstnm = str(sf[0].stats.sac.kstnm)
            stla = float(sf[0].stats.sac.stla)
            stlo = float(sf[0].stats.sac.stlo)
            stel = float(sf[0].stats.sac.stel)
            evla = float(sf[0].stats.sac.evla)
            evlo = float(sf[0].stats.sac.evlo)
            evel = float(sf[0].stats.sac.evel)
            kcmpnm = str(sf[0].stats.sac.kcmpnm)
            knetwk = str(sf[0].stats.sac.knetwk)
        shell_cmd.append(f"addf {xcorr}")
    shell_cmd.append(f'w {outsac}')
    shell_cmd.append(f'r {outsac}')
    shell_cmd.append(f"chnhdr kevnm '{int(nStacked)}'")
    shell_cmd.append(f"chnhdr kstnm {kstnm}")
    shell_cmd.append(f"chnhdr stla {stla}")
    shell_cmd.append(f"chnhdr stlo {stlo}")
    shell_cmd.append(f"chnhdr stel {stel}")
    shell_cmd.append(f"chnhdr evla {evla}")
    shell_cmd.append(f"chnhdr evlo {evlo}")
    shell_cmd.append(f"chnhdr evel {evel}")
    shell_cmd.append(f"chnhdr kcmpnm {kcmpnm}")
    shell_cmd.append(f"chnhdr knetwk {knetwk}")
    shell_cmd.append(f'wh')
    shell_cmd.append('quit')
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd, shell=True)


def sym_sac(inpSac, outSac):
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    shell_cmd.append(f'r {inpSac}')
    if bp:
        shell_cmd.append(f'bp co {cf1} {cf2} n 3 p 2')
    shell_cmd.append('reverse')
    shell_cmd.append('w rev.tmp')
    shell_cmd.append(f'r {inpSac}')
    if bp:
        shell_cmd.append(f'bp co {cf1} {cf2} n 3 p 2')
    shell_cmd.append('addf rev.tmp')
    shell_cmd.append('div 2')
    shell_cmd.append(f'w {outSac}')
    shell_cmd.append('quit')
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd, shell=True)
    os.remove('rev.tmp')


def causal_sac(inpSac, outSac):
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    shell_cmd.append(f'cut 0 e')
    shell_cmd.append(f'r {inpSac}')
    if bp:
        shell_cmd.append(f'bp co {cf1} {cf2} n 3 p 2')

    shell_cmd.append(f'w {outSac}')
    shell_cmd.append('quit')
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd, shell=True)


def acausal_sac(inpSac, outSac):
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    shell_cmd.append(f'r {inpSac}')
    if bp:
        shell_cmd.append(f'bp co {cf1} {cf2} n 3 p 2')
    shell_cmd.append('reverse')
    shell_cmd.append('w rev.tmp')
    shell_cmd.append(f'cut 0 e')
    shell_cmd.append(f'r rev.tmp')
    shell_cmd.append(f'w {outSac}')
    shell_cmd.append('quit')
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd, shell=True)
    os.remove('rev.tmp')


def get_signal_window_times(inpSac):
    st = obspy.read(inpSac, format='SAC')
    dist = st[0].stats.sac.dist
    t1 = dist/signal_vel[1]
    t2 = dist/signal_vel[0]
    return [t1, t2]


def get_noise_window_times(inpSac):
    st = obspy.read(inpSac, format='SAC')
    dist = st[0].stats.sac.dist
    t0 = dist/signal_vel[1]
    t1 = dist/signal_vel[0]
    t2 = t0+ t1
    return [t1, t2]


def cut_sac(inpSac, outSac, t1, t2):
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    shell_cmd.append(f'cut {t1} {t2}')
    shell_cmd.append(f'r {inpSac}')
    if bp:
        shell_cmd.append(f'bp co {cf1} {cf2} n 3 p 2')
    shell_cmd.append(f'w {outSac}')
    shell_cmd.append('quit')
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd, shell=True)


def get_sac_data(inpSac):
    st = obspy.read(inpSac, format='SAC')
    b = st[0].stats.sac.b
    e = st[0].stats.sac.e
    delta = st[0].stats.sac.delta
    amps = st[0].data
    times = np.arange(b, e+delta, delta)
    return amps, times


def calc_snr(signal, noise):
    srms = np.sqrt(np.nanmean(np.square(signal)))
    nrms = np.sqrt(np.nanmean(np.square(noise)))
    snr = 10*np.log10((srms**2)/(nrms**2))
    return snr


def correct_snr_value(snr, nstack, mean_nstack):
    nstack_factor = np.sqrt(mean_nstack)/np.sqrt(nstack)
    corrected_snr = snr*nstack_factor
    return float(corrected_snr)


def get_direction(sacfile):
    st = obspy.read(sacfile, headonly=True)
    azimuth = float(st[0].stats.sac.baz)
    if azimuth < 22.5:
        direction = 'S-N'
    elif 337.5 <= azimuth or 157.5 <= azimuth < 202.5:
        direction = 'S-N'
    elif 22.5 <= azimuth < 67.5 or 202.5 <= azimuth < 247.5:
        direction = 'SW-NE'
    elif 67.5 <= azimuth < 112.5 or 247.5 <= azimuth < 292.5:
        direction = 'W-E'
    elif 112.5 <= azimuth < 157.5 or 292.5 <= azimuth < 337.5:
        direction = 'NW-SE'
    return direction

#-----------------#

usage1 = False
usage2 = False
usage3 = False

if len(sys.argv) == 4:
    usage1 = True
    daily_xcorrs_dir = os.path.abspath(sys.argv[1])
    season_stack_dir = os.path.abspath(sys.argv[2])
    num_months = int(sys.argv[3])
elif len(sys.argv) == 2:
    usage2 = True
    season_stack_dir = os.path.abspath(sys.argv[1])
elif len(sys.argv) == 3:
    usage3 = True
    season_stack_dir = os.path.abspath(sys.argv[1])
    analysis_dir = os.path.abspath(sys.argv[2])
else:
    print(f"Error Usage!\n{usage}\n")
    exit()

#====USAGE 1====#
if usage1:
    print('Usage 1: generate season-stacked cross-correlograms.\n\n')
    if os.path.isdir(season_stack_dir):
        print(f"Error Usage 1! 'season_stack_dir' should not exist! This script will create it!\n\n")
        exit()

    if num_months not in [1, 2, 3, 4, 6]:
        print(f"Error Usage 1! 'num_months' should be in [1, 2, 3, 4, 6]\n\n{usage}\n")
        exit()

    season_months, seasons_names = get_seasons(num_months)

    xcorrFolders = []
    xcorrMonth = {}
    for path in glob(f'{daily_xcorrs_dir}/*000000'):
        path =  os.path.basename(path)
        if re.search(xcorr_dir_regex, path):
            xcorrFolders.append(path)
            xcorrMonth[xcorrFolders[-1]] = get_month(xcorrFolders[-1])

    if len(xcorrFolders) == 0:
        print("Error Usage 1! No daily xcorr folder was found!\n\
    Check 'xcorr_dir_regex' parameter.\n\n")
        exit()

    print(' Collecting datasets information ...\n')

    sacfiles = {}
    for xcorrFolder in xcorrFolders:
        sacs = []
        for x in os.listdir(os.path.join(daily_xcorrs_dir, xcorrFolder)):
            if re.search(sacfile_regex, x):
                sacs.append(os.path.basename(x))
        
        if len(sacs) > 0:
            sacfiles[xcorrFolder] = sacs
        else:
            print(f'Error Usage 1! Could not find any sacfile in "{xcorrFolder}"\n\n')
            exit()

    xcorr_uniq = [] #uniq xcorr list for each season
    for i in range(12):
        uniq_list = []
        for xcorrFolder in xcorrFolders:
            if get_month(xcorrFolder) in season_months[i]:
                for sac in sacfiles[xcorrFolder]:
                    if sac not in uniq_list:
                        uniq_list.append(sac)
        xcorr_uniq.append(uniq_list)

    num_xcorr_uniq = []
    for x in xcorr_uniq:
        num_xcorr_uniq.append(len(x))

    report = f" Number of months in each season: {num_months}\n Number of xcorr days: {len(xcorrFolders)}\n Number of xcorrs in each season (min-max): {np.nanmin(num_xcorr_uniq)}-{np.nanmax(num_xcorr_uniq)}\n cross-correlogram dir (input): {daily_xcorrs_dir}\n season-stacked dir (output): {season_stack_dir}\n\n"

    print(f"{report}")

    uin = input("Do you want to continue the season-staking process (y/n)? ")

    if uin.lower() != 'y':
        print("\nExit program!\n")
        exit()

    os.mkdir(season_stack_dir)

    # Start the main process
    for i in range(12):
        print(f"\n\nSTAKING PROCESS FOR SEASON: {seasons_names[i]}\n\n")
        os.mkdir(os.path.join(season_stack_dir,seasons_names[i]))
        c = 0
        for xcorr in xcorr_uniq[i]:
            c += 1
            stacklist = []
            print(f"Season {seasons_names[i]}; xcorr '{xcorr}' ({c} of {len(xcorr_uniq[i])})")
            for xcorrFolder in xcorrFolders:
                if get_month(xcorrFolder) in season_months[i]:
                    if xcorr in sacfiles[xcorrFolder]:
                        stacklist.append(os.path.join(daily_xcorrs_dir,xcorrFolder,xcorr))
            stack(stacklist, os.path.join(season_stack_dir, seasons_names[i], xcorr))

#====USAGE 2====#

if usage2:
    print('Usage 2: group season-stacked cross-correlograms into four azimuthal groups\n\n')

    if not os.path.isdir(season_stack_dir):
        print(f"Error Usage 2! Could not find 'season_stack_dir'!\n\n")
        exit()
    else:
        temp = sorted(os.listdir(season_stack_dir))

    seasons = []
    for i in range(len(temp)):
        if re.search('[0-9][0-9]-[0-9][0-9]',temp[i]) and os.path.isdir(os.path.join(season_stack_dir, temp[i])):
            seasons.append(temp[i])

    uniq_xcorr = []
    for i in range(len(seasons)):
        for fn in os.listdir(os.path.join(season_stack_dir, f'{seasons[i]}')):
            if fn not in uniq_xcorr and re.search(sacfile_regex, fn):
                uniq_xcorr.append(fn)

    num_seasons = len(seasons)
    num_uniq_xcorr = len(uniq_xcorr)

    if num_seasons == 0:
        print(f'Error Usage 2! Could not find season directories ("??-??").\n')
        exit()

    if num_uniq_xcorr == 0:
        print(f'Error Usage 2! Could not find any sac file in season directories ("*.sac").\n')
        exit()

    report = f'  Number of seasons: {num_seasons}\n  Number of cross-correlograms: {num_uniq_xcorr}\n  Input directory: {season_stack_dir}\n\n'

    print(report)

    uin = input("Do you want to continue grouping season-stacked cross-correlograms based on azimuths (y/n)? ")

    if uin.lower() == 'y':
        print("\n")
    else:
        print("\n\nExit program!\n")
        exit()

    # create directories    
    for x in ['S-N', 'SW-NE', 'W-E', 'NW-SE']:
        dirname = os.path.abspath(f'{season_stack_dir}_{x}')
        if os.path.isdir(dirname):
            shutil.rmtree(dirname)

        os.mkdir(dirname)
        for season in seasons:
            os.mkdir(os.path.join(dirname, season))

    for season in seasons:
        i = 0
        for xcorr in uniq_xcorr:
            i += 1
            print(f'  Season: {season}; progress: %.0f%s' %((i/num_uniq_xcorr)*100, '%'), end='   \r')
            sacfile = os.path.join(season_stack_dir, season, xcorr)
            if os.path.isfile(sacfile):
                direction = get_direction(sacfile)
                dst = os.path.join(f'{season_stack_dir}_{direction}', season, xcorr)
                shutil.copyfile(sacfile, dst)


#====USAGE 3====#
if usage3:
    print('Usage 3: perform the seasonality analysis on the previously processed season-stacked cross-correlograms\n\n')
    if not os.path.isdir(season_stack_dir):
        print(f'Error Usage 3! Could not find "season_stack_dir"!\n{usage}\n')
        exit()
    else:
        temp = sorted(os.listdir(season_stack_dir))

    seasons = []
    ylabels = []
    months = ['January', 'Febuary', 'March', 'April', 'May',\
             'June', 'July', 'August', 'September', 'October', 'November', 'December']

    for i in range(len(temp)):
        if re.search('[0-9][0-9]-[0-9][0-9]',temp[i]) and os.path.isdir(os.path.join(season_stack_dir, temp[i])):
            seasons.append(temp[i])
            i1 = int(temp[i].split('-')[0])-1
            i2 = int(temp[i].split('-')[1])-1
            ylabels.append(f'{months[i1][0:3]}-{months[i2][0:3]}')

    uniq_xcorr = []
    for i in range(len(seasons)):
        for fn in os.listdir(os.path.join(season_stack_dir, f'{seasons[i]}')):
            if fn not in uniq_xcorr and re.search(sacfile_regex, fn):
                uniq_xcorr.append(fn)

    num_seasons = len(seasons)
    num_uniq_xcorr = len(uniq_xcorr)

    if num_seasons == 0:
        print(f'Error Usage 3! Could not find season directories ("??-??")\n')
        exit()

    if num_uniq_xcorr == 0:
        print(f'Error Usage 3! Could not find any sac file in season directories ("*.sac")\n')
        exit()

    report = f'  Number of seasons: {num_seasons}\n  Number of cross-correlograms: {num_uniq_xcorr}\n  Input directory: {season_stack_dir}\n  Output directory: {analysis_dir}\n\n'

    print(report)

    if bp:
        print(f"WARNING! Script will perform bandpass filtering before the analysis.\n\n")

    uin = input("Do you want to continue generating the final results (y/n)? ")

    if uin.lower() == 'y':
        print("\n")
    else:
        print("\n\nExit program!\n")
        exit()

    if not os.path.isdir(analysis_dir):
        os.mkdir(analysis_dir)

    # STEP 1 of 2: analysis of xcorrs
    # collect data
    seasons = sorted(seasons)
    uniq_xcorr = sorted(uniq_xcorr)
    snr_sym_xcorr = []
    snr_causal_xcorr = []
    snr_acausal_xcorr = []
    nstack_xcorr = []
    amps_xcorr = []
    times_xcorr = []
    i = 0
    print("Step 1 of 2: Analysis of cross-correlograms...\n")
    for xcorr in uniq_xcorr:
        i += 1
        print(f"  collecting data ({i} of {num_uniq_xcorr}):", xcorr)
        snr = []
        snr_causal = []
        snr_acausal = []
        nstack = []
        amps = []
        times = []
        for season in seasons:
            if xcorr in os.listdir(os.path.join(season_stack_dir, season)):
                sf = os.path.join(season_stack_dir, season, xcorr)
                st = obspy.read(sf, headonly=True)
                nstack.append(int(st[0].stats.sac.kevnm))
                sfcut = os.path.join(analysis_dir, 'sfcut.tmp')
                sym = os.path.join(analysis_dir, 'sym.tmp')
                causal = os.path.join(analysis_dir, 'causal.tmp')
                acausal = os.path.join(analysis_dir, 'acausal.tmp')
                signal = os.path.join(analysis_dir, 'signal_sym.tmp')
                noise = os.path.join(analysis_dir, 'noise_sym.tmp')
                signal_causal = os.path.join(analysis_dir, 'signal_causal.tmp')
                noise_causal = os.path.join(analysis_dir, 'noise_causal.tmp')
                signal_acausal = os.path.join(analysis_dir, 'signal_acausal.tmp')
                noise_acausal = os.path.join(analysis_dir, 'noise_acausal.tmp')
                signal_window = get_signal_window_times(sf)
                noise_window = get_noise_window_times(sf)
                sym_sac(sf, sym)
                causal_sac(sf, causal)
                acausal_sac(sf, acausal)
                cut_sac(sf, sfcut, -seism_cut, seism_cut)
                cut_sac(sym, signal, signal_window[0], signal_window[1])
                cut_sac(sym, noise, noise_window[0], noise_window[1])
                cut_sac(causal, signal_causal, signal_window[0], signal_window[1])
                cut_sac(causal, noise_causal, noise_window[0], noise_window[1])
                cut_sac(acausal, signal_acausal, signal_window[0], signal_window[1])
                cut_sac(acausal, noise_acausal, noise_window[0], noise_window[1])
                snr.append(calc_snr(get_sac_data(signal)[0], get_sac_data(noise)[0]))
                snr_causal.append(calc_snr(get_sac_data(signal_causal)[0], get_sac_data(noise_causal)[0]))
                snr_acausal.append(calc_snr(get_sac_data(signal_acausal)[0], get_sac_data(noise_acausal)[0]))
                amps.append(get_sac_data(sfcut)[0])
                times.append(get_sac_data(sfcut)[1])
            else:
                snr.append(np.nan)
                snr_causal.append(np.nan)
                snr_acausal.append(np.nan)
                nstack.append(np.nan)
                amps.append(np.nan)
                times.append(np.nan) 

        if correct_snr:
            for j in range(len(snr)):
                if snr[j] != np.nan:
                    snr[j] = correct_snr_value(snr[j], nstack[j], np.nanmean(nstack))
                    snr_causal[j] = correct_snr_value(snr_causal[j], nstack[j], np.nanmean(nstack))
                    snr_acausal[j] = correct_snr_value(snr_acausal[j], nstack[j], np.nanmean(nstack))

        snr_sym_xcorr.append(snr)
        snr_causal_xcorr.append(snr_causal)
        snr_acausal_xcorr.append(snr_acausal)
        nstack_xcorr.append(nstack)
        amps_xcorr.append(amps)
        times_xcorr.append(times)

    os.remove(sfcut)
    os.remove(sym)
    os.remove(signal)
    os.remove(noise)
    os.remove(causal)
    os.remove(acausal)
    os.remove(signal_causal)
    os.remove(noise_causal)
    os.remove(signal_acausal)
    os.remove(noise_acausal)

    # start the analysis, generate plots
    if bp:
        xcorrs_analysis_dir = os.path.join(analysis_dir,f"seasonality_analysis_EGFs_{bandpass_prd[0]}-{bandpass_prd[1]}s")
    else:
        xcorrs_analysis_dir = os.path.join(analysis_dir,"seasonality_analysis_EGFs_unfiltered")

    if not os.path.isdir(os.path.join(analysis_dir,xcorrs_analysis_dir)):
        os.mkdir(xcorrs_analysis_dir)

    for i in range(num_uniq_xcorr):
        print(f"  generating plot {i+1} of {num_uniq_xcorr}")
        fn = open(os.path.join(xcorrs_analysis_dir, f"{uniq_xcorr[i].split('.sac')[0]}.dat"), 'w')
        fn.write("%12s %8s %7s %7s %7s %7s %7s\n" %('EGF', '#seasons', 'min_snr', 'max_snr', 'avg_snr', 'med_snr', 'std_snr'))
        fn.write("%12s %8d %7.3f %7.3f %7.3f %7.3f %7.3f\n\n" \
            %(uniq_xcorr[i].split('.sac')[0], num_seasons-snr_sym_xcorr[i].count(np.nan), np.nanmin(snr_sym_xcorr[i]), np.nanmax(snr_sym_xcorr[i]), np.nanmean(snr_sym_xcorr[i]), np.nanmedian(snr_sym_xcorr[i]), np.nanstd(snr_sym_xcorr[i])))
        pdf = os.path.join(xcorrs_analysis_dir, f"{uniq_xcorr[i].split('.sac')[0]}.pdf")
        sns.set_style('white')
        sns.set_context(sns_context)
        f=plt.figure(figsize=(figsize*2.5,figsize))
        ax1=plt.subplot2grid((50, 90), (0, 0),rowspan=50, colspan=30)
        fn.write("%7s %6s %6s\n" %('season','#stack','snr'))
        for j in range(num_seasons):
            if np.isnan(snr_sym_xcorr[i][j]):
                pass
            else:
                fn.write("%7s %6d %6.3f\n" %(ylabels[j], nstack_xcorr[i][j], snr_sym_xcorr[i][j]))
                amps = np.divide(amps_xcorr[i][j], np.max(np.abs(amps_xcorr[i][j])))
                amps = np.multiply(amps, seismogram_amp_factor)
                amps = np.multiply(amps, snr_sym_xcorr[i][j]/np.nanmax(snr_sym_xcorr[i]))
                amps = np.add(amps, j)
                plt.plot(times_xcorr[i][j], amps, linewidth=seismogram_line_width, color='k')

        plt.yticks(np.arange(len(ylabels)), ylabels)
        plt.ylim(-1, len(ylabels))
        plt.ylabel('Seasons')
        plt.xlabel('Correlation lag (s)')
        if bp:
            plt.title(f"Seasonal variations ({uniq_xcorr[i].split('.sac')[0]}; {bandpass_prd[0]}-{bandpass_prd[1]} s)")
        else:
            plt.title(f"Seasonal variations ({uniq_xcorr[i].split('.sac')[0]})")

        ax2=plt.subplot2grid((50, 90), (0, 35),rowspan=50, colspan=15)
        ax2.barh(range(12), snr_sym_xcorr[i], align='center')
        plt.yticks(np.arange(len(ylabels)), ylabels)
        plt.ylim(-1, len(ylabels))
        plt.xlabel('SNR value')
        if correct_snr:
            plt.title(f"Symmetrized SNR (corrected)")
        else:
            plt.title(f"Symmetrized SNR")

        ax3=plt.subplot2grid((50, 90), (0, 55),rowspan=50, colspan=15)
        ax3.barh(range(12), snr_causal_xcorr[i], align='center')
        plt.yticks(np.arange(len(ylabels)), ylabels)
        plt.ylim(-1, len(ylabels))
        plt.xlabel('SNR value')
        if correct_snr:
            plt.title(f"Causal SNR (corrected)")
        else:
            plt.title(f"Causal SNR")

        ax3=plt.subplot2grid((50, 90), (0, 75),rowspan=50, colspan=15)
        ax3.barh(range(12), snr_acausal_xcorr[i], align='center')
        plt.yticks(np.arange(len(ylabels)), ylabels)
        plt.ylim(-1, len(ylabels))
        plt.xlabel('SNR value')
        if correct_snr:
            plt.title(f"Acausal SNR (corrected)")
        else:
            plt.title(f"Acausal SNR")

        plt.savefig(pdf,dpi=figure_dpi)
        plt.close()
        fn.close()

    # STEP 2 of 2: analysis of the entire region
    print("\nStep 2 of 2: Analysis of entire region ...\n")
    if bp:
        reg_analysis_dir = os.path.join(analysis_dir,f"seasonality_analysis_region_{bandpass_prd[0]}-{bandpass_prd[1]}s")
    else:
        reg_analysis_dir = os.path.join(analysis_dir,"seasonality_analysis_region_unfiltered")
    
    if not os.path.isdir(os.path.join(analysis_dir,reg_analysis_dir)):
        os.mkdir(reg_analysis_dir)

    fn = open(os.path.join(reg_analysis_dir, 'snr_seasons.dat'), 'w')
    fn.write("%7s %5s %7s %7s %7s %7s %7s\n" %('season', '#EGFs', 'min_snr', 'max_snr', 'avg_snr', 'med_snr', 'std_snr'))
    snr_seasons = {}

    for i in range(len(seasons)):
        print(f"  processing season {i+1} of {len(seasons)}")
        temp = []
        for j in range(len(uniq_xcorr)):
            temp.append(snr_sym_xcorr[j][i])
        snr_seasons[f'{ylabels[i]}'] = temp
        fn.write(f"%7s %5d %7.3f %7.3f %7.3f %7.3f %7.3f\n" %(ylabels[i], len(temp)-temp.count(np.nan),np.nanmin(temp), np.nanmax(temp), np.nanmean(temp), np.nanmedian(temp), np.nanstd(temp)))

    # boxplot
    df = pd.DataFrame(snr_seasons)
    pdf = os.path.join(reg_analysis_dir, "snr_boxplot.pdf")
    sns.set_style('ticks')
    sns.set_context(sns_context)
    f=plt.figure(figsize=(figsize*1.5,figsize))
    ax2 = sns.boxplot(data=df, color='white')
    # change the color (do not want it to be so colorful!):
    myColor = (0.12,0.46,0.70,1)
    for i,box in enumerate(ax2.artists):
        box.set_edgecolor(myColor)
        box.set_facecolor('white')

        # iterate over whiskers and median lines
        for j in range(6*i,6*(i+1)):
             ax2.lines[j].set_color(myColor)

    plt.ylabel('SNR value')
    if correct_snr:
        plt.title(f"Seasonal variations of SNR (corrected) values")
    else:
        plt.title(f"Seasonal variations of SNR values")
    plt.savefig(pdf,dpi=figure_dpi)
    plt.close()

    # scatterplot with error bars
    f=plt.figure(figsize=(figsize*1.5,figsize))
    pdf = os.path.join(reg_analysis_dir, "snr_scatterplot.pdf")
    sns.set_style('ticks')
    sns.set_context(sns_context)
    plt.ylabel('SNR value')
    sns.pointplot(data=df, linestyles="--", capsize=.2, ci='sd')

    if correct_snr:
        plt.title(f"Seasonal variations of mean SNR (corrected)")
    else:
        plt.title(f"Seasonal variations of mean SNR")

    plt.savefig(pdf,dpi=figure_dpi)
    plt.close()

print("\n\nDone!\n")
