#!/usr/bin/env python3
import sys
import os
about = "Given the range of inter-station distance, this script calculates\
and plots maximum number of raypaths that will be generated in an \
ambient-noise tomography project.\n"
usage = '''
python3 ANT_design.py <netstaXY> <min dist> <max dist>

 <netsta> is a text file with 4 columns:
    1)network  2)station  3)longitude  4)latitude
 <min dist>: minimum inter-station distance in km
 <max dist>: maximum inter-station distance in km
'''
# coded by omid.bagherpur@gmail.com
# UPDATE: 15 Jan 2020
#====Adjustable Parameters=====#
# plot parameters
mapSize = 8
padding_coe = 0.2  # between 0 and 1; related to map_region for plotting
#==============================#
# Check inputs
os.system('clear')
print(about)

if len(sys.argv) != 4:
    print(f"Error USAGE!\n{usage}")
    exit()

if not os.path.isfile(sys.argv[1]):
    print(f"Error! Could not find <netstaXY>\n{usage}")
    exit()


try:
    mindist = float(sys.argv[2])
    maxdist = float(sys.argv[3])
except Exception as e:
    print(f"Error reading min/max inter-station distance!\n {e}\n{usage}")
    exit()

if mindist > maxdist:
    print(f"Error! <min dist> must be smaller than <max dist>\n{usage}")
    exit()

# read <netstaXY>
net = []
sta = []
lon = []
lat = []
with open(sys.argv[1], 'r') as data:
    for line in data:
        try:
            net.append(line.split()[0])
            sta.append(line.split()[1])
            lon.append(float(line.split()[2]))
            lat.append(float(line.split()[3]))
        except Exception as e:
            print(f"\nError! <netstaXY> format is not correct.\n{e}\n{usage}")
            exit()

uniq_net = []
for x in net:
    if x not in uniq_net:
        uniq_net.append(x)

staLat = {}
staLon = {}
for i in range(len(sta)):
    staLat[sta[i]] = lat[i]
    staLon[sta[i]] = lon[i]

lon_range = [f"%8.3f" % (min(lon)), f"%8.3f" % (max(lon))]
lat_range = [f"%8.3f" % (min(lat)), f"%8.3f" % (max(lat))]

info = f'''
 Number of networks: {len(uniq_net)}
 Number of stations: {len(sta)}
 Longitude range: [{lon_range[0]},  {lon_range[1]}]
 Latitude range:  [{lat_range[0]},  {lat_range[1]}]
 Inter-station distance range (km): [{mindist},  {maxdist}] 
'''
print(info)

# import required modules
# to install basemap:
# pip3 install https://github.com/matplotlib/basemap/archive/master.zip
try:
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.basemap import Basemap
    from geographiclib.geodesic import Geodesic
    from math import degrees, radians, sin, cos, asin, atan, sqrt
except ImportError as e:
    print(f"Error! {e}\n")
    exit()


#===FUNCTIONS===#
def find_uniq_pairs(lst0):
    # INPUT:  a list of strings
    # OUTPUT: a list of sorted and uniq pair list of strings
    lst = []
    for x in lst0:
        if x not in lst:
            lst.append(x)
    lst.sort()
    pairs = []
    i = 0
    while i < (len(lst)-1):
        for j in range(i+1, len(lst)):
            if [lst[i], lst[j]] not in pairs:
                pairs.append([lst[i], lst[j]])
        i += 1
    return pairs


def calc_dist(lat0, lon0, lat1, lon1):
    # INPUT: latitude and longitude of two points
    # OUTPUT: distance between two points in km
    dist = Geodesic.WGS84.Inverse(lat0, lon0, lat1, lon1)['s12']
    return dist/1000


#===============#
numEGF = 0
finalPairs = []
for pair in find_uniq_pairs(sta):
    dist = calc_dist(staLat[pair[0]], staLon[pair[0]],
                     staLat[pair[1]], staLon[pair[1]])
    if dist >= mindist and dist <= maxdist:
        finalPairs.append([pair[0], pair[1]])
        numEGF += 1

print(f" Maximum number of EGFs will be {numEGF}\n\n")

uans = 'y'
#uans=input("Do you want to plot inter-station raypaths (y/n)? ")
uans.lower()
print("\n")
if uans != 'y':
    print("Exit program!\n")
    exit()


centre = [(min(lon)+max(lon))/2, (min(lat)+max(lat))/2]
regSize = [max(lon)-min(lon), max(lat)-min(lat)]
xpadding = padding_coe*regSize[0]*cos(radians(centre[1]))
ypadding = padding_coe*regSize[1]
print('Plotting in progress ...\n')

fig, ax = plt.subplots(figsize=(mapSize, mapSize))
map = Basemap(llcrnrlon=min(lon)-xpadding, llcrnrlat=min(lat)-ypadding,
              urcrnrlon=max(lon)+xpadding, urcrnrlat=max(lat)+ypadding,
              projection='lcc', lat_1=min(lat), lat_2=max(lat),
              lon_0=(min(lon)+max(lon))/2, lat_0=(min(lat) +
                                                  max(lat))/2, resolution='i',
              area_thresh=1000., ax=ax)

map.fillcontinents(color='0.9')
map.drawcountries(linewidth=0.4)
map.drawcoastlines(linewidth=0.25)
for pair in finalPairs:
    xx = [staLon[pair[0]], staLon[pair[1]]]
    yy = [staLat[pair[0]], staLat[pair[1]]]
    x, y = map(xx, yy)
    map.plot(x, y, color='black', linewidth=0.5)

x, y = map(lon, lat)
map.plot(x, y, color='magenta', marker='o', markersize=4, linewidth=0)
plt.tight_layout()
plt.show()
