#!/usr/bin/env python
import time
import re
import sys
import os
about = "This script uses SAC for fast spectral whitening \
of SAC file timeseries."
usage = '''
USAGE: python3 whiten.py  <dataset dir>
'''
# Coded by omid.bagherpur@gmail.com
# UPDATE: 12 June 2020
#=====Adjustable Parameters====#
# Assuming dataset directory includes
# event directories in which there are a bunch of sac files:
# define python regular expressions for event names and sac file names
events_regex = "^[0-9]{11}$"
sacfile_regex = "([a-zA-Z0-9])*(Z)$"
SAC = "/usr/local/sac/bin/sac"
whiten_order = 6  # Whitening order (numper of poles); default=6
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
Whitening_order: {whiten_order}\n")

uans = input(
    "\nWARNING! This process is irreversible.\n\
Do you want to continue (y/n)? ")
if uans != 'y':
    print("\nExit program!\n\n")
    exit()

t0 = time.time()
#======Main Codes========#
# Import python modules
try:
    import numpy as np
    import subprocess
except ImportError as e:
    print(f"\nError importing python module! {e}\n")
    exit()


# Whiten timeseries
print("\n  Program progress %3.0f" % (0), end='%\r')
i = 0
while i < len(events):
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    j = 0
    log = open(f'{os.path.join(datasets,events[i],"whitened.log")}', 'w')
    while j < len(sacfiles[i]):
        shell_cmd.append(
            f'r {os.path.join(datasets, events[i],sacfiles[i][j])}')
        shell_cmd.append(f'whiten {whiten_order}')
        shell_cmd.append('w over')
        log.write(f"{sacfiles[i][j]}\n")
        j += 1

    shell_cmd.append('quit')
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd, shell=True)
    print("  Program progress %3.0f" % ((i+1)/len(events)*100),
          end='%\r')
    i += 1

print("  Program progress %3.0f" % (100), end='%\n')

t1 = time.time()
dt = "%.2f" % ((t1-t0)/60)
print(f"\nThe operation took about {dt} minutes.\n")
