#!/usr/bin/env python3
import shutil
import time
import re
import sys
import os
about = "This script performs cross-correlation of station\
 pairs needed in ambient-noise tomography procedure.\n"
usage = '''
USAGE:
 python3 ANT_xcorrelate.py  <input dir> <output dir> <min dist> <max dist>

<input dir>: input dataset directory containing daily chunk folders
<output dir>: script will output the results into this directory
<min dist>: minimum inter-station distance in km
<max dist>: maximum inter-station distance in km

Note: 1) <input dir> and <output dir> should not be the same.
      2) All sac files must at least have 'stla', 'stlo', and 'kcmpnm' headers.
'''
# UPDATE: 11 June 2020
# Coded by omid.bagherpur@gmail.com
#=====Adjustable Parameters=====#
# daily_chunk_dir_regex: regular expression for daily chunk directories
daily_chunk_dir_regex = '(^[0-9]{11})'

# sacfile_regex: regular expression for sac files in daily chunk directories
sacfile_regex = '(^[0-9]{11})?(HZ$)'

# xcorr_cmp: a list of acceptable cross-correlation components;
# Note that values refer to the last letter of sac kcmpnm header.
# For example, cross-correlation of a BHZ and a HHZ data gives kcmpnm=ZZ.
# Options include ZZ, ZR, TT, RZ, and RR.
xcorr_cmp = ['ZZ']

# SAC: Full path to the SAC software executable
SAC = "/usr/local/sac/bin/sac"  # path to SAC software
#===============================#
os.system('clear')
print(about)

# check inputs
if len(sys.argv) != 5:
    print(f"Error! This script requires 4 inputs.\n{usage}")
    exit()

if not os.path.isdir(os.path.abspath(sys.argv[1])):
    print(f"Error! <input dir> does not exist!\n{usage}")
    exit()
else:
    inputdir = os.path.abspath(sys.argv[1])

outputdir = os.path.abspath(sys.argv[2])

if not os.path.isdir(outputdir):
    os.mkdir(outputdir)

if inputdir == outputdir:
    print(f"Error! <input dir> and <output dir>\
     should not be the same!\n{usage}")
    exit()

try:
    mindist = float(sys.argv[3])
    maxdist = float(sys.argv[4])
except Exception as e:
    print(f"Error reading min/max inter-station distance!\n {e}\n{usage}")
    exit()

if mindist > maxdist:
    print(f"Error! <min dist> must be smaller than <max dist>\n{usage}")
    exit()

if not os.path.isfile(SAC):
    print(f"Error! Path to SAC software does not exist!\
        \nCheck 'Adjustable Parameters'\n\n")
    exit()


# import required modules
try:
    import obspy
    import subprocess
    from geographiclib.geodesic import Geodesic
except ImportError as e:
    print(f"Error! {e}\n")
    exit()

#===FUNCTIONS===#


def find_uniq_pairs(lst0):
    # INPUT:  a list of strings
    # OUTPUT: a list of sorted and uniq pair list of strings
    lst = []
    for x in lst0:
        if x not in lst:
            lst.append(x)
    lst.sort()
    pairs = []
    i = 0
    while i < (len(lst)-1):
        for j in range(i+1, len(lst)):
            if [lst[i], lst[j]] not in pairs:
                pairs.append([lst[i], lst[j]])
        i += 1
    return pairs


def calc_dist(lat0, lon0, lat1, lon1):
    # INPUT: latitude and longitude of two points
    # OUTPUT: distance between two points in km
    dist = Geodesic.WGS84.Inverse(lat0, lon0, lat1, lon1)['s12']
    return dist/1000


def xcorrelate(sacfile1, sacfile2, output_sacfile):
    # INPUTS: full path to the 2 sac files
    # OUTPUT: full path to the output sac file
    output_dir = os.path.dirname(output_sacfile)
    sf1 = os.path.join(output_dir, 'temp1.sac')  # sacfile1
    sf2 = os.path.join(output_dir, 'temp2.sac')  # sacfile2
    ac = os.path.join(output_dir, 'temp3.sac')  # auto correlation
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    shell_cmd.append(f"r {sacfile1} {sacfile2}")
    shell_cmd.append(f"cuterr fillz")
    shell_cmd.append(f"cut 0 86400")
    shell_cmd.append(f"w {sf1} {sf2}")
    shell_cmd.append(f"r {sf1} {sf2}")
    shell_cmd.append(f"correlate master 1 number 1 normalized")
    shell_cmd.append(f"w {ac} {output_sacfile}")
    shell_cmd.append(f"q")
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd, shell=True)
    os.remove(sf1)
    os.remove(sf2)
    os.remove(ac)


def write_sac_headers(sacfile, headers):
    # INPUTS: full path to sac file; sac headers in python dictionary format
    # OUTPUT: the same sacfile with modified headers
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    shell_cmd.append(f"r {sacfile}")
    for hdr in headers:
        shell_cmd.append(f"chnhdr {hdr} {headers[hdr]}")
    shell_cmd.append(f"wh")
    shell_cmd.append(f"q")
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd, shell=True)


#==============#

# obtain info about input dir
print("  Collecting dataset information ...", end="  \r")
chunks = []
for x in os.listdir(inputdir):
    if re.search(daily_chunk_dir_regex, x):
        chunks.append(x)

