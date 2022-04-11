#!/usr/bin/env python3
import subprocess
import time
import re
import sys
import os
about = "This script performs instrument response removal \
using obspy and stationxml files.\n"
usage = '''
USAGE:
  python3 removeResposne.py  \
<stationxml list> <dataset dir> <output dir>

'''
# UPDATE: 11 June 2020
# Coded by omid.bagherpur@gmail.com
#=====Adjustable Parameters=====#
event_regex = '(^[0-9]{11})'  # regular expression for event directories
sacfile_regex = '(^[0-9]{11})?(HZ$)'  # regular expression for sac files
# applied in st.remove_response() process;
# see obspy documentation for more info
pre_filt = (0.005, 0.006, 30.0, 35.0)
#===============================#
os.system('clear')
print(about)

# check inputs
if len(sys.argv) != 4:
    print(f'Error USAGE!\n {usage}')
    exit()
else:
    stxml = os.path.abspath(sys.argv[1])
    input_datasets = os.path.abspath(sys.argv[2])
    output_datasets = os.path.abspath(sys.argv[3])

try:
    import numpy as np
    import shutil
    import obspy
except ImportError as e:
    print(f"\n\nError! {e}!\n\n")
    exit()

t1 = time.time()
if not os.path.isfile(stxml):
    print(f"{usage}\n\nError!\n\n Could not find <stationxml> data.\n")
    exit()
else:
    stxml = open(stxml, 'r')
    stationxml = stxml.read().splitlines()

stxml.close()
for xml in stationxml:
    if not os.path.isfile(xml):
        print(f"\nError! Could not find:\n\n '{xml}'\n\n")
        exit()


if not os.path.isdir(input_datasets):
    print(f"{usage}\n\nError!\n\n Input datasets directory does not exist!\n")
    exit()

if not os.path.isdir(output_datasets):
    print(f"{usage}\n\nError!\n\n output datasets directory does not exist!\n")
    exit()

if input_datasets == output_datasets:
    print(f"{usage}\n\nError!\n\n output and input datasets directories \
should not be the same!\n")
    exit()

event = []
for x in os.listdir(input_datasets):
    if re.search(event_regex, x):
        event.append(x)

if len(event) == 0:
    print(f"{usage}\n\nError! No event directory was found! \
Check 'event_regex' parameter\n event_regex={event_regex}\n\n")
    exit()
else:
    event.sort()

# read sacfile tags (tags are in 'network.station.channel' format)
sacfile_src = []
sacfile_dst = []
sacfileTag = []
for evt in event:
    evt_src_dir = os.path.join(input_datasets, evt)
    evt_dst_dir = os.path.join(output_datasets, evt)
    if os.path.isdir(evt_dst_dir):
        shutil.rmtree(evt_dst_dir)
    os.mkdir(evt_dst_dir)

    saclist = os.listdir(evt_src_dir)
    saclist.sort()
    for x in saclist:
        if re.search(sacfile_regex, x):
            sacfile_src.append(os.path.join(evt_src_dir, x))
            sacfile_dst.append(os.path.join(evt_dst_dir, x))
            st = obspy.read(sacfile_src[-1], headonly=True)
            sacfileTag.append(st[0].stats.network+'.' +
                              st[0].stats.station+'.'+st[0].stats.channel)

sacfileTag_uniq = []
for tag in sacfileTag:
    if tag not in sacfileTag_uniq:
        sacfileTag_uniq.append(tag)
sacfileTag_uniq.sort()

# read stationxml file tags
stationxmlTag = []
stationxmlTagIndex = []

xmlinv = obspy.read_inventory()
i = 0
for xml in stationxml:
    xmlinv += obspy.read_inventory(xml, format="STATIONXML")
    network = xmlinv[-1].code
    station = xmlinv[-1].stations[0].code
    channel = xmlinv[-1].stations[0].channels[0].code
    stationxmlTag.append(f"{network}.{station}.{channel}")
    stationxmlTagIndex.append(i)
    i += 1

stationxmlTag_uniq = []
for tag in stationxmlTag:
    if tag not in stationxmlTag_uniq:
        stationxmlTag_uniq.append(tag)
stationxmlTag_uniq.sort()

# check if all responses are available
noa = []
exitFlag = 0
for tag in sacfileTag_uniq:
    if tag not in stationxmlTag_uniq:
        noa.append(tag)
        exitFlag += 1

if exitFlag:
    print("Error finding xml response data for:\n")
    for tag in noa:
        print(tag)
    print("\nExit program!\n")
    exit()


print(f"Input datasets:  {input_datasets}\nOutput datasets: \
{output_datasets}\nNumber of events found: {len(event)}\n\
Number of sac files found: {len(sacfile_src)}\n\
Number of response types:  {len(sacfileTag_uniq)}")

# Do you want to continue?
uans = input("\nDo you want to continue (y/n)? ")
uans.lower()
if uans == 'y':
    print("\n\n")
else:
    print("\nExit program!\n")
    exit()


# instrument response removal
i = 0
t1 = time.time()
error = []
print(f"  Program progress:  0% (#Errors: {len(error)})", end="     \r")
while i < len(sacfile_src):
    xml = stationxml[stationxmlTag.index(sacfileTag[i])]
    inv = obspy.read_inventory(xml)
    st = obspy.read(sacfile_src[i])
    try:
        st.remove_response(inventory=inv, pre_filt=pre_filt)
        st.write(sacfile_dst[i], format='SAC')
    except ValueError:
        error.append(sacfile_src[i])
    progress = "%.0f" % (((i+1) / len(sacfile_src))*100)
    print(f"  Program progress:  {progress}% \
(#Errors: {len(error)})", end="    \r")
    i += 1


t2 = time.time()
print(f"\n\nFinished! operation took about about %.2f minutes\n"
      % (round((t2-t1)/60, 1)))

if len(error) > 0:
    errorlog = open(os.path.join(output_datasets,
                                 'removeResponse_errors.log'), 'w')
    for x in error:
        errorlog.write(f"{x}\n")
    errorlog.close()
    print(f"Program failed to remove instrument response in \
    {len(error)} cases!\nCheck 'removeResponse_errors.log'\n")
