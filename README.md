# ANS: Ambient Noise Seismology

ans is a python wrapper for ambient noise seismology tasks and it has a GUI for easier configuration of ambient-noise seismology projects. In its backend, this package depends on Perl interpreter, GMT (Generic Mapping Tools), and SAC (Seismic Analysis Code) as well as python modules including ObsPy etc. ans is successfully tested on Python 3.6.* and 3.8.* versions.

## Version 0.0.1

This version include all the necessary commands and tools required for generating Rayleigh wave (ZZ and RR cross-correlations) and Love wave (TT cross-correlation component) Empirical Green's Functions (EGFs). A brief description of most useful CLI commands is given below:

	- $> ans init <maindir>
	  Description: initialize ans project at project main directory i.e. <maindir>

	- $> ans config
	  $> ans config --maindir <maindir>
	  Description: open the program GUI to configure the ans project
	  Note: default <maindir> is current working directory

	- $> ans download stations
	  Description: download list of available stations at the given 
	  region boundary and dates that was previously set using the GUI.
	  Datacenters, desired station components etc should also be set using '$> ans config'.

	- $> ans download metadata
	  Description: download station metadata files (xml file format) that will be used for
	  instrument response removal and updating sac headers.

	- $> ans download mseeds
	  Description: main data acquisition module; download seismograms in mseed format

	- $> ans mseed2sac <mseeds_dir> <sacs_dir>
	  Description: convert mseed to sac files while applying the listed processing steps
	  in project configuration mseed2sac tab (i.e., '$> ans config').
	  <mseeds_dir>: input mseed dataset directory
	  <sacs_dir>: output sac files dataset directory

	- $> ans sac2ncf <sacs_dir> <ncfs_dir>
	  Description: process the input sacfiles in <sacs_dir> and output NCFs (noise cross-correlation functions)
	  while applying the list of sac2ncf processes defined in project configuration file.
	  Note: At this step it is necessary that all sac headers are updated and this can be done by either
	  performing instrument response removal or adding "write headers" process to the list of processes.

	- $> ans ncf2egf <ncfs> <egfs_dir>
	  <ncfs>: either path to the <ncfs_dir> (full stack EGFs) or an ASCII datalist containing a one-column data format
	  list of paths to event directories (seasonal EGFs; e.g., "14001000000" i.e. 2014/01/01)
	  <egfs_dir>: path to output stacked EGF



