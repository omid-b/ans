#!/usr/bin/env python3
# Given a folder of EGF sac files, this script generates the reverese EGFs with corrected sac header information
# Note that the EGF filenames should be in the form: "sta1_sta2_chn.sac"
# UPDATE: 12 Jan 2021

import os
import sys
os.system('clear')

about = " Given a folder of EGF sac files, this script generates the reverese EGFs with corrected sac header information\n"
usage = '''
python3 ANT_gen_reversed_EGFs.py [input_EGF_dir] [output_EGF_dir]

'''

print(about)

if len(sys.argv) != 3:
    print(f"Error Usage!\n{usage}")
    exit()
else:
    inpDir = os.path.abspath(sys.argv[1])
    outDir = os.path.abspath(sys.argv[2])

try:
    from shutil import copyfile
    import subprocess
    from glob import glob
    from obspy import read
except ImportError as ie:
    print(f'{ie}')
    exit()

if os.path.isdir(inpDir):
    egfs = []
    for egf in glob(f"{inpDir}/*_*_*.sac"):
        egf = os.path.basename(egf)
        egfs.append(egf)
else:
    print(f"Error! Could not find the input EGF directory.\n{usage}")
    exit()

report = f"  Input EGF directory: {inpDir}\n  Output directory:    {outDir}\n  Number of EGFs: {len(egfs)}\n"
print(report)

#----FUNCTION----#

def read_sac_headers(basedir, sacfile):
    egf = os.path.join(basedir, sacfile)
    tr = read(egf, headonly=True)[0]
    headers = {}
    headers['stla'] = tr.stats.sac.stla
    headers['stlo'] = tr.stats.sac.stlo
    headers['stel'] = tr.stats.sac.stel
    headers['evla'] = tr.stats.sac.evla
    headers['evlo'] = tr.stats.sac.evlo
    headers['evel'] = tr.stats.sac.evel
    headers['kstnm'] = tr.stats.sac.kstnm
    headers['knetwk'] = tr.stats.sac.knetwk
    return headers


def write_sac_headers(basedir, sacfile, headers):
    egf = os.path.join(basedir, sacfile)
    st = read(egf, format='SAC')
    st[0].stats.sac.stlo = headers['stlo']
    st[0].stats.sac.stla = headers['stla']
    st[0].stats.sac.stel = headers['stel']
    st[0].stats.sac.evla = headers['evla']
    st[0].stats.sac.evlo = headers['evlo']
    st[0].stats.sac.evel = headers['evel']
    st[0].stats.station = "%s" %(headers['kstnm'])
    st[0].stats.network = headers['knetwk']
    st[0].write(egf, format='SAC')


def gen_reversed_egf(inpDir, outDir, egf):
    inpEGF = os.path.join(inpDir, egf)
    sta1 = egf.split('_')[0]
    sta2 = egf.split('_')[1]
    chn = egf.split('_')[2].split('.')[0]
    outEGF = f"{sta2}_{sta1}_{chn}.sac"
    outEGF = os.path.join(outDir, outEGF)
    st = read(inpEGF,format='SAC')
    st[0].data = st[0].data[::-1]
    st[0].write(outEGF,format='SAC')
    inpHeaders = read_sac_headers(inpDir, egf)
    outHeaders = dict()
    outHeaders['stla'] = float(inpHeaders['evla'])
    outHeaders['stlo'] = float(inpHeaders['evlo'])
    outHeaders['stel'] = float(inpHeaders['evel'])
    outHeaders['evla'] = float(inpHeaders['stla'] )
    outHeaders['evlo'] = float(inpHeaders['stlo'] )
    outHeaders['evel'] = float(inpHeaders['stel'])
    outHeaders['kstnm'] = str(f"{inpHeaders['kstnm'].split('-')[1]}-{inpHeaders['kstnm'].split('-')[0]}")
    outHeaders['knetwk'] = str(f"{inpHeaders['knetwk'].split('-')[1]}-{inpHeaders['knetwk'].split('-')[0]}")
    write_sac_headers(outDir, outEGF, outHeaders)

#----------------#

if not os.path.isdir(outDir):
    os.mkdir(outDir)

i = 0
for egf in egfs:
    i += 1
    print(f"{i} of {len(egfs)}: {egf}")
    copyfile(os.path.join(inpDir, egf), os.path.join(outDir, egf))
    gen_reversed_egf(inpDir, outDir, egf)

print('\nDone!\n')

