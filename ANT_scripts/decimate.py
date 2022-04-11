#!/usr/bin/env python3
import time
import re
import sys
import os
about = "This script uses obspy and SAC for \
fast resampling of SAC file timeseries."
usage = '''
USAGE:
 python3 decimate.py  <dataset dir> <desired sampling rate>
'''
# Coded by omid.bagherpur@gmail.com
# UPDATE: 11 June 2020
#=====Adjustable Parameters====#
# Assuming dataset directory includes event directories
# in which there are a bunch of sac files,
# define python regular expressions for event names and sac file names
events_regex = "^[0-9]{11}$"
sacfile_regex = "([a-zA-Z0-9])*(Z)$"
SAC = "/usr/local/sac/bin/sac"
#==============================#
os.system('clear')
print(f"{about}\n")
if(len(sys.argv) != 3):
    print(f"Error!\n {usage}")
    exit()
else:
    datasets = os.path.abspath(sys.argv[1])
    fs_desired = int(sys.argv[2])

if not os.path.isdir(datasets):
    print(f"Error! dataset directory does not exist!\n{usage}")
    exit()
else:
    events = []
    for x in os.listdir(datasets):
        if re.search(events_regex, x):
            events.append(x)

if not os.path.isfile(SAC):
    print(f"Error! Path to SAC software does not exist!\n\
Check 'Adjustable Parameters'\n\n")
    exit()

if len(events) == 0:
    print(f'Error! could not find any event in dataset directory!\n\
Check the "events_regex" parameter.\n{usage}')
    exit()

sacfiles = []
for evt in events:
    evt = os.path.join(datasets, evt)
    sf = []
    for x in os.listdir(evt):
        if re.search(sacfile_regex, x):
            sf.append(x)
    sacfiles.append(sf)

num_sacfiles = []  # a list of number of sacfiles withing each event
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
Desired sampling rate: {fs_desired} Hz\n")

uans = input("\nWARNING! This process is irreversible!\n\
Do you want to continue (y/n)? ")
if uans != 'y':
    print("\nExit program!\n\n")
    exit()

t0 = time.time()
#======Main Codes========#
# Import python modules
try:
    import numpy as np
    import obspy
    import subprocess
except ImportError as e:
    print(f"\nError importing python module! {e}\n")
    exit()


#---functions here---#
def find_factors(x, max_factor=99999):  # find factors of an integer
    factors = []
    for d in range(2, x+1):
        if x % d == 0 and d <= max_factor:
            factors.append(int(d))
    factors.sort(reverse=True)
    return factors


# outputs a python list of best decimation factors of less than 7
def find_sac_decimate_factor(fs0, fs_desired):
    sac_decimate_factor = []
    while fs0 != fs_desired:
        factors = find_factors(fs0, 7)
        for f in factors:
            if (fs0/f) % fs_desired == 0:
                sac_decimate_factor.append(f)
                break

        fs_new = int(fs0/sac_decimate_factor[-1])
        fs0 = fs_new
    return sac_decimate_factor
#--------------------#


# get delta header from all sacfiles
i = 0
fs0 = []
exit_flag = 0
while i < len(events):
    j = 0
    fsEvent = []
    while j < len(sacfiles[i]):
        st = obspy.read(os.path.join(
            datasets, events[i], sacfiles[i][j]), headonly=True)
        fsEvent.append(int(1/(st[0].stats.delta)))
        if fsEvent[-1] < fs_desired or fsEvent[-1] % fs_desired != 0:
            exit_flag = 1
            print(f"Cannot decimate to {fs_desired} Hz in \
'{events[i]}/{sacfiles[i][j]}' ({fsEvent[-1]} Hz)")
        j += 1
    fs0.append(fsEvent)
    i += 1

if exit_flag == 1:
    print("\nOperation aborted. Please choose a different desired \
sampling rate and try again!\n\n")
    exit()

# Decimat timeseries
print("\n  Program progress %3.0f" % (0), end='%\r')
i = 0
while i < len(events):
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    j = 0
    log = open(f'{os.path.join(datasets,events[i],"decimated.log")}', 'w')
    while j < len(sacfiles[i]):
        shell_cmd.append(
            f'r {os.path.join(datasets, events[i], sacfiles[i][j])}')
        for dec in find_sac_decimate_factor(fs0[i][j], fs_desired):
            shell_cmd.append(f'decimate {dec}')

        log.write(f"{sacfiles[i][j]}\n")
        shell_cmd.append('w over')
        j += 1

    shell_cmd.append('quit')
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd, shell=True)
    print("  Program progress %3.0f" % ((i+1)/len(events)*100), end='%\r')
    i += 1

print("  Program progress %3.0f" % (100), end='%\n')

t1 = time.time()
dt = "%.2f" % ((t1-t0)/60)
log.close()
print(f"\nThe operation took about {dt} minutes.\n")
