#!/usr/env/bin python3 

about = 'This script carries out directionality analysis of seismic ambient noise EGFs.\n'

usage = '''
# Usage 1: generate pickle file ("pickle_data")
> python3 ANT_directionality.py  EGF_dir

# Usage 2: directionality analysis of the entire dataset
  (all items stored in "pickle_data")
> python3 ANT_directionality.py  pickle_data  analysis_dir

# Usage 3: directionality analysis for subsets of stations
> python3 ANT_directionality.py  pickle_data  analysis_dir  staset_1  ...  staset_n

---------------------------------------------------------------------
"EGF_dir": path to directory containing non-symmetrized EGFs

"pickle_data": a python pickle file that is the output of Usage 1

"analysis_dir": path to the analysis outputs (will be created if does not exist)

"staset_1" to "staset_n": text file with one column (station name)
'''

# Note: Input EGFs must be sacfiles with the following sac headers:
#       b = -86400, e = 86400, delta = 1

# UPDATE: 29 Oct 2020
# CODED BY: omid.bagherpur@gmail.com
#====Adjustable Parameters====#
SAC = "/usr/local/sac/bin/sac"  # path to the SAC software
signal_vel = [2, 4.5] # signal window velocity range (km/s); important in snr calculation
bandpass_prd = [] # a list of two bandpass corner periods (s); empty list for no bandpass

seism_cut = 800 # time limits to store the egf data into pickle file; same axis limit will be applied for plots
figure_size = 10 #a float
dist_ticks = 100 #yaxis ticks in stacked seismogram plots; an integer

angle_bin_size = 15 #must be in [5,10,15,20,30,45,60,90,180]; for region-based analysis, 45 is hardwired

figure_dpi = 300 # dpi = dot per inch
seismogram_amp_factor = 30 # affects the amplitude of EGFs in the EGF plots
seismogram_line_width = 0.5 # seismogram line width (pixels) in the EGF plots
moveouts = [2, 4.5] # a list of moveouts to be plotted; empty list to disable this option

sns_context = "notebook" # seaborn "set_context" value; "talk", "paper", "poster", "notebook"

title_y = -0.3 # title y adjustment (negative float)
bar_edge_alpha = 1 # a float between 0 and 1 (line opacity)
max_snr = 50 # max SNR value for png fan-diagrams (uniform color-scale)
#=============================#
import os
os.system('clear')
print(about)

# import required modules
try:
    import re
    import sys
    import numpy as np
    import obspy
    import shutil
    import pandas as pd
    import seaborn as sns
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import subprocess
except ImportError as e:
    print(f'Import Error!\n{e}\n')
    exit()


if angle_bin_size not in [5,10,15,20,30,45,60,90,180]:
    print("Error! angle_bin_size parameter is not set correctly. Check the 'Adjustable Parameters' section.\n\n")
    exit()

bp = False
if len(bandpass_prd) == 2:
    if bandpass_prd[0] < bandpass_prd[1]:
        bp = True
        cf1 = 1/bandpass_prd[1]
        cf2 = 1/bandpass_prd[0]
    else:
        print("Error in 'bandpass_prd' parameter; check 'Adjustable Parameters' section\n\n")
        exit()
#----CLASSES & FUNCTIONS----#

