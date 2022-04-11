#!/usr/bin/python
about = "This script performs the directionality analysis in ambient-noise-tomography.\n"
usage = '''
#Step 1: Generate pickle dataset

  USAGE:
    python ANT_directionality.py <sta loc> <pairs & xcorrs> <CF1> <CF2>

#Step 2: Directionality analysis

  USAGE:
    python ANT_directionality.py <pickle file>

#Notes: <CF1> and <CF2> are optional float numbers, and they are
       the band pass corner frequencies to be applied before the analysis.

        <sta loc> must have 4 columns:
                  1) Network code  2) Station name
                  3) Longitude     4) Latitude
       
        <pairs & xcorrs> must have 3 columns:
                  1) Station 1     2) Station 2
                  3) Stacked cross-correlation SAC file
'''
# Note, if you run the code using the USAGE 1, the code will generate directionality.pkl file that you can later use as the input in the USAGE 2.
# Coded by: omid.bagherpur@gmail.com
# UPDATE: 11 Oct 2020
#=====Adjustable Parameters======#
SAC= "/usr/local/sac/bin/sac" #path to SAC software
default_pickle_name = 'test' #output pickle dataset file name
angle_bin_size = 10 #must be in [5,10,15,20,30,45,60,90,180]; for region-based analysis, 45 is hardwired
station_based_analysis = True #True or False; If True, station-based analysis will also be done in the USAGE 2
fan_diagram_azim = True #False or True; if true, bars will be plotted along azimuths rather than backazimuths (I recommend True!)

#plot parameters
figure_dpi = 300
figure_size = 10 #a float
dist_ticks = 100 #yaxis ticks in stacked seismogram plots; an integer
seismogram_line_width = 0.5 #a float
seismogram_time_limit = 800 #an integer 
seismogram_amplitude_factor = 30 #a float; a larger number results in smaller amplitudes
moveouts = [2.5,3.5] #a list of moveouts to be plotted; empty list to disable this option
title_y = -0.3 #title y location (negative float)
bar_edge_alpha = 0 #a float between 0 and 1
max_snr_png = 100 #max SNR value for png fan-diagrams
#================================#
import os, sys
os.system('clear')
print(about)

if len(sys.argv) != 2 and len(sys.argv) != 3 and len(sys.argv) != 5:
    print(f"Error USAGE!\n{usage}")
    exit()
elif len(sys.argv) != 2 and os.path.isfile(sys.argv[1]) == 0:
    print(f"Error! {sys.argv[1]} does not exist!\n{usage}")
    exit()
elif len(sys.argv) != 2 and os.path.isfile(sys.argv[2]) == 0:
    print(f"Error! {sys.argv[2]} does not exist!\n{usage}")
    exit()

if angle_bin_size not in [5,10,15,20,30,45,60,90,180]:
    print("Error! angle_bin_size parameter is not set correctly. Check the 'Adjustable Parameters' section.\n\n")
    exit()

bpFlag = False
if len(sys.argv) == 5:
    cf1 = float(sys.argv[3])
    cf2 = float(sys.argv[4])
    bpFlag = True

pickleFlag = False
if len(sys.argv) == 2:
    pickleFlag = True
    pickleData = os.path.abspath(sys.argv[1])
    if os.path.isfile(pickleData) == False:
        print(f'Error! Could not find <pickle file>!\n Run the code using USAGE 1 to create one!\n{usage}')
        exit()
    

#import required modules:
try:
    import numpy as np
    import pandas as pd
    import seaborn as sns
    import obspy, subprocess, shutil, math
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    from geographiclib.geodesic import Geodesic
except Exception as e:
    print(f'Error!\n {e}\n')
    exit()

############Classes and Functions###########
class StationPair: #sac file processing class
    def __init__(self,lon1,lat1,lon2,lat2):
        self.lon1 = float(lon1)
        self.lat1 = float(lat1)
        self.lon2 = float(lon2)
        self.lat2 = float(lat2)
    
    def faz(self): #back azimuth
        faz = Geodesic.WGS84.Inverse(self.lat1,self.lon1,self.lat2,self.lon2)['azi1']-180
        if faz<0:
            faz=faz+360
        
        return faz

    def baz(self): #back azimuth
        baz = Geodesic.WGS84.Inverse(self.lat1,self.lon1,self.lat2,self.lon2)['azi1']
        if baz<0:
            baz=baz+360
        
        return baz

    def dist(self): #length of inter-station path in km
        dist=Geodesic.WGS84.Inverse(self.lat1,self.lon1,self.lat2,self.lon2)['s12']
        return dist/1000

