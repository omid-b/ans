#!/usr/bin/env python3
import time
import re
import sys
import os
about = "This script removes sacfiles of similar channels \
(except one desired) of the same station within an event directory."
# Example usefulness: if both BHZ and HHZ components of the same station
# is available in an event directory, this script will be usefull to delete
# BHZ and only keep HHZ component. Of course, no sac file will be deleted if
# only one channel of 'similar_channels' is present in an event directory.
usage = '''
USAGE:
 python3 removeChannel.py <dataset dir>
'''
# Coded by omid.bagherpur@gmail.com
# UPDATE: 11 June 2019
#=====Adjustable Parameters====#
# Assuming dataset directory includes event directories in which
# there are a bunch of sac files:
# define python regular expressions for event names and sac file names
events_regex = "^[0-9]{11}$"
sacfile_regex = "([a-zA-Z0-9])*(Z)$"
similar_channels = ['BHZ', 'HHZ']
# keep_channel: for sac files of the same station within an event directory,
# all "similar_channels" except "keep_channel" will be deleted
keep_channel = 'HHZ'
#==============================#
os.system('clear')
print(f"{about}\n")
if(len(sys.argv) != 2):
    print(f"Error!\n {usage}")
    exit()
else:
    datasets = os.path.abspath(sys.argv[1])

if not os.path.isdir(datasets):
    print(f"Error! dataset directory does not exist!\n{usage}")
    exit()
else:
    events = []
    for x in os.listdir(datasets):
        if re.search(events_regex, x):
            events.append(x)
if len(events) == 0:
    print(f'Error! could not find any event in dataset directory!\n\
Check the "events_regex" parameter.\n{usage}')
    exit()
events.sort()

sacfiles = []
for evt in events:
    evt = os.path.join(datasets, evt)
    sf = []
    for x in os.listdir(evt):
        if re.search(sacfile_regex, x):
            sf.append(x)
    sf.sort()
    sacfiles.append(sf)

if keep_channel not in similar_channels:
    print(f'Error! keep_channel ({keep_channel}) \
must be included in similar_channels.\nCheck "Adjustable Parameters"\n\n')
    exit()

num_sacfiles = []  # a list of number of sacfiles within each event
num_sacfiles_total = 0
i = 0
while i < len(sacfiles):
    num_sacfiles.append(len(sacfiles[i]))
    num_sacfiles_total = num_sacfiles_total+num_sacfiles[-1]
    if(num_sacfiles[-1]) == 0:
        print(f'Error! No sacfile found in event: {events[i]}\n\
Check the "sacfile_regex" parameter.\n{usage}')
        exit()
    i += 1


print(f"#Events: {len(events)}\n#SAC files in event directories: \
{min(num_sacfiles)}-{max(num_sacfiles)}\nDataset directory: '{datasets}'\n\
Similar channels: {similar_channels}\nKeep channel: {keep_channel}\n")

uans = input("\nWARNING! This process is irreversible!\n\
Do you want to continue (y/n)? ")
if uans != 'y':
    print("\nExit program!\n\n")
    exit()

t0 = time.time()
#======Main Codes========#
try:
    import obspy
except ImportError as e:
    print(f"Error! {e}")
    exit()


print("\n  Program progress %3.0f" % (0), end='%\r')
i = 0
while i < len(events):
    j = 0
    sta = []
    stachn = []
    while j < len(sacfiles[i]):
        sacfile = os.path.join(datasets, events[i], sacfiles[i][j])
        st = obspy.read(sacfile, format='SAC', headersonly=True)
        sta.append(st[0].stats.station)
        stachn.append(st[0].stats.station+'.'+st[0].stats.channel)
        j += 1

    k = 0
    while k < len(sta):
        similar_stachn = []
        for x in similar_channels:
            similar_stachn.append(sta[k]+'.'+x)
        n = 0
        for x1 in similar_stachn:
            if x1 in stachn:
                n += 1

        if n > 1 and stachn[k] != sta[k]+'.'+keep_channel:
            os.remove(os.path.join(datasets, events[i], sacfiles[i][k]))
        k += 1

    print("  Program progress %3.0f" % ((i+1)/len(events)*100), end='%\r')
    i += 1

print("  Program progress %3.0f" % (100), end='%\n')

t1 = time.time()
dt = "%.2f" % ((t1-t0)/60)
print(f"\nThe operation took about {dt} minutes.\n")