class EGF:
    def __init__(self,sacfile):
        self.sacfile = os.path.abspath(sacfile)
        if bp:
            shell_cmd = ["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
            shell_cmd.append(f'r {self.sacfile}')
            shell_cmd.append(f'bp co {cf1} {cf2} n 3 p 2')
            shell_cmd.append(f'w tmp.sac')
            shell_cmd.append('quit')
            shell_cmd.append('EOF')
            shell_cmd = '\n'.join(shell_cmd)
            subprocess.call(shell_cmd, shell=True)
            self.trace = obspy.read('tmp.sac', format='SAC')[0]
            os.remove('tmp.sac')
        else:
            self.trace = obspy.read(self.sacfile, format='SAC')[0]

    def sta1(self):
        sta1 = os.path.basename(self.sacfile).split('_')[0]
        return sta1

    def lon1(self):
        lon1 = '%.2f' %(self.trace.stats.sac.evlo)
        return float(lon1)

    def lat1(self):
        lat1 = '%.2f' %(self.trace.stats.sac.evla)
        return float(lat1)

    def sta2(self):
        sta2 = os.path.basename(self.sacfile).split('_')[1]
        return sta2

    def lon2(self):
        lon2 = '%.2f' %(self.trace.stats.sac.stlo)
        return float(lon2)

    def lat2(self):
        lat2 = '%.2f' %(self.trace.stats.sac.stla)
        return float(lat2)

    def faz(self): # forward-azimuth
        faz = '%.2f' %(self.trace.stats.sac.az)
        return float(faz)

    def baz(self): # back-azimuth
        baz = '%.2f' %(self.trace.stats.sac.baz)
        return float(baz)

    def direction(self):
        azimuth = float(self.trace.stats.sac.baz)
        if azimuth < 22.5:
            direction = 'N-S'
        elif 337.5 <= azimuth or 157.5 <= azimuth < 202.5:
            direction = 'N-S'
        elif 22.5 <= azimuth < 67.5 or 202.5 <= azimuth < 247.5:
            direction = 'NE-SW'
        elif 67.5 <= azimuth < 112.5 or 247.5 <= azimuth < 292.5:
            direction = 'E-W'
        elif 112.5 <= azimuth < 157.5 or 292.5 <= azimuth < 337.5:
            direction = 'SE-NW'
        return direction

    def dist(self): # inter-station distance (km)
        dist = '%.4f' %(self.trace.stats.sac.dist)
        return float(dist)

    def nstack(self): # number of stacks (store in 'kevnm' header)
        kevnm = self.trace.stats.sac.kevnm
        return int(kevnm)

    def data(self):
        delta = self.trace.stats.sac.delta
        e = self.trace.stats.sac.e
        data = np.array(self.trace.data)
        i1 = int(e - (seism_cut/delta))
        i2 = i1+2*int(seism_cut/delta)+1
        return data[i1:i2]

    def times(self):
        delta = self.trace.stats.sac.delta
        times = np.arange(-seism_cut, seism_cut+delta, delta)
        return times

    def snr_sym(self, v1, v2): # v1 and v2 are velocity range of the signal (km/s)
        data_causal = np.array(self.trace.data)
        data_causal = data_causal[int(len(data_causal)/2):len(data_causal)]
        data_acausal = np.array(self.trace.data)[::-1]
        data_acausal = data_acausal[int(len(data_acausal)/2):len(data_acausal)]
        data = np.add(data_causal, data_acausal)
        data = np.divide(data,2)
        delta = self.trace.stats.sac.delta
        e = self.trace.stats.sac.e
        times = np.arange(0, e+delta, delta)
        dist = self.trace.stats.sac.dist
        t1 = dist/v2
        t2 = dist/v1
        signal = []
        noise = []
        for i in range(len(times)):
            if times[i] >= t1 and times[i] <= t2:
                signal.append(data[i])

        # same length window size for noise signal right after the signal window
        for i in range(len(times)):
            if times[i] > t2:
                while len(noise) != len(signal):
                    noise.append(data[i])

        srms = np.sqrt(np.nanmean(np.square(signal)))
        nrms = np.sqrt(np.nanmean(np.square(noise)))
        snr = 10*np.log10((srms**2)/(nrms**2))
        return float(snr)

    def snr_causal(self, v1, v2): # v1 and v2 are velocity range of the signal (km/s)
        data = np.array(self.trace.data)
        data = data[int(len(data)/2):len(data)]
        delta = self.trace.stats.sac.delta
        e = self.trace.stats.sac.e
        times = np.arange(0, e+delta, delta)
        dist = self.trace.stats.sac.dist
        t1 = dist/v2
        t2 = dist/v1
        signal = []
        noise = []
        for i in range(len(times)):
            if times[i] >= t1 and times[i] <= t2:
                signal.append(data[i])

        for i in range(len(times)):
            if times[i] > t2:
                while len(noise) != len(signal):
                    noise.append(data[i])

        srms = np.sqrt(np.nanmean(np.square(signal)))
        nrms = np.sqrt(np.nanmean(np.square(noise)))
        snr = 10*np.log10((srms**2)/(nrms**2))
        return float(snr)

    def snr_acausal(self, v1, v2): # v1 and v2 are velocity range of the signal (km/s)
        data = np.array(self.trace.data)[::-1]
        data = data[int(len(data)/2):len(data)]
        delta = self.trace.stats.sac.delta
        e = self.trace.stats.sac.e
        times = np.arange(0, e+delta, delta)
        dist = self.trace.stats.sac.dist
        t1 = dist/v2
        t2 = dist/v1
        signal = []
        noise = []
        for i in range(len(times)):
            if times[i] >= t1 and times[i] <= t2:
                signal.append(data[i])

        for i in range(len(times)):
            if times[i] > t2:
                while len(noise) != len(signal):
                    noise.append(data[i])

        srms = np.sqrt(np.nanmean(np.square(signal)))
        nrms = np.sqrt(np.nanmean(np.square(noise)))
        snr = 10*np.log10((srms**2)/(nrms**2))
        return float(snr)


def get_baz_direction(baz):
    if baz < 22.5 or baz >= 337.5:
        baz_direction = 'N'
    elif 22.5 <= baz < 67.5:
        baz_direction = 'NE'
    elif 67.5 <= baz < 112.5:
        baz_direction = 'E'
    elif 112.5 <= baz < 157.5:
        baz_direction = 'SE'
    elif 157.5 <= baz < 202.5:
        baz_direction = 'S'
    elif 202.5 <= baz < 247.5:
        baz_direction = 'SW'
    elif 247.5 <= baz < 292.5:
        baz_direction = 'W'
    elif 292.5 <= baz < 337.5:
        baz_direction = 'NW'

    return baz_direction


def get_angle_bins(angle_bin_size):
    angle_bins=[]
    angle_start = -(angle_bin_size/2)
    angle0 = angle_start
    angle1 = angle_start+angle_bin_size

    while angle1 != angle_start and angle1 != angle_start+360:       
        if (angle0+360) < 360:
            angle0=angle0+360
        elif (angle1+360) < 360:
            angle1=angle1+360

        angle_bins.append([angle0, angle1])
        angle0 = angle1
        angle1 = angle1+angle_bin_size
    
    if (angle_start+360) < 360:
            angle_start=angle_start+360

    angle_bins.append([angle0, angle_start])
    return angle_bins


def get_snr_rgba(value, maxValue):
    return plt.cm.jet((np.clip(value,0,maxValue))/maxValue)

def correct_snr(snr, dist, nstack, min_dist, mean_nstack):
    dist_factor = np.sqrt(dist)/np.sqrt(min_dist)
    nstack_factor = np.sqrt(mean_nstack)/np.sqrt(nstack)
    corrected_snr = snr*dist_factor*nstack_factor
    return float(corrected_snr)

#---------------------------#

usage1 = False
usage2 = False
usage3 = False

# python3 ANT_directionality.py  pickle_data  analysis_dir  staset_1  ...  staset_n

if len(sys.argv) == 2:
    print('Usage 1: generate pickle file ("pickle_data")\n')
    usage1 = True
    egf_dir = os.path.abspath(sys.argv[1])
    if not os.path.isdir(egf_dir):
        print("\nError! Could not find 'EGF_dir'.\n")
        exit()

elif len(sys.argv) == 3:
    print('Usage 2: directionality analysis of the entire dataset\n(all items stored in "pickle_data")\n')
    usage2 = True
    pickle_data = os.path.abspath(sys.argv[1])
    analysis_dir = os.path.abspath(sys.argv[2])
    if not os.path.isfile(pickle_data):
        print("\nError! Could not find 'pickle_data'.\n")
        exit()
    if os.path.isfile(analysis_dir):
        print("\nError! 'analysis_dir' will be created by by this script; a file is given!\n")
        exit()
elif len(sys.argv) > 3:
    print('Usage 3: directionality analysis for subsets of stations\n')
    usage3 = True
    pickle_data = os.path.abspath(sys.argv[1])
    analysis_dir = os.path.abspath(sys.argv[2])
    sta_grps = []
    for i in range(3 ,len(sys.argv)):
        grp = []
        if os.path.isfile(sys.argv[i]) == 0:
            print(f"Error! <Group {i-2}> does not exist: '{sys.argv[i]}'")
            exit()

        with open(sys.argv[i], 'r') as fn:
            for line in fn:
                grp.append(line.split()[0])

        sta_grps.append(grp)

    ngrps = len(sta_grps)
else:
    print(f'Error usage!\n{usage}')
    exit()

# General variables

moveout_text = ''
if len(moveouts):
    moveout_text = 'Moveouts (dashed orange lines) are plotted for %s km/s.' %(' '.join(str(moveouts)).replace('[','').replace(']','').replace(',',' and'))

#directions information
angle_bins = get_angle_bins(45)
directions = ['N-S','NE-SW','E-W','SE-NW']
direction_labels = ['North-South','Northeast-Southwest','East-West','Southeast-Northwest']
direction_labels2 = ['N','NE','E','SE','S','SW','W','NW','N']
direction_labels2 = ['N','NE','E','SE','S','SW','W','NW','N']
direction_color = [(49/255, 115/255, 161/255, 1),(226/255, 129/255, 47/255, 1),\
                            (73/255, 145/255, 59/255, 1),(193/255, 61/255, 62/255, 1),\
                   (49/255, 115/255, 161/255, 1),(226/255, 129/255, 47/255, 1),\
                            (73/255, 145/255, 59/255, 1),(193/255, 61/255, 62/255, 1)]
reverse_condition = [157.5, 202.5, 247.5, 292.5]
angle_centres = [[0,180],[45, 225],[90, 270],[135, 315]]

#====USAGE 1====#
# Generate pickle file
if usage1:
    egfs = []
    for x in os.listdir(egf_dir):
        if re.search('(sac)$', x):
            egfs.append(os.path.join(egf_dir, x))

    egfs = sorted(egfs)
    if len(egfs) == 0:
        print('\nError! Could not find any "*.sac" file in the given "EGF_dir".\n')
        exit()
    
    if bp:
        print(f'WARNING! Bandpass filtering will be carried out for the analysis.\n  Bandpass periods: [{bandpass_prd[0]}, {bandpass_prd[1]}]\n')

    # store nstack and dist values for further snr corrections
    dist = []
    nstack = []
    for i in range(len(egfs)):
        print('  Collecting dataset information ... %.0f%s' %((i+1)/len(egfs)*100, '%'), end='  \r')
        egf = EGF(egfs[i])
        dist.append(egf.dist())
        nstack.append(egf.nstack())

    min_dist = np.nanmin(dist)
    mean_nstack = np.nanmean(nstack)
    
    if bp:
        pickle_data = os.path.join(egf_dir.split(f"{os.path.basename(egf_dir)}")[0], f'{os.path.basename(egf_dir)}_directionality_{bandpass_prd[0]}-{bandpass_prd[1]}s.pkl')
    else:
        pickle_data = os.path.join(egf_dir.split(f"{os.path.basename(egf_dir)}")[0], f'{os.path.basename(egf_dir)}_directionality.pkl')

    report = "\n\nNumber of EGFs: %d\nInter-station distance: %.0f-%.0f km\nEGF datasets:  %s\nOutput pickle: %s\n" %(len(egfs), np.nanmin(dist), np.nanmax(dist), egf_dir, pickle_data)

    print(report)

    
    uin = input("Do you want to continue generating the pickle file (y/n)? ")
    if uin.lower() != 'y':
        print("\nExit program!\n")
        exit()
    else:
        print("\n")

    sta1 = [] # station A name
    lon1 = [] # station A longitude
    lat1 = [] # station A latitude
    sta2 = [] # station B name
    lon2 = [] # station B longitude
    lat2 = [] # station B latitude
    faz = [] # forward- azimuths
    baz = [] # back-azimuths
    direction = [] # azimuthal groups (S-N, SW-NE, W-E, NW-SE)
    baz_direction = [] # backazimuth direction (N, NE, E, SE, S, SW, W, NW)
    dist = [] # inter-station distance (km)
    nstack = [] # number of stacks that made the egf
    data = [] # independent variable
    times = [] # dependent variable 
    snr_sym = [] # symmetrized egf snr
    snr_sym_corr = [] # symmetrized egf snr (corrected)
    snr_causal_corr = [] # causal egf signal snr (corrected)
    snr_acausal_corr = [] # acausal egf signal snr (corrected)
    for i in range(len(egfs)):
        print('  Processing EGFs ... %.0f%s' %((i+1)/len(egfs)*100, '%'), end='  \r')
        egf = EGF(egfs[i])

        # append original (non-reveresed) egf information to lists
        sta1.append(egf.sta1())
        sta2.append(egf.sta2())
        lon1.append(egf.lon1())
        lat1.append(egf.lat1())
        lon2.append(egf.lon2())
        lat2.append(egf.lat2())
        faz.append(egf.faz())
        baz.append(egf.baz())
        baz_direction.append(get_baz_direction(egf.baz()))
        direction.append(egf.direction())
        dist.append(egf.dist())
        nstack.append(egf.nstack())
        data.append(egf.data())
        times.append(egf.times())
        snr_sym_corrected = correct_snr(egf.snr_sym(signal_vel[0], signal_vel[1]),\
         egf.dist(), egf.nstack(), min_dist, mean_nstack)
        snr_causal_corrected = correct_snr(egf.snr_causal(signal_vel[0], signal_vel[1]),\
         egf.dist(), egf.nstack(), min_dist, mean_nstack)
        snr_acausal_corrected = correct_snr(egf.snr_acausal(signal_vel[0], signal_vel[1]),\
         egf.dist(), egf.nstack(), min_dist, mean_nstack)
        snr_sym.append(egf.snr_sym(signal_vel[0], signal_vel[1]))
        snr_sym_corr.append(snr_sym_corrected)
        snr_causal_corr.append(snr_causal_corrected)
        snr_acausal_corr.append(snr_acausal_corrected)

        # append reveresed egf information to lists
        sta1.append(egf.sta2())
        sta2.append(egf.sta1())
        lon1.append(egf.lon2())
        lat1.append(egf.lat2())
        lon2.append(egf.lon1())
        lat2.append(egf.lat1())
        faz.append(egf.baz())
        baz.append(egf.faz())
        baz_direction.append(get_baz_direction(egf.faz()))
        direction.append(egf.direction())
        dist.append(egf.dist())
        nstack.append(egf.nstack())
        data.append(egf.data()[::-1])
        times.append(egf.times())
        snr_sym.append(egf.snr_sym(signal_vel[0], signal_vel[1]))
        snr_sym_corr.append(snr_sym_corrected)
        snr_causal_corr.append(snr_acausal_corrected)
        snr_acausal_corr.append(snr_causal_corrected)

    print("\n  Storing dataset into pandas pickle format \n")

    dataset = {'sta1':sta1, 'sta2':sta2, 'lon1':lon1, 'lat1':lat1, 'lon2':lon2, 'lat2':lat2, 'faz':faz, 'baz':baz, 'direction':direction, 'baz_direction':baz_direction, 'dist':dist, 'nstack':nstack, 'data':data, 'times':times, 'snr_sym':snr_sym, 'snr_sym_corr':snr_sym_corr, 'snr_causal_corr':snr_causal_corr, 'snr_acausal_corr':snr_acausal_corr}
    dataset = pd.DataFrame(dataset).reset_index()
    dataset.to_pickle(f'{pickle_data}')

    

#====USAGE 2====#
# directionality analysis of the entire dataset
if usage2:
    print("  Reading 'pickle_data' ... ", end='   \r')
    try:
        dataset = pd.read_pickle(pickle_data)
    except Exception as e:
        print(f"\n\nError reading pickle file!\n{e}\n")
        exit()

    #save a different version of dataset excluding the reveresed data (every two rows)
    mask = []
    for i in range(len(dataset)):
        if i in range(0,len(dataset),2):
            mask.append(True)
        else:
            mask.append(False)

    dataset2 = dataset[mask].reset_index()
    print("  Reading 'pickle_data' ... Done.\n")


    report = f"Number of EGFs: %d\nSNR (symmetrized) range (min, max): %.2f  %.2f\nInter-station distance range (min, max): %.2f  %.2f\nPickle file: '{os.path.basename(pickle_data)}'\nAnalysis directory: {analysis_dir}\n" %(len(dataset)/2, dataset['snr_sym'].min(), dataset['snr_sym'].max(), dataset['dist'].min(), dataset['dist'].max())

    print(report)

    uin = input("Do you want to continue (y/n)? ")
    if uin.lower() != 'y':
        print("\nExit program!\n")
        exit()
    else:
        print("\n")

    if not os.path.isdir(analysis_dir):
        os.mkdir(analysis_dir)


    ########################################
    # Region-based directionality analysis #
    ########################################

    dirname = os.path.join(analysis_dir, 'region_directionality')
    nop = 8 #number of plots, used only for printing progress

    if os.path.isdir(dirname):
        shutil.rmtree(dirname)
        os.mkdir(dirname)
    else:
        os.mkdir(dirname)

    for i in range(4):
        print(f"  Region-based directionality analysis progress: %3.0f" %(i/nop*100), end='%       \r')
        angle_bins_region = [angle_bins[i][0], angle_bins[i][1], angle_bins[i+4][0], angle_bins[i+4][1]]
        data_selected = []
        times_selected = []
        faz_selected = []
        baz_selected = []
        dist_selected = []
        snr_selected = []
        asnr_selected = []

        for j in range(len(dataset2)):
            faz = dataset2.iloc[j]['baz']
            baz = dataset2.iloc[j]['baz']
            dist = dataset2.iloc[j]['dist']
            times = dataset2.iloc[j]['times']
            if i == 0:

                if faz >= angle_bins_region[0] or faz < angle_bins_region[1]: #does not need reversing
                    data_selected.append(dataset2.iloc[j]['data'])
                    times_selected.append(times)
                    faz_selected.append(dataset2.iloc[j]['faz'])
                    baz_selected.append(dataset2.iloc[j]['baz'])
                    snr_selected.append(dataset2.iloc[j]['snr_causal_corr'])
                    asnr_selected.append(dataset2.iloc[j]['snr_acausal_corr'])
                    dist_selected.append(dist)
                elif angle_bins_region[2] <= faz < angle_bins_region[3]: #needs reversing
                    data_selected.append(dataset2.iloc[j]['data'][::-1])
                    times_selected.append(times)
                    faz_selected.append(dataset2.iloc[j]['baz'])
                    baz_selected.append(dataset2.iloc[j]['faz'])
                    snr_selected.append(dataset2.iloc[j]['snr_acausal_corr'])
                    asnr_selected.append(dataset2.iloc[j]['snr_causal_corr'])
                    dist_selected.append(dist)
                    

            else:

                if angle_bins_region[0] <= faz < angle_bins_region[1]: #does not need reversing
                    data_selected.append(dataset2.iloc[j]['data'])
                    times_selected.append(times)
                    faz_selected.append(dataset2.iloc[j]['faz'])
                    baz_selected.append(dataset2.iloc[j]['baz'])
                    snr_selected.append(dataset2.iloc[j]['snr_causal_corr'])
                    asnr_selected.append(dataset2.iloc[j]['snr_acausal_corr'])
                    dist_selected.append(dist)
                elif angle_bins_region[2] <= faz < angle_bins_region[3]: #needs reversing
                    data_selected.append(dataset2.iloc[j]['data'][::-1])
                    times_selected.append(times)
                    faz_selected.append(dataset2.iloc[j]['baz'])
                    baz_selected.append(dataset2.iloc[j]['faz'])
                    snr_selected.append(dataset2.iloc[j]['snr_acausal_corr'])
                    asnr_selected.append(dataset2.iloc[j]['snr_causal_corr'])
                    dist_selected.append(dist)
        
        df = pd.DataFrame({'data':data_selected, 'times':times_selected, 'faz':faz_selected, 'baz':baz_selected, 'dist':dist_selected, 'snr':snr_selected, 'asnr':asnr_selected}).sort_values(by='dist', ascending=True).reset_index()
        
        
        #plot for S-N, SW-NE, W-E, NW-SE
        sns.set_style("white") #seaborn style
        sns.set_context(sns_context)
        f=plt.figure(figsize=(figure_size*2,figure_size))
        pdf = os.path.join(dirname, f'{directions[i]}.pdf')
        f.suptitle(f"Negative lag signals indicate the ambient seismic noise contribution coming from the {direction_labels[i].split('-')[1]}\nPositive lag signals indicate the ambient seismic noise contribution coming from the {direction_labels[i].split('-')[0]}.\nNumber of cross-correlograms = {len(df)}; percentile(95) of causal SNRs = %.2f; percentile(95) of acausal SNRs = %.2f. {moveout_text}" %(df['snr'].quantile(0.95),df['asnr'].quantile(0.95)),x=0.01,y=0.98, ha='left')
        plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.3, hspace=0.3)
        #Subplot 1: Stacked cross-correlation
        ax1=plt.subplot2grid((50, 51), (0, 0),rowspan=50, colspan=30)
        amplitude_size = (df['dist'].max()-df['dist'].min())/seismogram_amp_factor
        for k in range(len(df)):
            time = df.iloc[k]['times']
            amplitude = np.divide(df.iloc[k]['data'], np.max(df.iloc[k]['data']))
            amplitude = np.multiply(amplitude, amplitude_size)
            amplitude = np.add(amplitude, df.iloc[k]['dist'])
            ax1=plt.plot(time,amplitude,linewidth=seismogram_line_width, color='k')

        ax1=plt.yticks(range(0,10000,dist_ticks))
        if len(df) > 1:
            ax1=plt.ylim([df['dist'].min()-amplitude_size*1.2, df['dist'].max()+amplitude_size*1.2])
            for moveout in moveouts:
                x1 = [-df['dist'].min()/moveout, -df['dist'].max()/moveout]
                x2 = [df['dist'].min()/moveout, df['dist'].max()/moveout]
                y = [df['dist'].min(), df['dist'].max()]
                ax1=plt.plot(x1,y,linewidth=2, linestyle='--', dashes=(10, 5), color=(255/255, 102/255, 0,1))
                ax1=plt.plot(x2,y,linewidth=2, linestyle='--', dashes=(10, 5), color=(255/255, 102/255, 0,1))

        ax1=plt.gca().invert_yaxis()
        ax1=plt.margins(x=0.01, y=0.01)
        ax1=plt.xlabel('Correlation lag (sec)')
        ax1=plt.ylabel('Inter-station distance (km)')
        ax1=plt.title(f'Stacked cross-correlations for stations along {directions[i]}')
        
        #SNR histogram
        ax2=plt.subplot2grid((50, 51), (30, 32),rowspan=20, colspan=19)
        ax2=plt.hist(df['snr'], color=(0,1,0,0.5), bins='auto', edgecolor='k', label='Positive lag SNR (causal)')
        ax2=plt.hist(df['asnr'], color=(1,0,0,0.5), bins='auto', edgecolor='k', label='Negative lag SNR (acausal)')
        ax2=plt.xlabel('SNR')
        ax2=plt.ylabel('Number')
        ax2=plt.legend()

        #Angle coverage
        ax3=plt.subplot2grid((50, 51), (0, 32),rowspan=20, colspan=20, projection='polar')
        ax3.set_theta_zero_location("N")
        ax3.set_theta_direction(-1)
        plt.yticks([],[])
        bars=ax3.bar(np.deg2rad(angle_centres[i]), [1,1], bottom=0,width=np.deg2rad(45))
        bars[0].set_color((0,1,0,0.5))
        bars[1].set_color((1,0,0,0.5))
        ax3=plt.title('Azimuthal coverage', y=title_y*0.7)


        plt.savefig(pdf,dpi=figure_dpi)
        plt.close()
    
    
    #Fan diagram for the entire dataset
    print(f"  Region-based directionality analysis progress: %3.0f" %(4/nop*100), end='%       \r')
    
    #Fan diagram calculations
    angle_bins = get_angle_bins(angle_bin_size)
    angle_centres = range(0,360,angle_bin_size)
    nbins = len(angle_bins)
    snrc_baz_group = [ [] for i in range(nbins) ]

    for i in range(len(dataset)):
        if dataset['baz'][i] >= angle_bins[0][0] or dataset['baz'][i] < angle_bins[0][1]:
            snrc_baz_group[0].append(dataset['snr_causal_corr'][i])
        else:
            for j in range(1, nbins):
                if angle_bins[j][0] <= dataset['baz'][i] < angle_bins[j][1]:
                    snrc_baz_group[j].append(dataset['snr_causal_corr'][i])


    snrc_baz_group_mean = [] #mean of (corrected) snr values for each baz snrc group; -999 if len(snrc_baz_group[i]) == 0

    isbar_baz = [] #1 if average snr value is available for the angle bin, and 0 if not!
    for i in range(nbins):
        if len(snrc_baz_group[i]):
            snrc_baz_group_mean.append(np.mean(snrc_baz_group[i]))
            isbar_baz.append(1)
        else:
            snrc_baz_group_mean.append(-999)
            isbar_baz.append(0)

    #fan diagram plotting
    angle_centres=np.deg2rad(angle_centres)
    pdf=os.path.join(dirname,f'fan-diagram.pdf')
    png=os.path.join(dirname,f'fan-diagram.png')
    f= plt.figure(figsize=(figure_size*0.9,figure_size))
    sns.set_context(sns_context)
    f.suptitle(f"High SNR bars in the fan digram show the direction of noise sources.\nAverage longitude: %.4f, average latitude: %.4f" %(dataset['lon1'].mean(), dataset['lat1'].mean()),x=0.01,y=0.98, ha='left') 

    ax1=plt.subplot2grid((50,50), (0, 3),rowspan=48, colspan=46, projection='polar')
    ax1.set_theta_zero_location("N")
    ax1.set_theta_direction(-1)
    ax1.set_xticks(np.deg2rad([0,90,180,270]))
    plt.yticks([],[])
    plt.margins(0)
    
    bars=ax1.bar(angle_centres, isbar_baz, bottom=0,width=np.deg2rad(angle_bin_size))

    dat = open(os.path.join(dirname,f'fan-diagram-stats.dat'), 'w')
    dat.write("baz(deg) #EGFs min_snr max_snr avg_snr\n")

    i=0
    for bar in bars:
        if isbar_baz[i]:
            dat.write(f"%03.0f-%03.0f %4d %7.2f %7.2f %7.2f\n" %(angle_bins[i][0], angle_bins[i][1], len(snrc_baz_group[i]), np.min(snrc_baz_group[i]), np.max(snrc_baz_group[i]), np.mean(snrc_baz_group[i])))
        bar.set_color(get_snr_rgba(snrc_baz_group_mean[i], np.max(snrc_baz_group_mean)))
        bar.set_edgecolor((0,0,0,bar_edge_alpha))
        i += 1

    dat.close()
    ax1=plt.title('Fan diagram (backazimuths)', y=title_y*0.4)

    ax2=plt.subplot2grid((50,50), (34, 0),rowspan=15, colspan=1)
    cmap = mpl.cm.jet
    norm = mpl.colors.Normalize(vmin=0, vmax=np.max(snrc_baz_group_mean))
    ax2 = mpl.colorbar.ColorbarBase(ax2, cmap=cmap, norm=norm, orientation='vertical')
    ax2=plt.xlabel('SNR (corrected)')


    plt.savefig(pdf,dpi=figure_dpi, transparent=True)
    plt.close()


    #fan diagram png plot
    sns.set_style('ticks')
    f= plt.figure(figsize=(figure_size, figure_size))
    sns.set_context(sns_context)
    ax1=plt.subplot2grid((10,10), (0, 0),rowspan=10, colspan=10, projection='polar')
    ax1.set_theta_zero_location("N")
    ax1.set_theta_direction(-1)
    plt.xticks([],[])
    plt.yticks([],[])
    ax1.set_ylim(0,1)

    bars=ax1.bar(angle_centres, isbar_baz, bottom=0,width=np.deg2rad(angle_bin_size))
    i=0
    for bar in bars:
        bar.set_color(get_snr_rgba(snrc_baz_group_mean[i], np.max(snrc_baz_group_mean)))
        i += 1

    ax1.spines['polar'].set_visible(False)
    plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    plt.savefig(png, format='png' ,dpi=figure_dpi, transparent=True)
    plt.close()

    print(f"  Region-based directionality analysis progress: %3.0f" %(5/nop*100), end='%       \r')
    
    sns.set_style("darkgrid")
    f = plt.figure(figsize=(figure_size*0.7,figure_size))
    sns.set_context(sns_context)
    pdf=os.path.join(dirname,f'./baz-regression.pdf')
    ax=plt.subplot2grid((10,10), (0, 0),rowspan=10, colspan=10)
    sns.lmplot(x='baz',y='snr_causal_corr',data=dataset, hue='direction')
    plt.xlim(0, 360)
    plt.ylim(0, max_snr)
    plt.xticks(range(0,405,45), direction_labels2)
    plt.xlabel('Backazimuths')
    plt.ylabel('SNR (corrected)')
    plt.savefig(pdf,dpi=figure_dpi)
    plt.close()

    print(f"  Region-based directionality analysis progress: %3.0f" %(6/nop*100), end='%       \r')

    sns.set_context(sns_context)
    sns.set_style("ticks")
    f = plt.figure(figsize=(figure_size,figure_size))
    pdf=os.path.join(dirname,f'./baz-boxplot.pdf')
    ax=plt.subplot2grid((10,10), (0, 0),rowspan=10, colspan=10)
    sns.boxplot(x='baz_direction',y='snr_causal_corr',data=dataset.sort_values(by='baz'), palette=direction_color)
    plt.xlabel('Backazimuth directions')
    plt.ylabel('Causal SNR (corrected)')
    plt.savefig(pdf,dpi=figure_dpi)
    plt.close()

    print(f"  Region-based directionality analysis progress: 100%")

    #########################################
    # Station-based directionality analysis #
    #########################################
    stations = dataset['sta1'].unique()

    sns.set_style("white")
    dirname = os.path.join(analysis_dir, 'station_directionality')

    if os.path.isdir(dirname):
        shutil.rmtree(dirname)
        os.mkdir(dirname)
    else:
        os.mkdir(dirname)

    dirname2 = os.path.join(dirname, 'png')
    os.mkdir(dirname2)

    #plot seismograms, BAZ distribution, and fan diagrams for each station
    with open(os.path.join(dirname2, 'pnglist.dat'), 'w') as fn:
        for station in stations:
            lon = "%.4f" %(dataset[dataset.sta1 == station].reset_index().loc[0]['lon1'])
            lat = "%.4f" %(dataset[dataset.sta1 == station].reset_index().loc[0]['lat1'])
            fn.write(f"png/{station}.png {lon} {lat}\n")

    k = -1
    for station in stations:
        k += 1
        print(f"  Station-based directionality analysis progress: {int(((k+1)/len(stations))*100)}", end='%       \r')
        df = dataset.loc[dataset['sta1'] == station]
        df = df.sort_values(by='dist',ascending=True).reset_index()
        #collect data (amplitude of signals) for plots
        pdf = os.path.join(dirname,f'{station}.pdf')
        dat = open(os.path.join(dirname,f'{station}.dat'), 'w')
        dat.write('#station 2, distance (km), backazimuth (deg), causal SNR (corrected), acausal SNR (corrected)\n')

        f=plt.figure(figsize=(figure_size*1.2,figure_size))
        sns.set_context(sns_context)

        fan_diagram_text = 'High SNR bars in the fan digram show the direction of noise sources.'

        f.suptitle(f'The causal signal (positive lags) indicate the outgoing signal.\nPercentile(95) of negative lag SNRs = %.2f; percentile(95) of positive lag SNRs = %.2f\n{fan_diagram_text}' %(df['snr_acausal_corr'].quantile(0.95),df['snr_causal_corr'].quantile(0.95)),x=0.01,y=0.98, ha='left')
        plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.3, hspace=0.3)
        #Subplot 1: Stacked cross-correlation
        ax1=plt.subplot2grid((50, 51), (0, 0),rowspan=50, colspan=30)
        amplitude_size = (np.max(df['dist'])-np.min(df['dist']))/seismogram_amp_factor
        for i in range(len(df)):
            dat.write(f'%4s %7.2f %6.2f %6.2f %6.2f\n' %(df['sta2'][i], df['dist'][i], df['baz'][i], df['snr_causal_corr'][i], df['snr_acausal_corr'][i]))
            amplitude = np.divide(df['data'][i], np.max(df['data'][i]))
            amplitude = np.multiply(amplitude, amplitude_size)
            amplitude = np.add(amplitude, df['dist'][i])
            ax1=plt.plot(time,amplitude,linewidth=seismogram_line_width, color='k')

        ax1=plt.yticks(range(0,10000,dist_ticks))
        if len(df['dist']) > 1:
            ax1=plt.ylim([df['dist'].min()-amplitude_size*1.2, df['dist'].max()+amplitude_size*1.2])

        ax1=plt.gca().invert_yaxis()
        ax1=plt.margins(x=0.01, y=0.01)
        ax1=plt.xlabel('Correlation lag (sec)')
        ax1=plt.ylabel('Inter-station distance (km)')
        ax1=plt.title(f'Stacked cross-correlations for station {station}')

        
        #Subplot 2: BAZ histogram
        degrees=np.asarray(df['baz'])
        radians=np.asarray(np.deg2rad(df['baz']))
        a, b=np.histogram(degrees, bins=np.arange(0-angle_bin_size/2, 360+angle_bin_size/2, angle_bin_size))
        centres=np.deg2rad(np.ediff1d(b)//2 + b[:-1])
        ax2=plt.subplot2grid((50, 51), (0, 31), rowspan=20, colspan=20, projection='polar')
        ax2.set_theta_zero_location("N")
        ax2.set_theta_direction(-1)
        bars=ax2.bar(centres, a, bottom=0,width=np.deg2rad(angle_bin_size), color='blue',edgecolor='k')
        for bar in bars:
            bar.set_alpha(0.8)

        ax2=plt.title('Backazimuth distribution', y=title_y*0.6)

        #Subplot 3: FAN diagrams

        #Step1: Fan diagram calculations
        angle_bins = get_angle_bins(angle_bin_size)
        angle_centres = range(0,360,angle_bin_size)
        nbins = len(angle_bins)
        snrc_baz_group = [ [] for i in range(nbins) ]

        for i in range(len(df)):
            if df['baz'][i] >= angle_bins[0][0] or df['baz'][i] < angle_bins[0][1]:
                snrc_baz_group[0].append(df['snr_causal_corr'][i])
            else:
                for j in range(1, nbins):
                    if angle_bins[j][0] <= df['baz'][i] < angle_bins[j][1]:
                        snrc_baz_group[j].append(df['snr_causal_corr'][i])

        snrc_baz_group_mean = [] #mean of (corrected) snr values for each baz snrc group; -999 if len(snrc_baz_group[i]) == 0
        isbar_baz = [] #1 if average snr value is available for the angle bin, and 0 if not!

        for i in range(nbins):
            if len(snrc_baz_group[i]):
                snrc_baz_group_mean.append(np.mean(snrc_baz_group[i]))
                isbar_baz.append(1)
            else:
                snrc_baz_group_mean.append(-999)
                isbar_baz.append(0)


        #Step 2: fan diagram plotting
        angle_centres=np.deg2rad(angle_centres)
        ax3=plt.subplot2grid((50, 51), (25, 31),rowspan=20, colspan=20, projection='polar')
        ax3.set_theta_zero_location("N")
        ax3.set_theta_direction(-1)
        plt.yticks([], [])
        bars=ax3.bar(angle_centres, isbar_baz, bottom=0,width=np.deg2rad(angle_bin_size))
        i=0
        for bar in bars:
            bar.set_color(get_snr_rgba(snrc_baz_group_mean[i], np.max(snrc_baz_group_mean)))
            bar.set_edgecolor('k')
            i += 1
        ax3=plt.title('Fan diagram (backazimuths)', y=title_y*0.6)

        ax4=plt.subplot2grid((50,50), (49, 35),rowspan=1, colspan=10)
        cmap = mpl.cm.jet
        norm = mpl.colors.Normalize(vmin=0, vmax=np.max(snrc_baz_group_mean))
        ax4 = mpl.colorbar.ColorbarBase(ax4, cmap=cmap, norm=norm, orientation='horizontal')
        ax4=plt.xlabel('SNR (corrected)')

        plt.savefig(pdf,dpi=figure_dpi)
        plt.close()

        #Step 3: fan diagram plotting (png)
        sns.set_style('ticks')
        sns.set_context(sns_context)
        png = os.path.join(dirname2,f'{station}.png')
        f= plt.figure(figsize=(figure_size, figure_size))
        ax1=plt.subplot2grid((10,10), (0, 0),rowspan=10, colspan=10, projection='polar')
        ax1.set_theta_zero_location("N")
        ax1.set_theta_direction(-1)
        plt.xticks([], [])
        plt.yticks([], [])
        ax1.set_ylim(0,1)

        bars=ax1.bar(angle_centres, isbar_baz, bottom=0,width=np.deg2rad(angle_bin_size))
        i=0
        for bar in bars:
            bar.set_color(get_snr_rgba(snrc_baz_group_mean[i], max_snr))
            i += 1

        ax1.spines['polar'].set_visible(False)
        plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
        plt.savefig(png, format='png' ,dpi=figure_dpi, transparent=True)
        plt.close()

    #Step 4: fan diagram plotting (scale bar)
    scale = os.path.join(dirname2,'SCALE.pdf')
    sns.set_context(sns_context)
    f= plt.figure(figsize=(figure_size, 0.15*figure_size))
    ax=plt.subplot2grid((2,10), (0, 0),rowspan=1, colspan=10)
    cmap = mpl.cm.jet
    norm = mpl.colors.Normalize(vmin=0, vmax=max_snr)
    ax = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='horizontal')
    plt.savefig(scale,format='pdf',dpi=figure_dpi)
    plt.close()

    print(f"  Station-based directionality analysis progress: 100%\n\n")


