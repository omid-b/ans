#!/usr/bin/env python3
import time
import re
import sys
import os
about = "This script uses obspy and SAC for writting sac header \
information from pertinent station xml files."
usage = '''
USAGE:
 python3 writeHeaders.py <dataset dir> <xml list>
'''
# This script writes these headers: stla, stlo, stel, cmpaz, cmpinc
# Coded by omid.bagherpur@gmail.com
# UPDATE: 12 June 2020
#=====Adjustable Parameters====#
# Assuming dataset directory includes event directories
# in which there are a bunch of sac files:
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
    xmllist = os.path.abspath(sys.argv[2])

# Import python modules
try:
    import numpy as np
    import obspy
    import subprocess
except ImportError as e:
    print(f"\nError importing python module! {e}\n")
    exit()

if not os.path.isdir(datasets):
    print(f"Error! dataset directory does not exist!\n{usage}")
    exit()
else:
    events = []
    for x in os.listdir(datasets):
        if re.search(events_regex, x):
            events.append(x)

if not os.path.isfile(xmllist):
    print(f"Error! <xml list> does not exist!\n{usage}")
    exit()
else:
    with open(xmllist, 'r') as xmls:
        stationxml = {}
        for xml in xmls:
            if not os.path.isfile(os.path.abspath(xml.split()[0])):
                print(f"Error! Could not find the xml file:\n  {xml}\n")
                exit()
            else:
                inv = obspy.read_inventory(os.path.abspath(xml.split()[0]))
                stationxml[f'{inv[0][0].code}.{inv[0][0].channels[0].code}'] =\
                    os.path.abspath(xml.split()[0])

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
            data = obspy.read(os.path.join(datasets, evt, x),
                              format='SAC', headonly=True)[0]
            stacha = f"{data.stats['station']}.{data.stats['channel']}"
            if stacha not in stationxml:
                print(f"Error! No stationxml found for '{stacha}'\n")
                exit()

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
{min(num_sacfiles)}-{max(num_sacfiles)}\nDataset directory: \
'{datasets}'\nxml list: {xmllist}\n")

uans = input(
    "\nWARNING! This process is irreversible!\n\
Do you want to continue (y/n)? ")
if uans != 'y':
    print("\nExit program!\n\n")
    exit()

t0 = time.time()
#======Main Codes========#


#---functions here---#
def write_sac_headers(sacfile, stationxml):
    inv = obspy.read_inventory(stationxml, format='stationxml')
    stla = np.float(inv[0][0].latitude)
    stlo = np.float(inv[0][0].longitude)
    stel = np.float(inv[0][0].elevation)
    cmpaz = np.float(inv[0][0][0].azimuth)
    cmpinc = np.float(inv[0][0][0].dip)+90
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    shell_cmd.append(f"r {sacfile}")
    shell_cmd.append(f"chnhdr stla {stla}")
    shell_cmd.append(f"chnhdr stlo {stlo}")
    shell_cmd.append(f"chnhdr stel {stel}")
    shell_cmd.append(f"chnhdr cmpaz {cmpaz}")
    shell_cmd.append(f"chnhdr cmpinc {cmpinc}")
    shell_cmd.append("chnhdr lovrok True")
    shell_cmd.append("chnhdr lcalda True")
    shell_cmd.append(f"wh")
    shell_cmd.append('quit')
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd, shell=True)
#--------------------#


# Decimat timeseries
print("\n  Program progress %3.0f" % (0), end='%\r')
i = 0
while i < len(events):
    j = 0
    while j < len(sacfiles[i]):
        sacfile = os.path.join(datasets, events[i], sacfiles[i][j])
        data = obspy.read(sacfile, format='SAC', headonly=True)[0]
        stacha = f"{data.stats['station']}.{data.stats['channel']}"
        write_sac_headers(sacfile, stationxml[stacha])
        j += 1
    print("  Program progress %3.0f" % ((i+1)/len(events)*100), end='%\r')
    i += 1

print("  Program progress %3.0f" % (100), end='%\n')

t1 = time.time()
dt = "%.2f" % ((t1-t0)/60)
print(f"\nThe operation took about {dt} minutes.\n")