class SAC_file: #sac file processing class
    def __init__(self, sacfile):
        self.sacfile = os.path.abspath(sacfile)

    def acausal_causal(self, acausal, causal): 
        #outputs: acausal(reversed) and causal sac files (0-86400 s)
        tempsac = os.path.abspath('./temp.sac')
        shell_cmd=["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
        shell_cmd.append(f"r {self.sacfile}")
        shell_cmd.append(f"reverse")
        shell_cmd.append(f"w {tempsac}")
        shell_cmd.append(f"cut 0 86400")
        shell_cmd.append(f"r {self.sacfile}")
        shell_cmd.append(f"w {causal}")
        shell_cmd.append(f"r {tempsac}")
        shell_cmd.append(f"w {acausal}")
        shell_cmd.append(f"q")
        shell_cmd.append('EOF')
        shell_cmd = '\n'.join(shell_cmd)
        subprocess.call(shell_cmd,shell=True)
        os.remove(tempsac)

    def reverse(self, reversedSac): 
        #outputs: reveresed sac file
        reversedSac = os.path.abspath(reversedSac)
        shell_cmd=["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
        shell_cmd.append(f"r {self.sacfile}")
        shell_cmd.append(f"reverse")
        shell_cmd.append(f"w {reversedSac}")
        shell_cmd.append(f"q")
        shell_cmd.append('EOF')
        shell_cmd = '\n'.join(shell_cmd)
        subprocess.call(shell_cmd,shell=True)

    def data(self):
        #outputs a list of depndent variable values
        st=obspy.read(f'{self.sacfile}', headonly=False)
        return st[0].data

    def nstack(self):
        #outputs a list of depndent variable values
        st=obspy.read(f'{self.sacfile}', headonly=False)
        kevnm = str(st[0].stats.sac.kevnm)
        return int(kevnm)

    def bpf(self, outbpf, cf1, cf2):
        #outputs bandpass filtered sacfile with corner frequencies of cf1 and cf2 
        shell_cmd=["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
        shell_cmd.append(f"r {self.sacfile}")
        shell_cmd.append(f"bp co {cf1} {cf2} n 3 p 2")
        shell_cmd.append(f"w {outbpf}")
        shell_cmd.append(f"q")
        shell_cmd.append('EOF')
        shell_cmd = '\n'.join(shell_cmd)
        subprocess.call(shell_cmd,shell=True)


    def snr(self,dist):
        #Assuming the input xcorr is only either causal or (reversed) acausal part (0-86400),
        #Outputs: the time domain SNR
        #see Tian and Ritzwoller (2015,GJI) for more info about SNR calculation method
        tempsac = os.path.abspath('./temp.sac')
        maxtime = int(dist/3) #depmax approximate time (move out is assumed 3 km/s)
        shell_cmd=["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
        shell_cmd.append(f"r {self.sacfile}")
        shell_cmd.append(f"w {tempsac}")
        shell_cmd.append(f"r {tempsac}")
        shell_cmd.append(f"mtw {maxtime+500} {maxtime+1000}")
        shell_cmd.append(f"rms to user4")
        shell_cmd.append(f"wh")
        shell_cmd.append(f"q")
        shell_cmd.append('EOF')
        shell_cmd = '\n'.join(shell_cmd)
        subprocess.call(shell_cmd,shell=True)
        st=obspy.read(f'{tempsac}', headonly=True)
        rms = float(st[0].stats.sac.user4)
        depmax = float(st[0].stats.sac.depmax)
        snr = depmax/rms
        os.remove(tempsac)
        return snr

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

def get_direction(azimuth):
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
##########################################

if pickleFlag == False:
    #Read data:
    with open(sys.argv[1],'r') as fn:
        stalon={}; stalat={};
        for line in fn:
            if len(line.split()) == 4:
                stalon[f'{line.split()[1]}'] = float(line.split()[2])
                stalat[f'{line.split()[1]}'] = float(line.split()[3])
            else:
                print(f"Error in <sta loc> file format!\n{usage}")
                exit()
    
    with open(sys.argv[2],'r') as fn:
        sacfiles=[]
        stapairs=[]
        for line in fn:
            if len(line.split()) == 3:
                sta1 = line.split()[0]
                sta2 = line.split()[1]
                sacfiles.append(os.path.abspath(line.split()[2]))
            else:
                print(f"Error in <pairs & xcorr> file format!\n{usage}")
                exit()
    
            if os.path.isfile(sacfiles[-1]) == 0:
                print(f'Error finding sac file: {sacfiles[-1]}\n')
                exit()
    
            if (sta1 in stalon) and (sta2 in stalon):
                stapairs.append([f'{sta1}', f'{sta2}'])
            else:
                print(f'Error! Station location for [{sta1}, {sta2}] was not found.\n')
                exit()
    
    #store parameters for each stacked xcorr in lists
    sta1 = [] #station 1 (master station in the xcorr)
    sta2 = [] #station 2
    lon1 = [] #station 1 longitude
    lat1 = [] #station 1 latitude
    lon2 = [] #station 2 longitude
    lat2 = [] #station 2 latitude
    faz = [] #forward azimuths from sta1 to sta2
    baz = [] #back azimuths from sta1 to sta2
    direction = [] #direction label (N, S , W, ...)
    dist = [] #inter-station distance in km
    nstack = [] #number of stacked days; read from KEVNM sac header
    snr = [] #SNR of the outgoing signal (causal)
    snr_corrected = [] #SNR of causal signal corrected for geometrical spreading factor + number of stacking days
    asnr = [] #SNR of the outgoing signal (acausal)
    asnr_corrected = [] #SNR of acausal signal corrected for geometrical spreading factor + number of stacking days
    data = [] #waveform data from -86400 s to 86400 s
    
    for i in range(len(sacfiles)):
        print(f"  Collecting dataset progress: {int(((i+1)/len(sacfiles))*100)}", end = '% \r')
        #step 1: original signal
        sta1.append(stapairs[i][0])
        sta2.append(stapairs[i][1])
        sta1_lon = stalon[f'{stapairs[i][0]}']
        sta1_lat = stalat[f'{stapairs[i][0]}']
        sta2_lon = stalon[f'{stapairs[i][1]}']
        sta2_lat = stalat[f'{stapairs[i][1]}']
        lon1.append(sta1_lon)
        lat1.append(sta1_lat)
        lon2.append(sta2_lon)
        lat2.append(sta2_lat)
        sta1sta2 = StationPair(sta1_lon,sta1_lat,sta2_lon,sta2_lat)
        faz.append(sta1sta2.faz())
        baz.append(sta1sta2.baz())
        direction.append(get_direction(baz[-1]))
        dist.append(sta1sta2.dist())
        sf = SAC_file(sacfiles[i])
        nstack.append(sf.nstack())
        bpsac = os.path.abspath('./bp.sac')
        if bpFlag:
            sf.bpf(bpsac, cf1, cf2)
            sf = SAC_file(bpsac)
        
        data.append(sf.data())
        acausal = os.path.abspath('./acausal.sac')
        causal = os.path.abspath('./causal.sac')
        sf.acausal_causal(acausal,causal)
        causalSac = SAC_file(causal)
        acausalSac = SAC_file(acausal)
        snr.append(causalSac.snr(dist[-1]))
        asnr.append(acausalSac.snr(dist[-1]))
    
        #step 2: reveresed signal
        sta1.append(stapairs[i][1])
        sta2.append(stapairs[i][0])
        lon1.append(sta2_lon)
        lat1.append(sta2_lat)
        lon2.append(sta1_lon)
        lat2.append(sta1_lat)
        sta1sta2 = StationPair(sta2_lon,sta2_lat,sta1_lon,sta1_lat)
        faz.append(float(sta1sta2.faz()))
        baz.append(float(sta1sta2.baz()))
        direction.append(get_direction(baz[-1]))
        dist.append(float(sta1sta2.dist()))
        reversedSac = os.path.abspath('./reversed.sac')
        sf.reverse(reversedSac)
        sf = SAC_file(reversedSac)
        nstack.append(sf.nstack())
        data.append(sf.data())
        sf.acausal_causal(acausal,causal)
        causalSac = SAC_file(causal)
        acausalSac = SAC_file(acausal)
        snr.append(causalSac.snr(dist[-1]))
        asnr.append(acausalSac.snr(dist[-1]))
        os.remove(acausal)
        os.remove(causal)
        os.remove(reversedSac)
        if os.path.isfile(bpsac):
            os.remove(bpsac)
    
    #calculate corrected snr
    for i in range(len(baz)):
        snr_corrected.append(snr[i]*math.sqrt(dist[i])/math.sqrt(np.min(dist))*math.sqrt(np.mean(nstack))/math.sqrt(nstack[i]))
        asnr_corrected.append(asnr[i]*math.sqrt(dist[i])/math.sqrt(np.min(dist))*math.sqrt(np.mean(nstack))/math.sqrt(nstack[i]))

    print(f"  Collecting dataset progress: 100%")

    print(f"  Saving pickle dataset ... ", end='      \r')
    #create pandas dataframe 
    dataset = {'sta1':sta1, 'sta2':sta2, 'lon1':lon1, 'lat1':lat1, 'lon2':lon2, 'lat2':lat2, 'dist':dist, 'baz':baz, 'faz':faz, 'direction':direction, 'snr':snr, 'snr_corrected':snr_corrected, 'asnr':asnr, 'asnr_corrected':asnr_corrected, 'data':data}
    dataset = pd.DataFrame(dataset)
    pickleData = os.path.abspath(f'./{default_pickle_name}.pkl')
    dataset.to_pickle(pickleData)
    print(f"  Saving pickle dataset ...... Done.\n\n A pickle dataset has been generated in:\n {pickleData}\n\n")
    
    exit()
else:
    try:
        dataset = pd.read_pickle(pickleData)
        stations = dataset['sta1'].unique()
    except Exception as e:
        print(f'Error reading pickle data!\n\n{e}\n\n')
        exit()

sns.set() #initiate seaborn styling

default_pickle_name = pickleData.split('/')[-1].split('.')[0:-1][0]
#save a different version of dataset excluding the reveresed data (every two rows)
mask = []
for i in range(len(dataset)):
    if i in range(0,len(dataset),2):
        mask.append(True)
    else:
        mask.append(False)

dataset2 = dataset[mask].reset_index()

#find time index in the data for the specified 'seismogram_time_limit' parameter
tsLen = len(dataset['data'][0]) #for daily chunks: 8600*2+1
if tsLen != 172801:
    print('Error! Stacked cross correlations should be from -86400 to +86400 sec (fs=1Hz)!\n\n')
    exit()

t1 = int(86400 - seismogram_time_limit)
t2 = t1+2*seismogram_time_limit+1
time = range(-seismogram_time_limit, seismogram_time_limit+1)
########################################
# Region-based directionality analysis #
########################################

dirname = os.path.abspath(f'{default_pickle_name}-region')
nop = 7 #number of plots, used only for printing progress

if os.path.isdir(dirname):
    shutil.rmtree(dirname)
    os.mkdir(dirname)
else:
    os.mkdir(dirname)

#collect data for S-N, SW-NE, W-E, NW-SE
angle_bins = get_angle_bins(45)
angle_labels_region = [['S','N'],['SW','NE'],['W','E'],['NW','SE']]
angle_labels_region2 = [['south','north'],['southwest','northeast'],['west','east'],['northwest','southeast']]
angle_centres = [[0,180],[45, 225],[90, 270],[135, 315]]

for i in range(4):
    print(f"  Region-based directionality analysis progress: %3.0f" %(i/nop*100), end='%       \r')
    angle_bins_region = [angle_bins[i][0], angle_bins[i][1], angle_bins[i+4][0], angle_bins[i+4][1]]
    data_selected = []
    baz_selected = []
    dist_selected = []
    snr_selected = []
    asnr_selected = []
    for j in range(len(dataset2)):
        baz = dataset2['baz'][j]
        dist = dataset2['dist'][j]

        if i == 0:

            if baz >= angle_bins_region[0] or baz < angle_bins_region[1]: #needs reversing
                data_selected.append(dataset2['data'][j][::-1])
                baz_selected.append(baz)
                dist_selected.append(dist)
                snr_selected.append(dataset2['asnr_corrected'][j])
                asnr_selected.append(dataset2['snr_corrected'][j])
            elif angle_bins_region[2] <= baz < angle_bins_region[3]: #does not need reversing
                data_selected.append(dataset2['data'][j])
                baz_selected.append(baz)
                dist_selected.append(dist)
                snr_selected.append(dataset2['snr_corrected'][j])
                asnr_selected.append(dataset2['asnr_corrected'][j])

        else:

            if angle_bins_region[0] <= baz < angle_bins_region[1]: #needs reversing
                data_selected.append(dataset2['data'][j][::-1])
                baz_selected.append(baz)
                dist_selected.append(dist)
                snr_selected.append(dataset2['asnr_corrected'][j])
                asnr_selected.append(dataset2['snr_corrected'][j])
            elif angle_bins_region[2] <= baz < angle_bins_region[3]: #does not need reversing
                data_selected.append(dataset2['data'][j])
                baz_selected.append(baz)
                dist_selected.append(dist)
                snr_selected.append(dataset2['snr_corrected'][j])
                asnr_selected.append(dataset2['asnr_corrected'][j])
    
    df = pd.DataFrame({'data':data_selected, 'baz':baz_selected, 'dist':dist_selected, 'snr':snr_selected, 'asnr':asnr_selected}).sort_values(by='dist', ascending=True).reset_index()

    #plot for S-N, SW-NE, W-E, NW-SE
    sns.set_style("white") #seaborn style
    moveout_text = ''
    if len(moveouts):
        moveout_text = 'Moveouts (dashed orange lines) are plotted for %s km/s.' %(' '.join(str(moveouts)).replace('[','').replace(']','').replace(',',' and'))

    f=plt.figure(figsize=(figure_size*2,figure_size))
    pdf = os.path.join(dirname, f'{angle_labels_region[i][0]}-{angle_labels_region[i][1]}.pdf')
    f.suptitle(f"Negative lag signal indicates the ambient seismic noise contribution coming from the {angle_labels_region2[i][0]}, and positive lag signal indicates the ambient seismic noise contribution coming from the {angle_labels_region2[i][1]}.\nNumber of cross-correlograms = {len(df)}; percentile(95) of negative lag SNRs = %.2f; percentile(95) of positive lag SNRs = %.2f.\n{moveout_text}" %(df['asnr'].quantile(0.95),df['snr'].quantile(0.95)),x=0.01,y=0.98, ha='left')
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.3, hspace=0.3)
    #Subplot 1: Stacked cross-correlation
    ax1=plt.subplot2grid((50, 51), (0, 0),rowspan=50, colspan=30)
    amplitude_size = (df['dist'].max()-df['dist'].min())/seismogram_amplitude_factor
    for k in range(len(df)):
        amplitude = np.divide(df['data'][k][t1:t2], np.max(df['data'][k][t1:t2]))
        amplitude = np.multiply(amplitude, amplitude_size)
        amplitude = np.add(amplitude, df['dist'][k])
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
    ax1=plt.title(f'Stacked cross-correlations for stations along {angle_labels_region[i][0]}-{angle_labels_region[i][1]}')
    
    #SNR histogram
    ax2=plt.subplot2grid((50, 51), (30, 32),rowspan=20, colspan=19)
    ax2=plt.hist(df['snr'], color=(0,1,0,0.5), bins='auto', edgecolor='k', label='Positive lag SNR')
    ax2=plt.hist(df['asnr'], color=(1,0,0,0.5), bins='auto', edgecolor='k', label='Negative lag SNR')
    ax2=plt.xlabel('SNR')
    ax2=plt.ylabel('Number')
    ax2=plt.legend()

    #Angle coverage
    ax3=plt.subplot2grid((50, 51), (0, 32),rowspan=20, colspan=20, projection='polar')
    ax3.set_theta_zero_location("N")
    ax3.set_theta_direction(-1)
    ax3.set_yticks([], [])
    bars=ax3.bar(np.deg2rad(angle_centres[i]), [1,1], bottom=0,width=np.deg2rad(45))
    bars[0].set_color((0,1,0,0.5))
    bars[1].set_color((1,0,0,0.5))
    ax3=plt.title('Backazimuth coverage', y=title_y*0.7)


    plt.savefig(pdf,dpi=figure_dpi)
    plt.close()

median_snrc = dataset['snr_corrected'].median()
mean_snrc = dataset['snr_corrected'].mean()
std_snrc = dataset['snr_corrected'].std()

sns.set_style("darkgrid") #seaborn style
pdf=os.path.join(dirname,f'./dataset-histograms.pdf')
f= plt.figure(figsize=(figure_size,figure_size))
f.suptitle(f'SNR (corrected) parameters: Mean=%.2f, Median=%.2f, STD=%.2f,\n percentile(68)=%.2f, percentile(95)=%.2f, percentile(99)=%.2f' %(mean_snrc,median_snrc,std_snrc, dataset['snr_corrected'].quantile(0.68), dataset['snr_corrected'].quantile(0.95), dataset['snr_corrected'].quantile(0.99)),x=0.01,y=0.98, ha='left')
plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.3, hspace=0.3)
ax1=plt.subplot2grid((2, 2), (0, 0),rowspan=1, colspan=2)
ax1=plt.hist(dataset['snr'], alpha = 0.5, bins='auto', edgecolor='k', label='SNR')
ax1=plt.hist(dataset['snr_corrected'], alpha = 0.5, bins='auto', edgecolor='k', label='SNR (corrected)')
ax1=plt.xlabel('SNR')
ax1=plt.ylabel('Number')
ax1=plt.title('Calculated SNR distribution')
ax1=plt.legend()

#inter-station distance histogram
ax2=plt.subplot2grid((2, 2), (1, 0), rowspan=1, colspan=1)
ax2=plt.hist(dataset['dist'], bins='auto', edgecolor='k')
ax2=plt.ylabel('Number')
ax2=plt.title('Inter-station distance', y=title_y*0.7)

#BAZ histogram
degrees=np.asarray(dataset['baz'])
radians=np.asarray(np.deg2rad(dataset['baz']))
a, b=np.histogram(degrees, bins=np.arange(0-angle_bin_size/2, 360+angle_bin_size/2, angle_bin_size))
centres=np.deg2rad(np.ediff1d(b)//2 + b[:-1])
ax3=plt.subplot2grid((2, 2), (1, 1), rowspan=1, colspan=1, projection='polar')
ax3.set_theta_zero_location("N")
ax3.set_theta_direction(-1)
bars=ax3.bar(centres, a, bottom=0,width=np.deg2rad(angle_bin_size), color='blue',edgecolor='k')
for bar in bars:
    bar.set_alpha(0.8)

ax3=plt.title('Backazimuth distribution', y=title_y*0.7)

plt.savefig(pdf,dpi=figure_dpi)
plt.close()


#Fan diagram for the entire dataset
print(f"  Region-based directionality analysis progress: %3.0f" %(4/nop*100), end='%       \r')
#Fan diagram calculations
angle_bins = get_angle_bins(angle_bin_size)
angle_centres = range(0,360,angle_bin_size)
nbins = len(angle_bins)
snrc_baz_group = [ [] for i in range(nbins) ]
snrc_faz_group = [ [] for i in range(nbins) ]

for i in range(len(dataset)):
    if dataset['baz'][i] >= angle_bins[0][0] or dataset['baz'][i] < angle_bins[0][1]:
        snrc_baz_group[0].append(dataset['snr_corrected'][i])
    else:
        for j in range(1, nbins):
            if angle_bins[j][0] <= dataset['baz'][i] < angle_bins[j][1]:
                snrc_baz_group[j].append(dataset['snr_corrected'][i])

    if dataset['faz'][i] >= angle_bins[0][0] or dataset['faz'][i] < angle_bins[0][1]:
        snrc_faz_group[0].append(dataset['snr_corrected'][i])
    else:
        for j in range(1, nbins):
            if angle_bins[j][0] <= dataset['faz'][i] < angle_bins[j][1]:
                snrc_faz_group[j].append(dataset['snr_corrected'][i])

snrc_baz_group_mean = [] #mean of (corrected) snr values for each baz snrc group; -999 if len(snrc_baz_group[i]) == 0
snrc_faz_group_mean = [] #mean of (corrected) snr values for each faz snrc group; -999 if len(snrc_faz_group[i]) == 0
isbar_baz = [] #1 if average snr value is available for the angle bin, and 0 if not!
isbar_faz = [] #1 if average snr value is available for the angle bin, and 0 if not!
for i in range(nbins):
    if len(snrc_baz_group[i]):
        snrc_baz_group_mean.append(np.mean(snrc_baz_group[i]))
        isbar_baz.append(1)
    else:
        snrc_baz_group_mean.append(-999)
        isbar_baz.append(0)

    if len(snrc_faz_group[i]):
        snrc_faz_group_mean.append(np.mean(snrc_faz_group[i]))
        isbar_faz.append(1)
    else:
        snrc_faz_group_mean.append(-999)
        isbar_faz.append(0)

#fan diagram plotting
angle_centres=np.deg2rad(angle_centres)
pdf=os.path.join(dirname,f'fan-diagram.pdf')
png=os.path.join(dirname,f'fan-diagram.png')
sns.reset_orig()
f= plt.figure(figsize=(figure_size*0.9,figure_size))
if fan_diagram_azim:
    f.suptitle(f"High SNR bars in the fan digram show the direction of noise sources.\nAverage longitude={dataset['lon1'].mean()}, average latitude: {dataset['lat1'].mean()}",x=0.01,y=0.98, ha='left')
ax1=plt.subplot2grid((50,50), (0, 3),rowspan=48, colspan=46, projection='polar')
ax1.set_theta_zero_location("N")
ax1.set_theta_direction(-1)
ax1.set_xticks(np.deg2rad([0,90,180,270]))
ax1.set_yticks([], [])
plt.margins(0)

if fan_diagram_azim:
    bars=ax1.bar(angle_centres, isbar_faz, bottom=0,width=np.deg2rad(angle_bin_size))
    i=0
    for bar in bars:
        bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], np.max(snrc_faz_group_mean)))
        bar.set_edgecolor((0,0,0,bar_edge_alpha))
        i += 1
    ax1=plt.title('Fan diagram (azimuths)', y=title_y*0.4)
