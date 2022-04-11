#!/usr/bin/env python3
import os
import sys
import subprocess
about = "This script uses obspy FDSN and IRIS FetchData \
to download daily chunks for ambient noise tomography.\n"
usage = '''
USAGE:
  python3 ANT_data_acquisition.py  <netsta> <download dir> <user:pass>

 <netsta> is a text file with 2 columns:
   1)network  2)station

 <user:pass> is optional, in username:password format for \
downloading restricted data
'''
# Coded by omid.bagherpur@gmail.com
# UPDATE: 11 June 2020
#====Adjustable Parameters====#
start_date = "2014-08-01"  # in "yyyy-mm-dd" format
end_date = "2014-08-01"  # in "yyyy-mm-dd" format
channels = ["BHZ", "HHZ"]  # list of channels to download
# locations: a list of station location codes to download;
# [""] for no location code
locations = ["", "00"]

# Limiting station location
# longitude_range: a list in [minLat, maxLat] format
longitude_range = [-180, 180]
# latitude_range: a list in [minLon, maxLon] format
latitude_range = [-90, 90]

# path to IRIS 'FetchData' perl script
FetchData_Script = './FetchData-2018.337'
# for full list visit https://docs.obspy.org/packages/obspy.clients.fdsn.html
FDSN_data_centres = ["IRIS"]
#=============================#
os.system('clear')
print(about)

if len(sys.argv) < 3:
    print(f"Error! {usage}\n")
    exit()
else:
    stalist = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])

authentication = False
if len(sys.argv) == 5:
    authentication = True
    try:
        username = str(sys.argv[4]).split(':')[0]
        password = str(sys.argv[4]).split(':')[1]
    except:
        print(f"\nError reading <user:pass>!\n{usage}")
        exit()

if not os.path.isfile(FetchData_Script):
    print(f"Error!\n Could not find IRIS 'FetchData' perl script\
\n\nVisit http://service.iris.edu/clients/ to download the script.\n\n")
    exit()
else:
    FetchData_Script = os.path.abspath(FetchData_Script)

if not os.path.isdir(outdir):
    print(f"\nError! <download dir> directory does not exist.\n{usage}")
    exit()

if not os.path.isfile(stalist):
    print(f"\nError! <net sta> file does not exist.\n{usage}")
    exit()
else:
    stations = []
    networks = []
    with open(stalist, 'r') as stalist:
        for line in stalist:
            try:
                networks.append(line.split()[0])
                stations.append(line.split()[1])
            except:
                print(f"\nError! <netsta> format is not correct.\n{usage}")
                exit()

uniq_networks = []
for x in networks:
    if x not in uniq_networks:
        uniq_networks.append(x)

try:
    import obspy
    import re
    import shutil
    from obspy import UTCDateTime
    from obspy.clients.fdsn.client import Client
    from obspy.clients.fdsn.mass_downloader import RectangularDomain
    from obspy.clients.fdsn.mass_downloader import Restrictions
    from obspy.clients.fdsn.mass_downloader import MassDownloader
except ImportError as e:
    print(f'\nError! {e}\n')
    exit()

domain = RectangularDomain(minlatitude=latitude_range[0],
                           maxlatitude=latitude_range[1],
                           minlongitude=longitude_range[0],
                           maxlongitude=longitude_range[1])

print(f"  Number of stations: {len(stations)}\n  Number of networks:\
 {len(uniq_networks)}\n  Channels: {channels}\n  Location codes: \
 {locations}\n  Date range: [ {start_date},  {end_date} ]\n \
 Longitude range: [ {longitude_range[0]}, {longitude_range[1]} ]\n \
 Latitude range:  [ {latitude_range[0]}, {latitude_range[1]} ]\n \
 Download directory: {outdir}\n\n")


