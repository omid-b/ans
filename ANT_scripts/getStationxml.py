#!/usr/bin/env python3
import subprocess
import sys
import os
about = "This script automates downloading a list of \
station xml data from IRIS using the FetchData perl script.\n"
usage = '''
USAGE:
 python3 getStationxml.py <netsta> <output dir>

 <netsta>: a text file with 2 columns:
   1)network  2)station
'''
# Coded by omid.bagherpur@gmail.com
# UPDATE: 12 June 2019
#====Adjustable Parameters=====#
start_date = "2013-01-01"  # in "yyyy-mm-dd" format
end_date = "2015-01-05"  # in "yyyy-mm-dd" format
channel = ['HHZ', 'BHZ']  # list of channels to download
# longitude_range: a list in [minLat, maxLat] format (station location)
longitude_range = [-180, 180]
# latitude_range: a list in [minLon, maxLon] format (station location)
latitude_range = [-90, 90]
# path to IRIS 'FetchData' perl script
FetchData_Script = './FetchData-2018.337'
# Note: download the latest IRIS 'FetchData' perl script from
# http://service.iris.edu/clients/
#==============================#
os.system('clear')
print(about)

if len(sys.argv) != 3:
    print(f"Error!\n{usage}")
    exit()
else:
    netsta = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])

if not os.path.isfile(netsta):
    print(f"Error!\n Could not find <netsta>\n{usage}\n")
    exit()
else:
    station = []
    network = []
    with open(netsta, 'r') as netsta:
        for line in netsta:
            try:
                network.append(line.split()[0])
                station.append(line.split()[1])
            except:
                print(f"\nError! <netsta> format is not correct.\n{usage}")
                exit()

network_uniq = []
for x in network:
    if x not in network_uniq:
        network_uniq.append(x)

if not os.path.isfile(FetchData_Script):
    print(f"Error!\n Could not find IRIS 'FetchData' perl script\n\n\
Visit http://service.iris.edu/clients/ to download the script.\n\n")
    exit()
else:
    FetchData_Script = os.path.abspath(FetchData_Script)

if not os.path.isdir(outdir):
    os.mkdir(outdir)

try:
    import obspy
except ImportError as e:
    print(f"Error!\n {e}\n")
    exit()


def getxml(sta, net, chn, outfile):
    start_time = f"{start_date},00:00:00"
    end_time = f"{end_date},23:59:59"
    shell_cmd = \
        f"perl {FetchData_Script} -S {sta} -N {net} -C {chn} \
    -s {start_time} -e {end_time} -X {outfile} -q\n"
    subprocess.call(shell_cmd, shell=True)


print(f"  Number of stations: {len(station)}\n  \
Number of networks: {len(network_uniq)}\n  Channels: {channel}\n  \
Date range: [ {start_date},  {end_date} ]\n  Output directory: {outdir}\n\n")

uans = input("Do you want to continue (y/n)? ")
uans.lower()
print("")
if uans != 'y':
    print("Exit program!\n\n")
    exit()

i = 0
errors = []
while i < len(station):
    ierr = 0
    print(f"  Downloding xml data for {network[i]}.{station[i]}",
          end="    \r")
    for chn in channel:
        fn = f"{network[i]}.{station[i]}.{chn}"
        fn = os.path.join(outdir, fn)
        getxml(station[i], network[i], chn, fn)
        if not os.path.isfile(fn):
            ierr += 1
    if ierr == len(channel):
        errors.append(f"{network[i]}.{station[i]}")
    i += 1

print("\n")
for err in errors:
    print(f"  No XML data found for {err}")

print("\nDone!\n")