else:
    bars=ax1.bar(angle_centres, isbar_baz, bottom=0,width=np.deg2rad(angle_bin_size))
    i=0
    for bar in bars:
        bar.set_color(get_snr_rgba(snrc_baz_group_mean[i], np.max(snrc_baz_group_mean)))
        bar.set_edgecolor((0,0,0,0.1))
        i += 1
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
ax1=plt.subplot2grid((10,10), (0, 0),rowspan=10, colspan=10, projection='polar')
ax1.set_theta_zero_location("N")
ax1.set_theta_direction(-1)
ax1.set_xticks([], [])
ax1.set_yticks([], [])
ax1.set_ylim(0,1)

if fan_diagram_azim:
    bars=ax1.bar(angle_centres, isbar_faz, bottom=0,width=np.deg2rad(angle_bin_size))
    i=0
    for bar in bars:
        bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], np.max(snrc_faz_group_mean)))
        i += 1
else:
    bars=ax1.bar(angle_centres, isbar_baz, bottom=0,width=np.deg2rad(angle_bin_size))
    i=0
    for bar in bars:
        bar.set_color(get_snr_rgba(snrc_baz_group_mean[i], np.max(snrc_baz_group_mean)))
        i += 1

plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
#plt.margins(x=0, y=0, tight=False)
#plt.tight_layout()
plt.savefig(png, format='png' ,dpi=figure_dpi, transparent=True)
plt.close()

