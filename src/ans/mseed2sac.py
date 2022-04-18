
import os
import obspy
from . import config

def get_mseed2sac_proc_list(maindir):
	conf = config.read_config(maindir)
	