if len(chunks) == 0:
    print(f'\nError! could not find any daily chunk directory!\
        \nCheck the "daily_chunk_dir_regex" parameter.\n{usage}')
    exit()

chunks.sort()
sacfiles = []
nsac = 0  # total number of sacfiles
for chunk in chunks:
    chunk = os.path.join(inputdir, chunk)
    sf = []
    for x in os.listdir(chunk):
        nsac += 1
        if re.search(sacfile_regex, x):
            sf.append(x)
    sf.sort()
    sacfiles.append(sf)

sacfiles_sta = []
sta = []  # a list of unique stations
staLat = dict()  # latitude of stations
staLon = dict()  # longitude of stations
staElv = dict()  # elevation of stations
i = 0
while i < len(chunks):
    chunk = os.path.join(inputdir, chunks[i])
    j = 0
    stations = []
    while j < len(sacfiles[i]):
        data = os.path.join(inputdir, chunks[i], sacfiles[i][j])
        st = obspy.read(data, headonly=True, format='SAC')
        stations.append(st[0].stats.station)
        if st[0].stats.station not in sta:
            sta.append(st[0].stats.station)
            staLat[st[0].stats.station] = st[0].stats.sac.stla
            staLon[st[0].stats.station] = st[0].stats.sac.stlo
            staElv[st[0].stats.station] = st[0].stats.sac.stel
        j += 1
    sacfiles_sta.append(stations)
    i += 1

# find accepted station pairs according to (mindist, maxdist) range
sta_pairs0 = find_uniq_pairs(sta)
sta_pairs = []
sta_pairs_dist = []
for pair in sta_pairs0:
    lat0 = staLat[pair[0]]
    lon0 = staLon[pair[0]]
    lat1 = staLat[pair[1]]
    lon1 = staLon[pair[1]]
    dist = calc_dist(lat0, lon0, lat1, lon1)
    if dist >= mindist and dist <= maxdist:
        sta_pairs.append(pair)
        sta_pairs_dist.append(dist)

print("  Collecting dataset information ... Done!\n\n")
info = " Input directory: %s\n Output directory: %s\n \
#Stations: %d\n #Daily-chunk folders: %d\n Total number of sacfiles:\
 %d\n\n Minimum inter-station distance: %.0f km\n Maximum inter-station\
  distance: %.0f km\n Number of accepted station pairs: %d\n"\
   % (inputdir, outputdir, len(sta), len(chunks), nsac, mindist,
      maxdist, len(sta_pairs))
print(info)

uans = input("Do you want to continue (y/n)? ")
uans.lower()
print("\n")
if uans != 'y':
    print("Exit program!\n")
    shutil.rmtree(outputdir)
    exit()

# start the cross correlation process
nCC = []  # number of cross-correlation for sta_pairs
for i in range(len(sta_pairs)):
    nCC.append(0)

progress = 0
for i in range(len(chunks)):
    print(f"  Program progress: {progress}%", end="     \r")
    sacs = sacfiles_sta[i].copy()
    j = 0
    for pair in sta_pairs:
        if pair[0] in sacfiles_sta[i] and pair[1] in sacfiles_sta[i]:
            sacfile1 = os.path.join(
                inputdir, chunks[i], sacfiles[i][sacs.index(pair[0])])
            sacfile2 = os.path.join(
                inputdir, chunks[i], sacfiles[i][sacs.index(pair[1])])
            sf1 = obspy.read(sacfile1, format='SAC', headonly=True)[0]
            sf2 = obspy.read(sacfile2, format='SAC', headonly=True)[0]
            kstnm = f"{sf1.stats.sac.kstnm}-{sf2.stats.sac.kstnm}"
            knetwk = f"{sf1.stats.sac.knetwk}-{sf2.stats.sac.knetwk}"
            kcmpnm = f"{sf1.stats.sac.kcmpnm[-1]}{sf2.stats.sac.kcmpnm[-1]}"

            if not os.path.isdir(os.path.join(outputdir, chunks[i])):
                os.mkdir(os.path.join(outputdir, chunks[i]))

            output_CC = os.path.join(outputdir, chunks[i],
                                     f"{pair[0]}_{pair[1]}_{kcmpnm}.sac")
            xcorrelate(sacfile1, sacfile2, output_CC)

            # write headers
            headers = dict()
            headers['kstnm'] = kstnm
            headers['knetwk'] = knetwk
            headers['kcmpnm'] = kcmpnm
            headers['evla'] = staLat[pair[0]]
            headers['evlo'] = staLon[pair[0]]
            headers['evel'] = staElv[pair[0]]
            headers['stla'] = staLat[pair[1]]
            headers['stlo'] = staLon[pair[1]]
            headers['stel'] = staElv[pair[1]]
            headers['cmpaz'] = 'UNDEF'
            headers['cmpinc'] = 'UNDEF'
            write_sac_headers(output_CC, headers)

            nCC[j] += 1
        j += 1

    progress = "%.0f" % (((i+1)/(len(chunks)))*100)

# write xcorrelate.log
report = open(os.path.join(outputdir, "xcorrelate.log"), 'w')
report.write(info)
report.write("\nTotal number of cross-correlations for \
each station pair:\n")
for i in range(len(sta_pairs)):
    report.write(f"{sta_pairs[i][0]}-{sta_pairs[i][1]}  {nCC[i]}\n")
report.close()
print("  Program progress: 100%\n\n")