#=====FUNCTIONS=====#
def get_date_intervals(startDate, endDate):
    startDate = f"{startDate}T000000Z"
    startDate = UTCDateTime(startDate)
    endDate = f"{endDate}T000000Z"
    endDate = UTCDateTime(endDate)
    date_intervals = []
    while startDate <= endDate:
        t1 = startDate
        t2 = t1+86400
        t1_date = "%4d-%02d-%02d" % (t1.year, t1.month, t1.day)
        t2_date = "%4d-%02d-%02d" % (t2.year, t2.month, t2.day)
        date_intervals.append([t1_date, t2_date])
        startDate += 86400
    return date_intervals


def get_IRIS_interval(date_interval):
    t1 = f"{date_interval[0]},00:00:00.0000"
    t2 = f"{date_interval[1]},00:00:00.0000"
    IRIS_interval = [t1, t2]
    return IRIS_interval


def get_FDSN_interval(date_interval):
    t1 = f"{date_interval[0]}T00:00:00Z"
    t2 = f"{date_interval[1]}T00:00:00Z"
    FDSN_interval = [t1, t2]
    return FDSN_interval


def getxml(sta, net, chn, outfile):
    if authentication:
        shell_cmd = f"perl {FetchData_Script} -S {sta} -N {net} \
        -C {chn} -a {username}:{password} -X {outfile} -v\n"
    else:
        shell_cmd = f"perl {FetchData_Script} -S {sta} -N {net} \
        -C {chn} -X {outfile} -v\n"
    subprocess.call(shell_cmd, shell=True)


def check_IRIS_availability(sta, net, chn, loc, t1, t2,
                            longitude_range, latitude_range):
    # a trick to find out if data is available:
    # If metafile is created data is available!
    metafile = os.path.join(outdir, 'meta.tmp')
    if os.path.isfile(metafile):
        os.remove(metafile)
    if authentication:
        shell_cmd = f"perl {FetchData_Script} -S {sta} -N {net} \
        -C {chn} -L {loc} -s {t1} -e {t2} \
        --lon {longitude_range[0]}:{longitude_range[1]} \
        --lat {latitude_range[0]}:{latitude_range[1]} \
        -a {username}:{password} -m {metafile} -q\n"
    else:
        shell_cmd = f"perl {FetchData_Script} -S {sta} -N {net} \
        -C {chn} -L {loc} -s {t1} -e {t2} \
        --lon {longitude_range[0]}:{longitude_range[1]} \
        --lat {latitude_range[0]}:{latitude_range[1]} -m {metafile} -q\n"
    subprocess.call(shell_cmd, shell=True)
    if os.path.isfile(metafile):
        os.remove(metafile)
        return True
    else:
        return False


def get_IRIS_data(sta, net, chn, loc, t1, t2, outfile,
                  longitude_range, latitude_range):
    if authentication:
        shell_cmd = f"perl {FetchData_Script} -S {sta} -N {net} \
        -C {chn} -L {loc} -s {t1} -e {t2} \
        --lon {longitude_range[0]}:{longitude_range[1]} \
        --lat {latitude_range[0]}:{latitude_range[1]} \
        -a {username}:{password} -o {outfile} -v\n"
    else:
        shell_cmd = f"perl {FetchData_Script} -S {sta} -N {net} \
        -C {chn} -L {loc} -s {t1} -e {t2} \
        --lon {longitude_range[0]}:{longitude_range[1]} \
        --lat {latitude_range[0]}:{latitude_range[1]} -o {outfile} -v\n"
    subprocess.call(shell_cmd, shell=True)

#===================#


uans = input("Do you want to continue (y/n)? ")
uans.lower()
if uans != 'y':
    print("\nExit program!\n\n")
    exit()
else:
    pass

date_intervals = get_date_intervals(start_date, end_date)

