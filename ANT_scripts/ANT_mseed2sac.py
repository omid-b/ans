#!/usr/bin/env python3
import subprocess
import sys
import os
about = "Taking care of data fragmentation problem in \
ambient-noise tomography, this script converts daily-chunk \
mseed files into SAC files."
usage = '''
USAGE:
 python3  ANT_mseed2sac.py  <mseed list> <output directory>
'''
# Coded by omid.bagherpur@gmail.com
# UPDATE: 11 June 2020
#===Adjustable Parameters===#
channels = '?H?'  # e.g. '?H?' includes BHZ and HHZ components
output_fragmented = 'no'  # 'yes' or 'no'; output fragmented files as *.p???
SAC = "/usr/local/sac/bin/sac"  # path to SAC software

# Processing parameters:
# Notes from Omid:
#  1) rtrend command in SAC is equivalent to detrend_method='demean' here.
#  2) taper command in SAC is equivalent to max_taper=0 here.
#  3) 'spline' method gives the best detrending results (visually),
#      but results highly depend on dspline parameter.
#      My tests indicate dspline=duration*10=864000
#      gives the best results (hardwired in the code)
# between 0 and 0.5; I recommend a very small number (0.001-0.01)
max_taper = 0.005
# options: (1) 'spline', (2) 'polynomial' (3) 'demean',
#          (4) 'linear'; I recommend 'spline' method
detrend_method = 'spline'
# utilised only if detrend_method is either set to 'spline'
# or 'polynomial'; I recommend 3-5
detrend_order = 4
#===========================#
os.system('clear')
print(about)

if len(sys.argv) != 3:
    print('\nError!\n', usage)
    exit()
else:
    print("\n  Channel(s):    %s\n  Output fragmented data: %s\n  \
max_taper:  %s\n  detrend_method:  %s\n"
          % (channels, output_fragmented, max_taper, detrend_method))

if os.path.isfile(sys.argv[1]):
    mseeds = open(sys.argv[1], 'r').read().splitlines()
else:
    print(f'\nError! Could not find "{sys.argv[1]}"\n')
    exit()

outdir = os.path.abspath(sys.argv[2])

for mseed in mseeds:
    if not os.path.isfile(mseed):
        print('Error! Could not find "%s"\n' % (mseed))
        exit()

if not os.path.isfile(SAC):
    print(f"Error! Path to SAC software does not exist!\n\
Check 'Adjustable Parameters'\n\n")
    exit()

try:
    import numpy as np
    import matplotlib.pyplot as plt
    from fnmatch import filter as wcard
    import obspy
    import glob
    import shutil
except ImportError as e:
    print(f'Error! {e}\n')
    exit()

#--functions--#


def find_duplicates(seq, item):
    start_at = -1
    locs = []
    while True:
        try:
            loc = seq.index(item, start_at+1)
        except ValueError:
            break
        else:
            locs.append(loc)
            start_at = loc
    return locs


def sac_setBegin(sacfile, btime):
    st = obspy.read(sacfile, format='SAC')
    tr = st[0]
    tr.stats.sac = obspy.core.AttribDict()
    tr.stats.sac.b = btime
    tr.stats.sac.iztype = 9
    tr.stats.sac.lovrok = True
    tr.stats.sac.lcalda = True
    tr.write(sacfile, format='SAC')


def sac_dailyCut(sacfile):
    shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    shell_cmd.append(f"cuterr fillz")
    shell_cmd.append(f"cut 0 86400")
    shell_cmd.append(f"r {sacfile}")
    shell_cmd.append(f"w over")
    shell_cmd.append(f"q")
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd, shell=True)


#------------#
# main code block
uans = input("\n\nDo you want to continue (y/n)? ")
uans.lower()
print('\n')
if uans != 'y':
    print('\n\nExit program!\n')
    exit()

