#!/usr/bin/env python
# This script generates a map using a continental-scale map projection.

about = 'This script generates a bluemarble map in gnomonic projection'
usage = '''

USAGE:
  python plot_continental_map.py <fan-diagrams>

Note, <fan-diagrams> is optional and in the following format:
  1) fan-diagram (png file location)   2) longitude   3) latitude

'''
#Coded by omid.bagherpur@gmail.com
#UPDATE: 4 April 2020
#=====Adjustable Parameters=====#
output_fname = 'continental_map'
output_format = 'pdf'
output_dpi = 600
fan_zoom = 0.015

lon_0 = -95
lat_0 = 44
width =  7500 #in km
height =  5000 #in km
size_factor = 1.5 #controls the document dimensions


#Plot parameters
bluemarble_scale = 3 #Affect the quality of bluemarble
xticks =  [-140,-130,-120,-110,-100,-90,-80,-70,-60,-50]
yticks = [25,30,35,40,45,50,55,60]
marker_only = False #True or False
marker_size = [1.5, 1] #a list of two
parallels_color = (1,1,1,0.15) #(R,G,B,A)
drawcoastlines = True
drawcounties = False
linewidth=0.3
color= (0,0,0,0.5)
resolution_flag = 'h'
#===============================#

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
print(f"Map parameters:\n  width(km)={width}, height(km)={height}, centre=[{lon_0},{lat_0}]\n")
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


fig, ax = plt.subplots(figsize=(width/1000*size_factor,height/1000*size_factor))


m = Basemap(projection='gnom',lat_0=lat_0,lon_0=lon_0,width=width*1000, height=height*1000, resolution=resolution_flag)

m.bluemarble(scale=bluemarble_scale)

if drawcounties:
    m.drawcounties()

if drawcoastlines:
    m.drawcoastlines(linewidth=linewidth, color=color)

xticks_labels = [0,0,1,0]
yticks_labels = [1,1,0,0]
m.drawmeridians(xticks, parallels_color,labels=xticks_labels, dashes=(3,3))
m.drawparallels(yticks, parallels_color,labels=yticks_labels, dashes=(3,3))


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




