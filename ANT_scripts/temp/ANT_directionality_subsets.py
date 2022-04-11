#!/usr/bin/python
about = "This script performs the directionality analysis in ambient-noise-tomography for clusters of stations.\n\n Note that one should run this script only when pickle dataset is available.\n"
usage = '''
  USAGE:
    python ANT_directionality_subsets.py <pickle file> <Subset 1> ... <Subset n>

#Notes: <Subset> files should have only 1 column:
         1) station name
'''
# Coded by: omid.bagherpur@gmail.com
# UPDATE: 4 April 2020
#=====Adjustable Parameters======#
angle_bin_size = 10 #must be in [5,10,15,20,30,45,60,90,180]; for region-based analysis, 45 is hardwired
fan_diagram_azim = True #False or True; if true, bars will be plotted along azimuths rather than backazimuths

#plot parameters
figure_dpi = 300
figure_size = 10 #a float
dist_ticks = 100 #yaxis ticks in stacked seismogram plots; an integer
seismogram_line_width = 0.01 #a float
seismogram_time_limit = 800 #an integer 
seismogram_amplitude_factor = 30 #a float; a larger number results in smaller amplitudes
moveouts = [2.5,3.5] #a list of moveouts to be plotted; empty list to disable this option
title_y = -0.3 #title y location (negative float)
bar_edge_alpha = 0 #a float between 0 and 1
max_snr = 40 #'auto' or an integer; max SNR value for all fan-diagrams
#================================#
import os, sys
os.system('clear')
print(about)

if len(sys.argv) < 3:
    print(f"Error USAGE!\n{usage}")
    exit()
elif os.path.isfile(sys.argv[1]) == 0:
    print(f"Error! Pickle data does not exist: '{sys.argv[1]}'\n{usage}")
    exit()

sta_grps = []
if len(sys.argv) > 2:
    for i in range(2, len(sys.argv)):
        grp = []
        if os.path.isfile(sys.argv[i]) == 0:
            print(f"Error! <Group {i-1}> does not exist: '{sys.argv[i]}\n{usage}'")
            exit()

        with open(sys.argv[i], 'r') as fn:
            for line in fn:
                grp.append(line.split()[0])

        sta_grps.append(grp)

ngrps = len(sta_grps)
pickleData = os.path.abspath(sys.argv[1])

if angle_bin_size not in [5,10,15,20,30,45,60,90,180]:
    print("Error! angle_bin_size parameter is not set correctly. Check the 'Adjustable Parameters' section.\n\n")
    exit()

#import required modules:
try:
    import numpy as np
    import pandas as pd
    import seaborn as sns
    import obspy, subprocess, shutil, math
    import matplotlib.pyplot as plt
    import matplotlib as mpl
except Exception as e:
    print(f'Error!\n {e}\n')
    exit()

print(" Reading pickle dataset\n")

############Classes and Functions###########
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

##########################################

try:
    dataset = pd.read_pickle(pickleData)
    stations = dataset['sta1'].unique()
except Exception as e:
    print(f'Error reading pickle data!\n\n{e}\n\n')
    exit()

#check availability of all stations
for i in range(ngrps):
    for sta in sta_grps[i]:
        if sta not in stations:
            print(f"Eror!\nCould not find station: '{sta}' from group: '{sys.argv[i+2]}' in dataset!")
            exit()

default_dataset_name = pickleData.split('/')[-1].split('.')[0:-1][0]
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

#########################
# Starting the analysis #
#########################

dirname = os.path.abspath(f"./{pickleData.split('/')[-1].split('.')[0:-1][0]}_subsets")
nop = 7 #number of plots, used only for printing progress

if os.path.isdir(dirname):
    shutil.rmtree(dirname)
    os.mkdir(dirname)
else:
    os.mkdir(dirname)

#direction plot
directions = ['S-N','SW-NE','W-E','NW-SE']
direction_labels = ['south-north','southwest-northeast','west-east','northwest-southeast']
reverse_condition = [157.5, 202.5, 247.5, 292.5]

