#!/usr/bin/env python3

about = "This program carries out the stacking process in seasonality analysis procedure in ambient-noise tomography."

usage = '''Usage:
  python ANT_seasonality_stack.py  daily_xcorrs_dir season_stack_dir  num_months

'''

# Notes: 1) "num_months" should be in [1, 2, 3, 4, 6]
#        2) "daily_xcorrs_dir" should contain cross-correlation daily record folders
#           in "YYJJJ000000" format
#       
# Input datasets are daily record cross-correlation sac files
# UPDATE: 30 Sep 2020
# CODED BY: omid.bagherpur@gmail.com
#======Adjustable Parameters======#
# regular expression for daily chunk directories
xcorr_dir_regex = '(^[0-9]{11})'
sacfile_regex = 'sac$'  # regular expression for sac files
SAC = "/usr/local/sac/bin/sac"  # path to SAC software

signal_vel = [2.5, 4.5]

#=================================#
import os
import sys
import re
from glob import glob
from datetime import datetime
import numpy as np
import subprocess
import obspy

os.system('clear')
print(f"{about}\n")

daily_xcorrs_dir = str(os.path.abspath(sys.argv[1]))
season_stack_dir = str(os.path.abspath(sys.argv[2]))
num_months = int(sys.argv[3])

if num_months not in [1, 2, 3, 4, 6]:
    print(f"Error! 'num_months' should be in [1, 2, 3, 4, 6]\n\n{usage}\n")
    exit()

#-----FUNCTIONS-----#

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


def calc_snr(signal, noise):
    srms = sqrt(npmean(square(signal)))
    nrms = sqrt(npmean(square(noise)))
    snr = 10*log10((srms**2)/(nrms**2))
    return snr


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

#-------------------#

season_months, seasons_names = get_seasons(num_months)

xcorrFolders = []
xcorrMonth = {}
for path in glob(f'{daily_xcorrs_dir}/*000000'):
    path =  os.path.basename(path)
    if re.search(xcorr_dir_regex, path):
        xcorrFolders.append(path)
        xcorrMonth[xcorrFolders[-1]] = get_month(xcorrFolders[-1])

if len(xcorrFolders) == 0:
    print("Error! No daily xcorr folder was found!\n\
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
        print(f'Error! Could not find any sacfile in "{xcorrFolder}"\n\n')
        exit()

xcorr_uniq = [] #uniq xcorr list for each season
for i in range(3,12,1):
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

report = f" Number of months in each season: {num_months}\n Number of xcorr days: {len(xcorrFolders)}\n Number of xcorrs in each season (min-max): {np.nanmin(num_xcorr_uniq)}-{np.nanmax(num_xcorr_uniq)}\n\n"

print(f"{report}")

uin = input("Do you want to proceed to the staking process (y/n)? ")

if uin.lower() != 'y':
    print("\nExit program!\n")
    exit()

# Start the main process
for i in range(3,12,1):
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

print("\nDone!\n")

