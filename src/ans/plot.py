import os
import sys
import numpy as np
import subprocess
from . import config
from . import download

pkg_dir, _ = os.path.split(__file__)


def remove_gmt_temp(fdir, fname):
    flist = [f"{fname}.tmp",
    f"{fname}.eps",f"{fname}.epsi",
    "gmt.conf","gmt.history"]
    for f in flist:
        if os.path.isfile(os.path.join(fdir,f)):
            os.remove(os.path.join(fdir,f))


def ps2pdf(input_ps, outdir):
    fname, _ = os.path.splitext(os.path.split(input_ps)[1])
    fname_ext_out = f"{fname}.pdf"
    if sys.platform in ["linux","linux2","darwin"]:
        # method 1: works on MacOS and Ubuntu
        if subprocess.call('ps2eps --version',shell=True,
        stderr=subprocess.STDOUT,
        stdout=subprocess.DEVNULL) == 0:
            script = [f"ps2eps {fname}.ps --quiet -f",
            f"epstopdf {fname}.eps --outfile={os.path.join(outdir,fname)}.pdf --quiet"]
            subprocess.call('\n'.join(script), shell=True)
        # method 2: works on CentOS
        if subprocess.call('ps2epsi --version',shell=True,
        stderr=subprocess.STDOUT,
        stdout=subprocess.DEVNULL) == 0\
        and not os.path.isfile(f"{fname}.eps"):
            script = [f"ps2epsi {fname}.ps {fname}.epsi",
            f"epstopdf {fname}.epsi --outfile={os.path.join(outdir,fname)}.pdf"]
            subprocess.call('\n'.join(script), shell=True)
    if not os.path.isfile(os.path.join(outdir,f'{fname}.pdf')):
        shutil.copyfile(input_ps,os.path.join(outdir,fname_ext_out))
        fname_ext_out = f"{fname}.ps"
    return fname_ext_out



def plot_stations(maindir, labels=False):
    padding_fac = 0.10
    # get/calc variables
    cfg = config.read_config(maindir)
    tempdir = os.path.join(maindir,'.ans')
    _, fname = os.path.split(cfg['download']['le_stalist'])
    fname, _ = os.path.splitext(fname)

    stations = download.STATIONS(maindir)
    stations = stations.read_stalist()
    if len(stations['lon']) == 0:
        print(f"\nError! No station is listed in the station file!\n")
        exit(1)
    print(f"Station list: {os.path.split(cfg['download']['le_stalist'])[1]}\n")
    region_centre = [np.mean([cfg['setting']['le_minlon'], cfg['setting']['le_maxlon']]),
                     np.mean([cfg['setting']['le_minlat'], cfg['setting']['le_maxlat']])]
    prj = f"L{region_centre[0]}/{region_centre[1]}/{cfg['setting']['le_minlat']}/{cfg['setting']['le_maxlat']}/800p"
    lat_fac = np.cos(np.deg2rad(region_centre[1]))
    if lat_fac < 0.3:
        lat_fac = 0.3
    lon_pad = (cfg['setting']['le_maxlon'] - cfg['setting']['le_minlon']) * padding_fac
    lat_pad = (cfg['setting']['le_maxlat'] - cfg['setting']['le_minlat']) * padding_fac * lat_fac
    reg = "%.2f/%.2f/%.2f/%.2f" \
    %(cfg['setting']['le_minlon']-lon_pad, cfg['setting']['le_maxlon']+lon_pad,\
      cfg['setting']['le_minlat']-lat_pad, cfg['setting']['le_maxlat']+lat_pad)
    # bulid plot script and run
    print(f"  Generating stations map plot ...\n")
    remove_gmt_temp(tempdir, fname)
    # GMT
    GMT = cfg['setting']['le_gmt']
    if not os.path.isfile(GMT):
    	print(f"Error! Could not find GMT executable:\nGMT: '{GMT}'\n")
    	exit(1)
    os.chdir(tempdir)
    gmt_script = [\
    f"{GMT} set PS_MEDIA 2000px2000p",
    f"{GMT} set GMT_VERBOSE q",
    f"{GMT} set MAP_FRAME_PEN thin,black",
    f"{GMT} set MAP_GRID_CROSS_SIZE_PRIMARY 0",
    f"{GMT} set MAP_FRAME_TYPE plain",
    f"{GMT} set MAP_FRAME_PEN 2p,black",
    f"{GMT} set FONT_ANNOT_PRIMARY 18p,Helvetica,black",
    f"{GMT} pscoast -R{reg} -J{prj} -K -P -Di -Ba -A1000 -Givory3 -Slightcyan > {fname}.ps"]
    fopen = open(f"{fname}.dat",'w')
    for i in range(len(stations['lon'])):
        fopen.write(f"{stations['lon'][i]} {stations['lat'][i]}\n")
    fopen.close()
    fopen = open(f"{fname}.tmp",'w')
    for i in range(len(stations['lon'])):
        fopen.write(f"{stations['lon'][i]} {stations['lat'][i]} {stations['net'][i]}.{stations['sta'][i]}\n")
    fopen.close()
    if labels:
        gmt_script += [f"cat {fname}.tmp| gmt pstext -D0/-0.27i -F+f11p,Helvetica-Bold,black -R -J -P -K -O >> {fname}.ps"]
    gmt_script += [f"cat {fname}.dat | gmt psxy -R -J -K -O -P -Si15p -Groyalblue4 -Wthin,black >> {fname}.ps",
    f"echo 0 0|gmt psxy -R -J -P -O -Sc0.001p -Gblack -Wthin,black >> {fname}.ps"]
    subprocess.call("\n".join(gmt_script), shell=True)
    outfile = ps2pdf(f"{fname}.ps", maindir)
    remove_gmt_temp(tempdir, fname)
    print(f"Output figure in project directory: {outfile}\n\nDone!\n")




