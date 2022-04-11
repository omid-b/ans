#!/usr/bin/env python
# This script generates a map using a regional-scale map projection.

about = 'This script generates an ESRI map with fan-diagrams using a regional (epsg) projection.'
usage = '''

USAGE:
  python plot_regional_map.py <fan-diagrams>

Note, <fan-diagrams> is optional and in the following format:
  1) fan-diagram (png file location)   2) longitude   3) latitude

'''
#Coded by omid.bagherpur@gmail.com
#UPDATE: 4 April 2020
#=====Adjustable Parameters=====#
output_fname = 'regional_map'
output_format = 'pdf'
output_dpi = 600
fan_zoom = 0.008
figure_size =  12

#Esri map parameters
llcrnrlon = -80
urcrnrlon = -53
llcrnrlat = 39
urcrnrlat = 52
epsg = 2013 #map projection epsg code; find more at https://spatialreference.org/ref/epsg/
services = ['World_Imagery', #0
            'World_Street_Map', #1
            'World_Topo_Map', #2
            'World_Shaded_Relief', #3
            'USA_Topo_Maps', #4
            'NatGeo_World_Map', #5
            'World_Physical_Map', #6
            'World_Terrain_Base', #7
            'ESRI_Imagery_World_2D', #8
            'ESRI_StreetMap_World_2D', #9
            'Ocean_Basemap' #10
            ]
service = services[0] #choose from services in the above line
esri_dpi = 600
xpixels = 3000
verbose = True

#Plot parameters
marker_only = False #True or False; if True, fan diagrams will not be plotted!
marker_size = [1.5, 1] #a list of two; only if marker_only=True
xticks = range(-80, -53, 3)
yticks = range(-90,70,2)
parallels_color = (1,1,1,0.15) #(R,G,B,A)
drawcoastlines = True
drawcounties = False
linewidth=0.3
color= (0,0,0,0.5)
resolution_flag = 'h'
#===============================#
lon_0 = f"%.2f" %(llcrnrlon+(urcrnrlon-llcrnrlon)/2)
lat_0 = f"%.2f" %(llcrnrlat+(urcrnrlat-llcrnrlat)/2)
try:
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    from matplotlib._png import read_png
    from PIL import Image
    
    import os, sys, math
    import numpy as np
    import matplotlib.pyplot as plt
    from mpl_toolkits.basemap import Basemap
except Exception as e:
    print(f'{e}\n')
    exit()

os.system('clear')
print(about, usage)
print(f"Map centre:\n centre=[{lon_0},{lat_0}]\n")

if len(sys.argv) > 1:
    if os.path.isfile(sys.argv[1]):
        print(f"Input <points>: '{sys.argv[1]}'\n")
        output_fname = sys.argv[1].split('/')[-1].split('.')[0]
        fn = open(sys.argv[1], 'r')
        points=[]
        fans=[]
        for line in fn:
            point = [ float(line.split()[1]), float(line.split()[2]) ]
            points.append(point)
            if os.path.isfile(line.split()[0]):
                fans.append(line.split()[0])
            else:
                print(f"Error finding fan-diagram: {line.split()[0]}\n")
                exit()
    else:
        print('Error in finding <points>!')
        exit()

uans = input('Do you want to continue (y/n)? ')
if uans == 'n':
    print('\nExit program!\n\n')
    exit()

lon_0 = float(lon_0)
lat_0 = float(lat_0)

fig, ax = plt.subplots(figsize=(figure_size,figure_size))

m = Basemap(llcrnrlon=llcrnrlon,llcrnrlat=llcrnrlat,urcrnrlon=urcrnrlon,urcrnrlat=urcrnrlat, epsg=epsg, resolution=resolution_flag)

m.arcgisimage(service=service, xpixels = xpixels, dpi=esri_dpi, verbose= verbose)

if drawcounties:
    m.drawcounties()

if drawcoastlines:
    m.drawcoastlines(linewidth=linewidth, color=color)

xticks_labels = [0,0,1,0]
yticks_labels = [1,1,0,0]
m.drawmeridians(xticks, parallels_color, labels=xticks_labels, dashes=(3,3))
m.drawparallels(yticks, parallels_color, labels=yticks_labels, dashes=(3,3))


if marker_only:
    if len(sys.argv) > 1:
        i=0
        for point in points:
            x = [point[0], point[0]]
            y = [point[1]-marker_size[1]/2, point[1]+marker_size[1]/2]
            m.plot(x,y,latlon=True,color='r',linewidth=1)
            x = [point[0]-marker_size[0]/2, point[0]+marker_size[0]/2]
            y = [point[1], point[1]]
            m.plot(x,y,latlon=True,color='r',linewidth=1)
            x,y = m(point[0], point[1])
            plt.text(x, y, f"{i+1}",fontsize=6,fontweight='bold',ha='center',va='top',color=(1,1,1,1))
            i+=1

else:
    if len(sys.argv) > 1:
        for i in range(len(points)):
            x0, y0 = m(points[i][0], points[i][1])
            x1, y1 = x0, y0+1e4
            x2, y2 = m(points[i][0], points[i][1]+1)

            abs1 = math.sqrt((x1-x0)**2 + (y1-y0)**2)
            abs2 = math.sqrt((x2-x0)**2 + (y2-y0)**2)
            dotProduct = (x1-x0)*(x2-x0) + (y1-y0)*(y2-y0)
            acosine = math.acos(dotProduct/(abs1*abs2))
            theta = np.rad2deg(acosine)

            if points[i][0] < lon_0:
                theta*=-1

            fan  = Image.open(fans[i])
            fan_rotated     = fan.rotate(theta)
            fan_rotated.save(f'fan.png')
            im = read_png('fan.png')
            os.remove('fan.png')
            imbox = OffsetImage(im, zoom=fan_zoom)
            ab = AnnotationBbox(imbox, [x0, y0], frameon=False)
            ax.add_artist(ab)



plt.tight_layout()
plt.savefig(f"{output_fname}.{output_format}",format=output_format, dpi=output_dpi)
print(f"\n{output_fname}.{output_format} has been generated!\n\n")