c1 = 0
for mseed in mseeds:
    c1 += 1
    loc = mseed.split('.')[2]
    print(f"Extracting SAC data ({c1} of \
{len(mseeds)}): \n  {mseed.split('/')[-1]}")
    st = obspy.read(mseed)

    if detrend_method == 'spline':
        try:
            st.detrend(detrend_method, order=detrend_order, dspline=864000)
        except:
            st.detrend('demean')
    elif detrend_method == 'polynomial':
        try:
            st.detrend(detrend_method, order=detrend_order)
        except:
            st.detrend('demean')
    else:
        st.detrend(detrend_method)

    st.taper(max_taper)

    st.sort(['starttime'])
    trace = []
    station = []
    channel = []
    stacha = []
    length = []
    event = []
    time = []
    for i in range(len(st)):
        if wcard([st[i].stats.channel], channels):
            trace.append(st[i])
            station.append(st[i].stats.station)
            channel.append(st[i].stats.channel)
            stacha.append(st[i].stats.station+'.'+st[i].stats.channel)
            length.append(round(st[i].stats.npts*st[i].stats.delta, 0))
            yy = str(st[i].stats.starttime.year)[2:]
            jjj = '%03d' % (st[i].stats.starttime.julday)
            hh = '%02d' % (st[i].stats.starttime.hour)
            mm = '%02d' % (st[i].stats.starttime.minute)
            ss = '%02d' % (st[i].stats.starttime.second)
            event.append(yy+jjj+hh+mm+ss)
            time.append(st[i].stats.starttime.timestamp)

    # stacha members are strings in "station.channel" format
    stacha_index_group = []
    for i in range(len(stacha)):
        if find_duplicates(stacha, stacha[i]) not in stacha_index_group:
            stacha_index_group.append(find_duplicates(stacha, stacha[i]))

    for i in range(len(stacha_index_group)):
        dirname = event[stacha_index_group[i][0]][0:5]+'000000'
        dirname = os.path.join(outdir, dirname)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        if len(stacha_index_group[i]) == 1:  # no data fragmentation!

            fname = event[stacha_index_group[i][0]][0:5] + \
                '000000'+'_'+stacha[stacha_index_group[i][0]]
            fname0 = fname
            fname = os.path.join(outdir, dirname, fname)
            temp = os.path.join(outdir, dirname, 'temp0')
            tr = trace[stacha_index_group[i][0]].copy()
            begin_time = int(tr.stats.starttime.hour*3600 +
                             tr.stats.starttime.minute*60 +
                             tr.stats.starttime.second)
            tr.write(fname, format='SAC')
            # fix wrong begin time:
            sac_setBegin(fname, begin_time)
            # cut data into 0-86400 sec:
            sac_dailyCut(fname)

        else:  # data is fragmented and merging is required
            dtime = []
            dtime_index = []
            ref = stacha_index_group[i][0]
            k = 0

            while k < len(stacha_index_group[i]):
                current_index = stacha_index_group[i][k]
                dtime.append(round(abs(time[current_index] - time[ref]), 0))
                dtime_index.append(current_index)

                if dtime[-1] > 86400:
                    k = k-1
                    fname = event[dtime_index[0]][0:5] + \
                        '000000'+'_'+stacha[dtime_index[0]]
                    fname0 = fname
                    fname = os.path.join(outdir, dirname, fname)

                    ii = 0
                    temp = [os.path.join(outdir, 'temp0')]
                    trace[dtime_index[0]].write(temp[-1], format='SAC')
                    st2 = obspy.read(temp[-1])
                    while ii < len(dtime)-2:
                        ii += 1
                        temp.append(os.path.join(
                            outdir, dirname, 'temp'+str(ii)))
                        trace[dtime_index[ii]].write(temp[-1], format='SAC')
                        st2 += obspy.read(temp[-1])

                    if output_fragmented == 'yes':
                        c = 1
                        for tmp in temp:
                            shutil.copyfile(tmp, fname+'.p'+str('%03d' % (c)))
                            c += 1

                    for tmp in temp:
                        os.remove(tmp)

                    st2.sort(['starttime'])
                    st2.merge(method=1, fill_value=0)
                    tr = st2[0]
                    begin_time = int(tr.stats.starttime.hour*3600 +
                                     tr.stats.starttime.minute*60 +
                                     tr.stats.starttime.second)
                    st2.write(fname, format='SAC')
                    sac_setBegin(fname, begin_time)
                    sac_dailyCut(fname)

                    ref = current_index
                    dtime = []
                    dtime_index = []

                elif current_index == stacha_index_group[i][-1]:
                    fname = event[dtime_index[0]]+'_'+stacha[dtime_index[0]]
                    fname0 = fname
                    fname = os.path.join(outdir, dirname, fname)

                    ii = 0
                    temp = [os.path.join(outdir, dirname, 'temp0')]
                    trace[dtime_index[0]].write(temp[-1], format='SAC')
                    st2 = obspy.read(temp[-1])
                    while ii < len(dtime)-1:
                        ii += 1
                        temp.append(os.path.join(outdir, 'temp'+str(ii)))
                        trace[dtime_index[ii]].write(temp[-1], format='SAC')
                        st2 += obspy.read(temp[-1])

                    if output_fragmented == 'yes':
                        c = 1
                        for tmp in temp:
                            shutil.copyfile(tmp, fname+'.p'+str('%03d' % (c)))
                            c += 1

                    for tmp in temp:
                        os.remove(tmp)

                    st2.merge(method=1, fill_value=0)
                    tr = st2[0]
                    begin_time = int(tr.stats.starttime.hour*3600 +
                                     tr.stats.starttime.minute*60 +
                                     tr.stats.starttime.second)
                    st2.write(fname, format='SAC')
                    sac_setBegin(fname, begin_time)
                    sac_dailyCut(fname)

                k = k+1

print('\n\nDone!\n')
