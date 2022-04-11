#!/bin/csh
# This script generates a global map with some gc paths on it
#
# USAGE: csh plot_global_map.csh <points>
#   where <points> has 5 columns:
#   1)lon  2)lat 3)azim 4)arc 5)GMT w-flag
# UPDATE: 21 April 2020
#===Adjustable Parameters====#
set output = 'global_map' #without file extenstion
set map_region = '-240/60/-90/90'
set media_size = 20 #in cm
set A_flag = '-A1000' #gmt -A flag
set N_flag = '-N1/thin,SLATEGRAY4 -N2/thin,SLATEGRAY4'
set land_color = 'grey66'
set ocean_color = 'steelblue1'
set gmt_annotation = '-Bg20 -Bx40 -By20 -BWENs'
set coastline_resolution = 'i' #options: c, l, i, h, f
#============================#

#GMT set defaults
set ps_media = `echo $media_size|awk '{printf "%fcx%fc",$1+2,$1+2}'`
gmt set PS_MEDIA $ps_media GRID_PEN_PRIMARY 0.5p,gray,--

clear
if ($#argv != 1) then
    printf ' Usage: csh robinson_map.csh <points>\n where <points>: 1)lon  2)lat 3)azim 4)arc 5)GMT w-flag\n\n'
    exit
endif

set nPaths = `cat $argv[1]|wc -l`
set lon = `awk '{printf "%f ",$1}' $argv[1]`
set lat = `awk '{printf "%f ",$2}' $argv[1]`
set azim = `awk '{printf "%f ",$3}' $argv[1]`
set arc = `awk '{printf "%f ",$4}' $argv[1]`
set style = `awk '{printf "%s ",$5}' $argv[1]`
set shape = `awk '{printf "%s ",$6}' $argv[1]`

gmt pscoast -R$map_region -JN"$media_size"c $gmt_annotation -D$coastline_resolution $A_flag -W0.3p,black -G$land_color -S$ocean_color  $N_flag -P -X1c -Y1c -K > $output.ps

#plate boundaries
set nop = `ls plates/*.dat|wc -l`
set plates = `ls plates/*.dat`
@ i=1
while ($i <= $nop)
    cat $plates[$i]|gmt psxy -R -J -O -P -K -Wthick,white >> $output.ps
    @ i++
end

#great circles
set nop = 1000
@ i=1
while ($i <= $nPaths)
    gmt project -C$lon[$i]/$lat[$i] -A$azim[$i] -G1 -L0/$arc[$i]|awk '{printf "%.4f %.4f\n",$1,$2}' > tmp
    set nol = `cat tmp|wc -l|awk '{print $1-1}'`
    head -n$nol tmp > xy.tmp
    cat xy.tmp| gmt psxy -R -J -O -K -P -W$style[$i] >> $output.ps
    rm -f xy.tmp tmp
    @ i++
end

@ i=1
while ($i <= $nPaths)
    echo $lon[$i] $lat[$i]| gmt psxy -R -J -O -K -P -S$shape[$i] -Gsnow3 -Wthin,black >> $output.ps
    @ i++
end

echo 0 0|gmt psxy -R -J -O -P -Sc0.001p -Gblack -Wthin,black >> $output.ps

ps2eps -q -f $output.ps
epstopdf $output.eps $output.pdf
rm -f $output.eps $output.ps gmt.*

open $output.pdf