#====USAGE 3====#
# directionality analysis for subsets of stations
if usage3:
    print("  Reading 'pickle_data' ... ", end='   \r')
    try:
        dataset = pd.read_pickle(pickle_data)
    except Exception as e:
        print(f"\n\nError reading pickle file!\n{e}\n")
        exit()

    #save a different version of dataset excluding the reveresed data (every two rows)
    mask = []
    for i in range(len(dataset)):
        if i in range(0,len(dataset),2):
            mask.append(True)
        else:
            mask.append(False)

    stations = dataset['sta1'].unique()
    dataset2 = dataset[mask].reset_index()

    print("  Reading 'pickle_data' ... Done.\n")

    #check availability of all stations
    for i in range(ngrps):
        for sta in sta_grps[i]:
            if sta not in stations:
                print(f"Eror!\nCould not find station: '{sta}' from group: '{sys.argv[i+3]}' in dataset!")
                exit()


    time = dataset.iloc[0]['times']

    ######################
    # Start the analysis #
    ######################

    analysis_dir = analysis_dir
    nop = 7 #number of plots, used only for printing progress

    report = f"Number of station subsets: {len(sys.argv)-3}\nPickle file: '{os.path.basename(pickle_data)}'\nAnalysis directory: {analysis_dir}\n"

    print(report)

    uin = input("Do you want to continue (y/n)? ")
    if uin.lower() != 'y':
        print("\nExit program!\n")
        exit()
    else:
        print("\n")

    if not os.path.isdir(analysis_dir):
        os.mkdir(analysis_dir)

    for i in range(ngrps):
        print(f"  Generating plots for subset {i+1} of {ngrps}: '{os.path.basename(sys.argv[i+3])}'\n")
        #building sta_grps[i] dataframes
        df = pd.DataFrame()
        for sta in sta_grps[i]:
            df = pd.concat([df, dataset[dataset.sta1 == sta] ], axis=0, ignore_index=True)
        
        df.sort_values(by='sta1', ascending=True,inplace=True)
        df.reset_index(inplace=True)

        dirname = os.path.join(analysis_dir, "%s" %(sys.argv[i+3].split('/')[-1].split('.')[0]))
        
        if  os.path.isdir(dirname):
            shutil.rmtree(dirname)
            os.mkdir(dirname)
        else:
            os.mkdir(dirname)

        readme = open(os.path.join(dirname,'readme.txt'), 'w')
        readme.write(f"Average longitude and latitude:\n%.4f %.4f\n\nSNR (corrected) statistics:\n min=%.2f\n max=%.2f\n average=%.2f\n percentile(95)=%.2f\n\nStations in this group (#stations=%d):\n" %(df.lon1.mean(), df.lat1.mean(), df.snr_causal_corr.min(),df.snr_causal_corr.max(), df.snr_causal_corr.mean(), df.snr_causal_corr.quantile(0.95), len(sta_grps[i])))
        for sta in sta_grps[i]:
            readme.write(f"{sta}\n")

        readme.close()

        # baz regression plot
        sns.set_style("darkgrid")
        sns.set_context(sns_context)
        f= plt.figure(figsize=(figure_size*0.7,figure_size))
        pdf=os.path.join(dirname,f'baz-regression.pdf')
        sns.lmplot(x='baz',y='snr_causal_corr',data=df, hue='direction')
        plt.xlim(0, 360)
        plt.ylim(0, max_snr)
        plt.xticks(range(0,405,45), direction_labels2)
        plt.xlabel('Backazimuths')
        plt.ylabel('SNR (corrected)')
        plt.savefig(pdf,dpi=figure_dpi)
        plt.close()


        #Plot set 1: S-N, SW-NE, W-E, NW-SE
        for j in range(len(directions)):
            nod = len(df[df.direction == directions[j]])#number of rows in the selected dataset
            df2 = df[df.direction == directions[j]].sort_values(by='dist', ascending=True).reset_index(drop=True)
            timeseries = []
            asnr=[]
            snr=[]
            for k in range(nod):
                if df2.faz[k] < reverse_condition[j]:
                    timeseries.append(df2.data[k][::-1])
                    asnr.append(df2.snr_causal_corr[k])
                    snr.append(df2.snr_acausal_corr[k])
                else:
                    timeseries.append(df2.data[k])
                    asnr.append(df2.snr_acausal_corr[k])
                    snr.append(df2.snr_causal_corr[k])

            df2['data'] = timeseries
            df2['snr_acausal_corr'] = asnr
            df2['snr_causal_corr'] = snr

            #start plotting
            sns.set_style("white") #seaborn style
            sns.set_context(sns_context)
            f=plt.figure(figsize=(figure_size*2,figure_size))
            pdf = os.path.join(dirname, f'{directions[j]}.pdf')
            f.suptitle(f"Negative lag signal indicates the ambient seismic noise contribution coming from the {direction_labels[j].split('-')[0]}, and positive lag signal indicates the ambient seismic noise contribution coming from the {direction_labels[j].split('-')[1]}.\nNumber of cross-correlograms = {len(df2)}; percentile(95) of negative lag SNRs = %.2f; percentile(95) of positive lag SNRs = %.2f.\n{moveout_text}" %(df2['snr_acausal_corr'].quantile(0.95),df2['snr_causal_corr'].quantile(0.95)),x=0.01,y=0.98, ha='left')
            plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.3, hspace=0.3)
            #Subplot 1: Stacked cross-correlation
            ax1=plt.subplot2grid((50, 51), (0, 0),rowspan=50, colspan=30)
            amplitude_size = (df2['dist'].max()-df2['dist'].min())/seismogram_amp_factor
            for k in range(nod):
                amplitude = np.divide(df2['data'][k], np.max(df2['data'][k]))
                amplitude = np.multiply(amplitude, amplitude_size)
                amplitude = np.add(amplitude, df2['dist'][k])
                ax1=plt.plot(time,amplitude,linewidth=seismogram_line_width, color='k')

            ax1=plt.yticks(range(0,10000,dist_ticks))
            if len(df2) > 1:
                ax1=plt.ylim([df2['dist'].min()-amplitude_size*1.2, df2['dist'].max()+amplitude_size*1.2])
                for moveout in moveouts:
                    x1 = [-df2['dist'].min()/moveout, -df2['dist'].max()/moveout]
                    x2 = [df2['dist'].min()/moveout, df2['dist'].max()/moveout]
                    y = [df2['dist'].min(), df2['dist'].max()]
                    ax1=plt.plot(x1,y,linewidth=2, linestyle='--', dashes=(10, 5), color=(255/255, 102/255, 0,1))
                    ax1=plt.plot(x2,y,linewidth=2, linestyle='--', dashes=(10, 5), color=(255/255, 102/255, 0,1))

            ax1=plt.gca().invert_yaxis()
            ax1=plt.margins(x=0.01, y=0.01)
            ax1=plt.xlabel('Correlation lag (sec)')
            ax1=plt.ylabel('Inter-station distance (km)')
            ax1=plt.title(f'Stacked cross-correlations for stations along {directions[j]}')
            
            #Subplot 2: SNR histogram
            ax2=plt.subplot2grid((50, 51), (30, 32),rowspan=20, colspan=19)
            ax2=plt.hist(df2['snr_causal_corr'], color=(0,1,0,0.5), bins='auto', edgecolor='k', label='Positive lag SNR')
            ax2=plt.hist(df2['snr_acausal_corr'], color=(1,0,0,0.5), bins='auto', edgecolor='k', label='Negative lag SNR')
            ax2=plt.xlabel('SNR')
            ax2=plt.ylabel('Number')
            ax2=plt.legend()

            #Subplot 3: Angle coverage
            ax3=plt.subplot2grid((50, 51), (0, 32),rowspan=20, colspan=20, projection='polar')
            ax3.set_theta_zero_location("N")
            ax3.set_theta_direction(-1)
            plt.yticks([], [])
            bars=ax3.bar(np.deg2rad(angle_centres[j]), [1,1], bottom=0,width=np.deg2rad(45))
            bars[0].set_color((0,1,0,0.5))
            bars[1].set_color((1,0,0,0.5))
            ax3=plt.title('Backazimuth coverage', y=title_y*0.7)

            plt.savefig(pdf,dpi=figure_dpi)
            plt.close()

        #Plot set 2: Fan diagrams

        #Fan diagram calculations
        angle_bins = get_angle_bins(angle_bin_size)
        angle_centres = range(0,360,angle_bin_size)
        nbins = len(angle_bins)
        snrc_baz_group = [ [] for i in range(nbins) ]
        snrc_faz_group = [ [] for i in range(nbins) ]

        for i in range(len(df)):
            if df['baz'][i] >= angle_bins[0][0] or df['baz'][i] < angle_bins[0][1]:
                snrc_baz_group[0].append(df['snr_causal_corr'][i])
            else:
                for j in range(1, nbins):
                    if angle_bins[j][0] <= df['baz'][i] < angle_bins[j][1]:
                        snrc_baz_group[j].append(df['snr_causal_corr'][i])

            if df['faz'][i] >= angle_bins[0][0] or df['faz'][i] < angle_bins[0][1]:
                snrc_faz_group[0].append(df['snr_causal_corr'][i])
            else:
                for j in range(1, nbins):
                    if angle_bins[j][0] <= df['faz'][i] < angle_bins[j][1]:
                        snrc_faz_group[j].append(df['snr_causal_corr'][i])

        snrc_baz_group_mean = [] #mean of (corrected) snr values for each baz snrc group; -999 if len(snrc_baz_group[i]) == 0
        isbar_baz = [] #1 if average snr value is available for the angle bin, and 0 if not!
        isbar_faz = [] #1 if average snr value is available for the angle bin, and 0 if not!
        for i in range(nbins):
            if len(snrc_baz_group[i]):
                snrc_baz_group_mean.append(np.mean(snrc_baz_group[i]))
                isbar_baz.append(1)
            else:
                snrc_baz_group_mean.append(-999)
                isbar_baz.append(0)


        #fan diagram plotting
        angle_centres=np.deg2rad(angle_centres)
        pdf=os.path.join(dirname,f'fan-diagram.pdf')
        png=os.path.join(dirname,f'fan-diagram.png')
        sns.set_context(sns_context)
        f= plt.figure(figsize=(figure_size*0.9,figure_size))
        f.suptitle(f"High SNR bars in the fan digram show the direction of noise sources.\nAverage longitude: %.4f, average latitude: %.4f" %(df['lon1'].mean(), df['lat1'].mean()),x=0.01,y=0.98, ha='left')
        ax1=plt.subplot2grid((50,50), (0, 3),rowspan=48, colspan=46, projection='polar')
        ax1.set_theta_zero_location("N")
        ax1.set_theta_direction(-1)
        ax1.set_xticks(np.deg2rad([0,90,180,270]))
        plt.yticks([], [])
        plt.margins(0)

        bars=ax1.bar(angle_centres, isbar_baz, bottom=0,width=np.deg2rad(angle_bin_size))

        dat = open(os.path.join(dirname,f'fan-diagram-stats.dat'), 'w')
        dat.write("baz(deg) #EGFs min_snr max_snr avg_snr\n")

        i=0
        for bar in bars:
            if isbar_baz[i]:
                dat.write(f"%03.0f-%03.0f %4d %7.2f %7.2f %7.2f\n" %(angle_bins[i][0], angle_bins[i][1], len(snrc_baz_group[i]), np.min(snrc_baz_group[i]), np.max(snrc_baz_group[i]), np.mean(snrc_baz_group[i])))
            bar.set_color(get_snr_rgba(snrc_baz_group_mean[i], np.max(snrc_baz_group_mean)))
            bar.set_edgecolor((0,0,0,bar_edge_alpha))
            i += 1

        dat.close()

        ax1=plt.title('Fan diagram (backazimuths)', y=title_y*0.4)
        ax2=plt.subplot2grid((50,50), (34, 0),rowspan=15, colspan=1)
        cmap = mpl.cm.jet
        norm = mpl.colors.Normalize(vmin=0, vmax=np.max(snrc_baz_group_mean))

        ax2 = mpl.colorbar.ColorbarBase(ax2, cmap=cmap, norm=norm, orientation='vertical')
        ax2=plt.xlabel('SNR (corrected)')

        plt.savefig(pdf,dpi=figure_dpi, transparent=True)
        plt.close()

        #fan diagram png plot
        sns.set_style('ticks')
        sns.set_context(sns_context)
        f= plt.figure(figsize=(figure_size, figure_size))
        ax1=plt.subplot2grid((10,10), (0, 0),rowspan=10, colspan=10, projection='polar')
        ax1.set_theta_zero_location("N")
        ax1.set_theta_direction(-1)
        plt.xticks([], [])
        plt.yticks([], [])
        ax1.set_ylim(0,1)

        bars=ax1.bar(angle_centres, isbar_baz, bottom=0,width=np.deg2rad(angle_bin_size))
        i=0
        for bar in bars:
            bar.set_color(get_snr_rgba(snrc_baz_group_mean[i], max_snr))
            i += 1

        ax1.spines['polar'].set_visible(False)
        plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
        plt.savefig(png, format='png' ,dpi=figure_dpi, transparent=True)
        plt.close()

        # boxplot
        sns.set_context(sns_context)
        sns.set_style("ticks")
        f = plt.figure(figsize=(figure_size,figure_size))
        pdf=os.path.join(dirname,f'./baz-boxplot.pdf')
        ax=plt.subplot2grid((10,10), (0, 0),rowspan=10, colspan=10)
        sns.boxplot(x='baz_direction',y='snr_causal_corr',data=dataset.sort_values(by='baz'), palette=direction_color)
        plt.xlabel('Backazimuth directions')
        plt.ylabel('Causal SNR (corrected)')
        plt.savefig(pdf,dpi=figure_dpi)
        plt.close()


    # plot scale bar
    scale = os.path.join(analysis_dir,'SCALE.pdf')
    sns.set_context(sns_context)
    f= plt.figure(figsize=(figure_size, 0.15*figure_size))
    ax=plt.subplot2grid((2,10), (0, 0),rowspan=1, colspan=10)
    cmap = mpl.cm.jet
    norm = mpl.colors.Normalize(vmin=0, vmax=max_snr)
    ax = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='horizontal')
    plt.savefig(scale,format='pdf',dpi=figure_dpi)
    plt.close()


print("\nDone!\n")







