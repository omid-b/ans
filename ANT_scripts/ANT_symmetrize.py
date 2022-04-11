#!/usr/bin/env python3
about="This script takes average of causal and acausal components of stacked cross correlations, and generates the final EGFs.\n"
usage = '''
USAGE:
 python3 ANT_symmetrize.py  <dataset dir> <EGFs dir>

<dataset dir>: dataset dir containing stacked cross correlations
<EGFs dir>: output directory

Note: <dataset dir> and <EGFs dir> should not be the same.
'''
#UPDATE: 29 Jan 2020
#Coded by omid.bagherpur@gmail.com
#=====Adjustable Parameters=====#
cut_positive = False #True or False; cut seismograms from 0 to 86400 after symmetrizing
sacfile_regex = 'sac$' #regular expression for sac files
SAC= "/usr/local/sac/bin/sac" #path to SAC software
#===============================#
import os, sys, re, time, subprocess
os.system('clear')
print(about)

if len(sys.argv)!=3:
    print(f"Error USAGE!\n{usage}")
    exit()
else:
    datasetDir=os.path.abspath(sys.argv[1])
    outputDir=os.path.abspath(sys.argv[2])

if datasetDir==outputDir:
    print(f"Error! <dataset dir> and <stacked dir> should not be the same!\n{usage}")
    exit()


sacfiles=[]
for x in os.listdir(datasetDir):
    if re.search(sacfile_regex, x):
        sacfiles.append(x)

if not os.path.isfile(SAC):
    print(f"Error! Path to SAC software does not exist!\nCheck 'Adjustable Parameters'\n\n")
    exit()

if len(sacfiles)==0:
    print("Error! No sac file was found!\nCheck 'sacfile_regex' parameter.\n\n")
    exit()

info=f'''
 Dataset directory: {datasetDir}
 Output directory:  {outputDir}
 Number of station pairs: {len(sacfiles)}
 Only positive part: {cut_positive}
'''
print(info)

uans=input("\n\n Do you want to continue (y/n)? ")
uans.lower()
print('\n')
if uans != 'y':
    print('\n Exit program!\n')
    exit()

if not os.path.isdir(outputDir):
    os.mkdir(outputDir)

#===FUNCTIONS===#
def symmetrize(inputDataset,outputDataset,sacfile):
    input_fn=os.path.join(inputDataset,sacfile)
    output_fn=os.path.join(outputDataset,sacfile)
    shell_cmd=["export SAC_DISPLAY_COPYRIGHT=0", f"{SAC}<<EOF"]
    shell_cmd.append(f"r {input_fn}")
    shell_cmd.append("reverse")
    shell_cmd.append(f"addf {input_fn}")
    shell_cmd.append("div 2")
    if cut_positive:
        shell_cmd.append("cut 0 e")
    shell_cmd.append(f"w {output_fn}")
    shell_cmd.append(f"r {output_fn}")
    shell_cmd.append("w over")
    shell_cmd.append('quit')
    shell_cmd.append('EOF')
    shell_cmd = '\n'.join(shell_cmd)
    subprocess.call(shell_cmd,shell=True)

#===============#

progress= 0
print(f" Program progress: {progress}%", end="    \r")
for i in range(len(sacfiles)):
    symmetrize(datasetDir,outputDir,sacfiles[i])
    progress= "%.0f" %(((i+1)/len(sacfiles))*100)
    print(f" Program progress: {progress}%", end="    \r")

print("\n\n Done!\n")

