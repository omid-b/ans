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
# UPDATE: 12 Oct 2020
# CODED BY: omid.bagherpur@gmail.com
#====Adjustable Parameters====#
SAC = "/usr/local/sac/bin/sac"  # path to SAC software
signal_vel = [2, 4.5] # signal window velocity range (km/s); important in snr calculation

seism_cut = 800 # time limits in the egf plots (s)
figure_size = [16,12] # a list of two numbers; [xSize, ySize]
figure_dpi = 150 # dpi = dot per inch
seismogram_amp_factor = 0.5 # affects the amplitude of EGFs in the EGF plots
seismogram_line_width = 0.5 # seismogram line width (pixels) in the EGF plots
sns_context = "talk" # seaborn context (paper, notebook, poster, talk); affects annotation size
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
except ImportError as e:
    print(f'Import Error!\n{e}\n')
    exit()

#----CLASSES & FUNCTIONS----#

class EGF:
    def __init__(self,sacfile):
        self.sacfile = os.path.abspath(sacfile)
        self.trace = obspy.read(self.sacfile, format='SAC')[0]

    # def name(self):
    #     name = os.path.basename(self.sacfile).split('.sac')[0]
    #     return name

    def sta1(self):
        sta1 = os.path.basename(self.sacfile).split('_')[0]
        return sta1

    def sta2(self):
        sta2 = os.path.basename(self.sacfile).split('_')[1]
        return sta2

    # def chn(self):
    #     chn = os.path.basename(self.sacfile).split('_')[2].split('.')[0]
    #     return chn

    def faz(self): # forward-azimuth
        faz = '%.2f' %(self.trace.stats.sac.az)
        return float(faz)

    def baz(self): # back-azimuth
        baz = '%.2f' %(self.trace.stats.sac.baz)
        return float(baz)

    def direction(self):
        azimuth = float(self.trace.stats.sac.baz)
        if azimuth < 22.5:
            direction = 'S-N'
        elif 337.5 <= azimuth or 157.5 <= azimuth < 202.5:
            direction = 'S-N'
        elif 22.5 <= azimuth < 67.5 or 202.5 <= azimuth < 247.5:
            direction = 'SW-NE'
        elif 67.5 <= azimuth < 112.5 or 247.5 <= azimuth < 292.5:
            direction = 'W-E'
        elif 112.5 <= azimuth < 157.5 or 292.5 <= azimuth < 337.5:
            direction = 'NW-SE'
        return direction

    def dist(self): # inter-station distance (km)
        dist = '%.4f' %(self.trace.stats.sac.dist)
        return float(dist)

    def nstack(self): # number of stacks (store in 'kevnm' header)
        kevnm = self.trace.stats.sac.kevnm
        return int(kevnm)

    def data(self):
        data = np.array(self.trace.data)
        return data

    # def data_reverse(self):
    #     data_reverse = np.array(self.trace.data)[::-1]
    #     return data_reverse

    # def causal_data(self):
    #     data = np.array(self.trace.data)
    #     causal = data[int(len(data)/2):len(data)]
    #     return causal

    # def acausal_data(self):
    #     data = np.array(self.trace.data)[::-1]
    #     acausal = data[int(len(data)/2):len(data)]
    #     return acausal

    def times(self):
        delta = self.trace.stats.sac.delta
        b = self.trace.stats.sac.b
        e = self.trace.stats.sac.e
        times = np.arange(b, e+delta, delta)
        return times

    # def times_causal(self):
    #     delta = self.trace.stats.sac.delta
    #     e = self.trace.stats.sac.e
    #     times_causal = np.arange(0, e+delta, delta)
    #     return times_causal

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

            if times[i] < t1:
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

            if times[i] < t1:
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

            if times[i] < t1:
                noise.append(data[i])

        srms = np.sqrt(np.nanmean(np.square(signal)))
        nrms = np.sqrt(np.nanmean(np.square(noise)))
        snr = 10*np.log10((srms**2)/(nrms**2))
        return float(snr)


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
    if not os.path.isdir(pickle_data):
        print("\nError! Could not find 'pickle_data'.\n")
        exit()
    if not os.path.isfile(analysis_dir):
        print("\nError! 'analysis_dir' will be created by by this script; a file is given!\n")
        exit()
elif len(sys.argv) > 3:
    print('Usage 3: directionality analysis for subsets of stations\n')
    usage3 = True
else:
    print(f'Error usage!\n{usage}')
    exit()

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
    pickle_data = os.path.join(egf_dir.split(f"{os.path.basename(egf_dir)}")[0],\
     f'{os.path.basename(egf_dir)}_directionality.pkl')

    report = "\n\n  Number of EGFs: %d\n  Inter-station distance: %.0f-%.0f km\n  EGF datasets:  %s\n  Output pickle: %s\n\n" %(len(egfs), np.nanmin(dist), np.nanmax(dist), egf_dir, pickle_data)

    print(report)
    uin = input("Do you want to continue generating the pickle file (y/n)? ")
    if uin.lower() != 'y':
        print("\nExit program!\n")
        exit()
    else:
        print("\n")

    sta1 = [] # station A name
    sta2 = [] # station B name
    faz = [] # forward- azimuths
    baz = [] # back-azimuths
    direction = [] # azimuthal groups (S-N, SW-NE, W-E, NW-SE)
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
        faz.append(egf.faz())
        baz.append(egf.baz())
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
        sta1.append(sta2[-1])
        sta2.append(sta1[-1])
        faz.append(baz[-1])
        baz.append(faz[-1])
        direction.append(direction[-1])
        dist.append(dist[-1])
        nstack.append(nstack[-1])
        data.append(data[::-1])
        times.append(times[-1])
        snr_sym.append(snr_sym[-1])
        snr_sym_corr.append(snr_sym_corr[-1])
        snr_causal_corr.append(snr_acausal_corr[-1])
        snr_acausal_corr.append(snr_causal_corr[-1])

    print("\n  Generating pickle file ... ", end='  \r')
    dataset = {'sta1':sta1, 'sta2':sta2, 'faz':faz, 'baz':baz, 'direction':direction, 'dist':dist, 'nstack':nstack, 'data':data, 'times':times, 'snr_sym':snr_sym, 'snr_sym_corr':snr_sym_corr, 'snr_causal_corr':snr_causal_corr, 'snr_acausal_corr':snr_acausal_corr}
    dataset = pd.DataFrame(dataset)
    dataset.to_pickle(pickle_data)
    print("  Generating pickle file ... Done\n")


#====USAGE 2====#
# directionality analysis of the entire dataset
if usage2:
    try:
        dataset = pd.read_pickle(pickle_data)
    except Exception as e:
        print(f"Error reading pickle file!\n{e}\n")
        exit()

print("\n\nDone!\n")