for i in range(ngrps):
    print(f" Generating plots for subset {i+1} of {ngrps}\n")
    #building sta_grps[i] dataframes
    df = pd.DataFrame()
    for sta in sta_grps[i]:
        df = pd.concat([df, dataset[dataset.sta1 == sta] ], axis=0, ignore_index=True)
    
    df.sort_values(by='sta1', ascending=True,inplace=True)
    df.reset_index(inplace=True)

    dirname2 = os.path.join(dirname, "%s" %(sys.argv[i+2].split('/')[-1].split('.')[0]))
    os.mkdir(dirname2)
    readme = open(os.path.join(dirname2,'readme.txt'), 'w')
    readme.write(f"Average longitude and latitude:\n%.4f %.4f\n\nSNR (corrected) statistics:\n min=%.2f\n max=%.2f\n average=%.2f\n percentile(95)=%.2f\n\nStations in this group (#stations=%d):\n" %(df.lon1.mean(), df.lat1.mean(), df.snr_corrected.min(),df.snr_corrected.max(), df.snr_corrected.mean(), df.snr_corrected.quantile(0.95), len(sta_grps[i])))
    for sta in sta_grps[i]:
        readme.write(f"{sta}\n")

    readme.close()
    angle_centres = [[0,180],[45, 225],[90, 270],[135, 315]]

    #Plot set 1: S-N, SW-NE, W-E, NW-SE
    for j in range(len(directions)):
        nod = len(df[df.direction == directions[j]])#number of rows in the selected dataset
        df2 = df[df.direction == directions[j]].sort_values(by='dist', ascending=True).reset_index()
        timeseries = []
        asnr=[]
        snr=[]
        for k in range(nod):
            if df2.baz[k] < reverse_condition[j]:
                timeseries.append(df2.data[k][::-1])
                asnr.append(df2.snr[k])
                snr.append(df2.asnr[k])
            else:
                timeseries.append(df2.data[k])
                asnr.append(df2.asnr[k])
                snr.append(df2.snr[k])

        df2['data'] = timeseries
        df2['asnr'] = asnr
        df2['snr'] = snr

        #start plotting
        sns.set_style("white") #seaborn style
        moveout_text = ''
        if len(moveouts):
            moveout_text = 'Moveouts (dashed orange lines) are plotted for %s km/s.' %(' '.join(str(moveouts)).replace('[','').replace(']','').replace(',',' and'))

        f=plt.figure(figsize=(figure_size*2,figure_size))
        pdf = os.path.join(dirname2, f'{directions[j]}.pdf')
        f.suptitle(f"Negative lag signal indicates the ambient seismic noise contribution coming from the {direction_labels[j].split('-')[0]}, and positive lag signal indicates the ambient seismic noise contribution coming from the {direction_labels[j].split('-')[1]}.\nNumber of cross-correlograms = {len(df2)}; percentile(95) of negative lag SNRs = %.2f; percentile(95) of positive lag SNRs = %.2f.\n{moveout_text}" %(df2['asnr'].quantile(0.95),df2['snr'].quantile(0.95)),x=0.01,y=0.98, ha='left')
        plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.3, hspace=0.3)
        #Subplot 1: Stacked cross-correlation
        ax1=plt.subplot2grid((50, 51), (0, 0),rowspan=50, colspan=30)
        amplitude_size = (df2['dist'].max()-df2['dist'].min())/seismogram_amplitude_factor
        for k in range(nod):
            amplitude = np.divide(df2['data'][k][t1:t2], np.max(df2['data'][k][t1:t2]))
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
        ax2=plt.hist(df2['snr'], color=(0,1,0,0.5), bins='auto', edgecolor='k', label='Positive lag SNR')
        ax2=plt.hist(df2['asnr'], color=(1,0,0,0.5), bins='auto', edgecolor='k', label='Negative lag SNR')
        ax2=plt.xlabel('SNR')
        ax2=plt.ylabel('Number')
        ax2=plt.legend()

        #Subplot 3: Angle coverage
        ax3=plt.subplot2grid((50, 51), (0, 32),rowspan=20, colspan=20, projection='polar')
        ax3.set_theta_zero_location("N")
        ax3.set_theta_direction(-1)
        ax3.set_yticks([], [])
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

    #fan diagram plotting
    angle_centres=np.deg2rad(angle_centres)
    pdf=os.path.join(dirname2,f'fan-diagram.pdf')
    png=os.path.join(dirname2,f'fan-diagram.png')
    sns.reset_orig()
    f= plt.figure(figsize=(figure_size*0.9,figure_size))
    if fan_diagram_azim:
        f.suptitle(f"High SNR bars in the fan digram show the direction of noise sources.\nAverage longitude={df['lon1'].mean()}, average latitude: {df['lat1'].mean()}",x=0.01,y=0.98, ha='left')
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

            if max_snr == 'auto':
                bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], np.max(snrc_faz_group_mean)))
            else:
                bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], max_snr))

            bar.set_edgecolor((0,0,0,bar_edge_alpha))
            i += 1
        ax1=plt.title('Fan diagram (azimuths)', y=title_y*0.4)
    else:
        bars=ax1.bar(angle_centres, isbar_baz, bottom=0,width=np.deg2rad(angle_bin_size))
        i=0
        for bar in bars:

            if max_snr == 'auto':
                bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], np.max(snrc_faz_group_mean)))
            else:
                bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], max_snr))

            bar.set_edgecolor((0,0,0,0.1))
            i += 1
        ax1=plt.title('Fan diagram (backazimuths)', y=title_y*0.4)

    ax2=plt.subplot2grid((50,50), (34, 0),rowspan=15, colspan=1)
    cmap = mpl.cm.jet
    if max_snr == 'auto':
        norm = mpl.colors.Normalize(vmin=0, vmax=np.max(snrc_baz_group_mean))
    else:
        norm = mpl.colors.Normalize(vmin=0, vmax=max_snr)

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
            
            if max_snr == 'auto':
                bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], np.max(snrc_faz_group_mean)))
            else:
                bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], max_snr))

            i += 1
    else:
        bars=ax1.bar(angle_centres, isbar_baz, bottom=0,width=np.deg2rad(angle_bin_size))
        i=0
        for bar in bars:
            
            if max_snr == 'auto':
                bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], np.max(snrc_faz_group_mean)))
            else:
                bar.set_color(get_snr_rgba(snrc_faz_group_mean[i], max_snr))

            i += 1

    plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    #plt.margins(x=0, y=0, tight=False)
    #plt.tight_layout()
    plt.savefig(png, format='png' ,dpi=figure_dpi, transparent=True)
    plt.close()

print(f"\nDone!\n\n")