print(f"  Region-based directionality analysis progress: %3.0f" %(5/nop*100), end='%       \r')
sns.set_style("darkgrid")
f= plt.figure(figsize=(figure_size*0.7,figure_size))
pdf=os.path.join(dirname,f'./faz-regression.pdf')
sns.lmplot(x='faz',y='snr_corrected',data=dataset, hue='direction')
plt.xlim(0, 360)
plt.xticks(range(0,405,45))
plt.xlabel('Azimuth (degrees)')
plt.ylabel('SNR (corrected)')
plt.savefig(pdf,dpi=figure_dpi)
plt.close()

print(f"  Region-based directionality analysis progress: 100%")


if station_based_analysis == False:
    print(f'\nResults are generated in the following path:\n  {dirname}\n')
    exit()


#########################################
# Station-based directionality analysis #
#########################################
sns.set_style("white")
dirname = os.path.abspath(f'./{default_pickle_name}-stations')

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
    dat.write('#station 2, distance (km), backazimuth (deg), corrected SNR (causal)\n')

    f=plt.figure(figsize=(figure_size*1.2,figure_size))
    if fan_diagram_azim:
        fan_diagram_text = 'High SNR bars in the fan digram show the direction of noise sources.'
    else:
        fan_diagram_text = ''

    f.suptitle(f'The causal signal (positive lags) indicate outgoing signal.\nPercentile(95) of negative lag SNRs = %.2f; percentile(95) of positive lag SNRs = %.2f\n{fan_diagram_text}' %(df['asnr'].quantile(0.95),df['snr'].quantile(0.95)),x=0.01,y=0.98, ha='left')
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.3, hspace=0.3)
    #Subplot 1: Stacked cross-correlation
    ax1=plt.subplot2grid((50, 51), (0, 0),rowspan=50, colspan=30)
    amplitude_size = (np.max(df['dist'])-np.min(df['dist']))/seismogram_amplitude_factor
    for i in range(len(df)):
        dat.write(f'%4s %7.2f %6.2f %6.2f\n' %(df['sta2'][i], df['dist'][i], df['baz'][i], df['snr_corrected'][i]))
        amplitude = np.divide(df['data'][i][t1:t2], np.max(df['data'][i][t1:t2]))
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
    snrc_faz_group = [ [] for i in range(nbins) ]

    for i in range(len(df)):
        if df['baz'][i] >= angle_bins[0][0] or df['baz'][i] < angle_bins[0][1]:
            snrc_baz_group[0].append(df['snr_corrected'][i])
        else:
            for j in range(1, nbins):
                if angle_bins[j][0] <= df['baz'][i] < angle_bins[j][1]:
                    snrc_baz_group[j].append(df['snr_corrected'][i])

        if df['faz'][i] >= angle_bins[0][0] or df['faz'][i] < angle_bins[0][1]:
            snrc_faz_group[0].append(df['snr_corrected'][i])
        else:
            for j in range(1, nbins):
                if angle_bins[j][0] <= df['faz'][i] < angle_bins[j][1]:
                    snrc_faz_group[j].append(df['snr_corrected'][i])

    snrc_baz_group_mean = [] #mean of (corrected) snr values for each baz snrc group; -999 if len(snrc_baz_group[i]) == 0
    snrc_faz_group_mean = [] #mean of (corrected) snr values for each faz snrc group; -999 if len(snrc_faz_group[i]) == 0
    isbar_baz = [] #1 if average snr value is available for the angle bin, and 0 if not!
    isbar_faz = [] #1 if average snr value is available for the angle bin, and 0 if not!
    for i in range(nbins):
        if len(snrc_baz_group[i]):
            snrc_baz_group_mean.append(np.mean(snrc_baz_group[i]))
            isbar_baz.append(1)
        else:
            snrc_baz_group_mean.append(-999)
            isbar_baz.append(0)

        if len(snrc_faz_group[i]):
            snrc_faz_group_mean.append(np.mean(snrc_faz_group[i]))
            isbar_faz.append(1)
        else:
            snrc_faz_group_mean.append(-999)
            isbar_faz.append(0)

    #Step 2: fan diagram plotting
    angle_centres=np.deg2rad(angle_centres)
    ax3=plt.subplot2grid((50, 51), (25, 31),rowspan=20, colspan=20, projection='polar')
    ax3.set_theta_zero_location("N")
    ax3.set_theta_direction(-1)
    ax3.set_yticks([], [])

    if fan_diagram_azim:
        bars=ax3.bar(angle_centres, isbar_faz, bottom=0,width=np.deg2rad(angle_bin_size))
        i=0
        for bar in bars:
            bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], np.max(snrc_faz_group_mean)))
            bar.set_edgecolor('k')
            i += 1
        ax3=plt.title('Fan diagram (azimuths)', y=title_y*0.6)
    else:
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
    png = os.path.join(dirname2,f'{station}.png')
    f= plt.figure(figsize=(figure_size, figure_size))
    ax1=plt.subplot2grid((10,10), (0, 0),rowspan=10, colspan=10, projection='polar')
    ax1.set_theta_zero_location("N")
    ax1.set_theta_direction(-1)
    ax1.set_xticks([], [])
    ax1.set_yticks([], [])
    ax1.set_ylim(0,1)

    if fan_diagram_azim:
        bars=ax1.bar(angle_centres, isbar_faz, bottom=0,width=np.deg2rad(angle_bin_size))
        i=0
        for bar in bars:
            bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], max_snr_png))
            i += 1
    else:
        bars=ax1.bar(angle_centres, isbar_baz, bottom=0,width=np.deg2rad(angle_bin_size))
        i=0
        for bar in bars:
            bar.set_color(get_snr_rgba(snrc_baz_group_mean[i], max_snr_png))
            i += 1


    plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    plt.savefig(png, format='png' ,dpi=figure_dpi, transparent=True)
    plt.close()

#Step 4: fan diagram plotting (scale bar)
scale = os.path.join(dirname2,'SCALE.pdf')
f= plt.figure(figsize=(figure_size, 0.15*figure_size))
ax=plt.subplot2grid((2,10), (0, 0),rowspan=1, colspan=10)
cmap = mpl.cm.jet
norm = mpl.colors.Normalize(vmin=0, vmax=max_snr_png)
ax = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='horizontal')
plt.savefig(scale,format='pdf',dpi=figure_dpi)
plt.close()

print(f"  Station-based directionality analysis progress: 100%\n\n")
