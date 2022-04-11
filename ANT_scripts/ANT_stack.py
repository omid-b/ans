#!/usr/bin/env python3
import subprocess
import time
import re
import sys
import os
about = "This script performs stacking of cross-correlated station pairs.\n"
usage = '''
USAGE:
 python3 ANT_stack.py  <dataset dir> <stacked dir>

<dataset dir>: dataset dir containing cross-correlated station pairs
<stacked dir>: output stacked dir

Note: <dataset dir> and <stacked dir> should not be the same.
'''
# UPDATE: 30 Sep 2020
# Coded by omid.bagherpur@gmail.com
#=====Adjustable Parameters=====#
# regular expression for daily chunk directories
xcorr_dir_regex = '(^[0-9]{11})'
sacfile_regex = 'sac$'  # regular expression for sac files
SAC = "/usr/local/sac/bin/sac"  # path to SAC software
#===============================#


os.system('clear')
print(about)

if len(sys.argv) != 3:
    print(f"Error USAGE!\n{usage}")
    exit()
else:
    datasetDir = os.path.abspath(sys.argv[1])
    stackedDir = os.path.abspath(sys.argv[2])

try:
    from obspy import read
except ImportError as e:
    print(f"Error! {e}")
    exit()

if datasetDir == stackedDir:
    print(f"Error! <dataset dir> and <stacked dir> \
should not be the same!\n{usage}")
    exit()

if not os.path.isfile(SAC):
    print(f"Error! Path to SAC software does not exist!\n\
Check 'Adjustable Parameters'\n\n")
    exit()

xcorrFolders = []
for x in os.listdir(datasetDir):
    if re.search(xcorr_dir_regex, x):
        xcorrFolders.append(x)

if len(xcorrFolders) == 0:
    print("Error! No daily chunk folder was found!\n\
Check 'xcorr_dir_regex' parameter.\n\n")
    exit()

sacfiles = []
uniqStaPairs = []
for xcorrFolder in xcorrFolders:
    temp = []
    for x in os.listdir(os.path.join(datasetDir, xcorrFolder)):
        if x not in uniqStaPairs:
            uniqStaPairs.append(x)
        if re.search(sacfile_regex, x):
            temp.append(x)
    sacfiles.append(temp)


if len(uniqStaPairs) == 0:
    print("Error! No sac file was found!\n\
Check 'sacfile_regex' parameter.\n\n")
    exit()

#===FUNCTIONS===#


def stacking(inputDataset, outputDataset, xcorrFolders, xcorr):
    nStacked = 0
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    shell_cmd.append("fg line 0 0 delta 1 npts 172801 begin -86400")
    for xcorrFolder in xcorrFolders:
        if xcorr in os.listdir(os.path.join(inputDataset, xcorrFolder)):
            nStacked += 1
            fn = os.path.join(inputDataset, xcorrFolder, xcorr)

            # read sac headers from the first occurrence
            if nStacked == 1:
                sf = read(fn, format='SAC', headonly=True)
                kstnm = str(sf[0].stats.sac.kstnm)
                stla = float(sf[0].stats.sac.stla)
                stlo = float(sf[0].stats.sac.stlo)
                stel = float(sf[0].stats.sac.stel)
                evla = float(sf[0].stats.sac.evla)
                evlo = float(sf[0].stats.sac.evlo)
                evel = float(sf[0].stats.sac.evel)
                kcmpnm = str(sf[0].stats.sac.kcmpnm)
                knetwk = str(sf[0].stats.sac.knetwk)
            shell_cmd.append(f"addf {fn}")
    shell_cmd.append(f'w {os.path.join(outputDataset,xcorr)}')
    xcorrnm = int(nStacked)
    shell_cmd.append(f'r {os.path.join(outputDataset,xcorr)}')
    shell_cmd.append(f"chnhdr kevnm '{xcorrnm}'")
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
    return nStacked
#===============#


info = f'''
 Dataset directory: {datasetDir}
 Output directory:  {stackedDir}
 Number of daily chunks:  {len(xcorrFolders)}
 Number of station pairs: {len(uniqStaPairs)}
'''
print(info)

uans = input("\n\n Do you want to continue (y/n)? ")
uans.lower()
print('\n')
if uans != 'y':
    print('\n Exit program!\n')
    exit()

if not os.path.isdir(stackedDir):
    os.mkdir(stackedDir)

nStacked = []
progress = 0
print(f" Program progress: {progress}%", end="    \r")
for i in range(len(uniqStaPairs)):
    ns = stacking(datasetDir, stackedDir, xcorrFolders, uniqStaPairs[i])
    nStacked.append(ns)
    progress = "%.0f" % (((i+1)/len(uniqStaPairs))*100)
    print(f" Program progress: {progress}%", end="    \r")


print("\n\n Done!\n")