i = 0  # counter for events
while i < len(date_intervals):
    j = 0  # counter for stations
    while j < len(stations):
        for chn in channels:
            for loc in locations:
                os.system('clear')
                print(f"Downloading data for day {i+1} of \
{len(date_intervals)}, station: '{stations[j]}' \
({j+1} of {len(stations)})\n\n")

                mseed_storage = f"{start_date.replace('-','')}_\
                {end_date.replace('-','')}_mseed"
                mseed_storage = os.path.join(outdir, mseed_storage)
                stationxml_storage = f"stationxml_{chn}"
                stationxml_storage = os.path.join(outdir, stationxml_storage)

                if not os.path.isdir(mseed_storage):
                    os.mkdir(mseed_storage)

                if not os.path.isdir(stationxml_storage):
                    os.mkdir(stationxml_storage)

                # obspy FDSN method
                btime = UTCDateTime(get_FDSN_interval(date_intervals[i])[0])
                etime = UTCDateTime(get_FDSN_interval(date_intervals[i])[1])
                domain = RectangularDomain(minlatitude=latitude_range[0],
                                           maxlatitude=latitude_range[1],
                                           minlongitude=longitude_range[0],
                                           maxlongitude=longitude_range[1])
                restrictions = Restrictions(
                    starttime=btime,
                    endtime=etime,
                    chunklength_in_sec=86400,
                    network=networks[j],
                    station=stations[j],
                    location=loc,
                    channel=chn,
                    reject_channels_with_gaps=False,
                    # we will take care of data fragmentation later!
                    minimum_length=0.0,  # all data is usefull!
                    minimum_interstation_distance_in_m=0)

                for k in range(len(FDSN_data_centres)):
                    if authentication:
                        cl = Client(FDSN_data_centres[k],
                                    user=username, password=password)
                        mdl = MassDownloader(providers=[cl])
                        mdl.download(domain, restrictions,
                                     mseed_storage=mseed_storage,
                                     stationxml_storage=stationxml_storage,
                                     print_report=True)
                    else:
                        mdl = MassDownloader(providers=[FDSN_data_centres[k]])
                        mdl.download(domain, restrictions,
                                     mseed_storage=mseed_storage,
                                     stationxml_storage=stationxml_storage,
                                     print_report=True)

                # IRIS FetchData method:
                fileName = "%s.%s.%s.%s__%4d%02d%02dT%02d%02d%02dZ__\
                %4d%02d%02dT%02d%02d%02dZ.mseed" \
                % (networks[j], stations[j], loc, chn, btime.year,
                   btime.month, btime.day, btime.hour, btime.minute,
                   btime.second, etime.year, etime.month, etime.day,
                   etime.hour, etime.minute, etime.second)
                if not os.path.isfile(os.path.join(mseed_storage, fileName)):
                    if check_IRIS_availability(stations[j], networks[j],
                                               chn, loc, get_IRIS_interval(
                                                   date_intervals[i])[0],
                                               get_IRIS_interval(
                                               date_intervals[i])[1],
                                               longitude_range,
                                               latitude_range):
                        print(f"\nUsing method 2, IRIS FetchData:\n")
                        get_IRIS_data(stations[j], networks[j], chn,
                                      loc, get_IRIS_interval(
                                          date_intervals[i])[0],
                                      get_IRIS_interval(date_intervals[i])[1],
                                      os.path.join(mseed_storage, fileName),
                                      longitude_range, latitude_range)
        j += 1
    i += 1

# FDSN xml data are not reliable in our case!
# redownloading through IRIS FetchData:
for chn in channels:
    stationxml_storage = os.path.join(outdir, f"stationxml_{chn}")
    if not os.path.isdir(stationxml_storage):
        os.mkdir(stationxml_storage)
    for i in range(len(stations)):
        print(f"  Downloding xml data for \
            {networks[i]}.{stations[i]}", end="    \r")
        fn0 = f"{networks[i]}.{stations[i]}.xml"
        fn0 = os.path.join(stationxml_storage, fn0)
        if os.path.isfile(fn0):
            os.remove(fn0)
        fn = f"{networks[i]}.{stations[i]}.{chn}"
        fn = os.path.join(stationxml_storage, fn)
        getxml(stations[i], networks[i], chn, fn)
    if len(os.listdir(stationxml_storage)) == 0:
        shutil.rmtree(stationxml_storage)

print("\n\nDone!\n\n")
