import os
import sys
import subprocess
import configparser
from numpy import array

setting_params = ["le_maindir","le_startdate","le_enddate",
                  "le_maxlat","le_minlon","le_maxlon","le_minlat",
                  "le_sac","le_gmt","le_perl"]

download_params = ["chb_dc_service_iris_edu","chb_dc_service_ncedc_org","chb_dc_service_scedc_caltech_edu",
                   "chb_dc_rtserve_beg_utexas_edu","chb_dc_eida_bgr_de","chb_dc_ws_resif_fr","chb_dc_seisrequest_iag_usp_br",
                   "chb_dc_eida_service_koeri_boun_edu_tr","chb_dc_eida_ethz_ch","chb_dc_geofon_gfz_potsdam_de",
                   "chb_dc_ws_icgc_cat","chb_dc_eida_ipgp_fr","chb_dc_fdsnws_raspberryshakedata_com",
                   "chb_dc_webservices_ingv_it","chb_dc_erde_geophysik_uni_muenchen_de","chb_dc_eida_sc3_infp_ro",
                   "chb_dc_eida_gein_noa_gr","chb_dc_www_orfeus_eu_org","chb_dc_auspass_edu_au",
                   "le_stalist","le_stameta","le_stalocs","le_stachns","le_timelen","chb_obspy","chb_fetch"]

mseed2sac_params = ["mseed2sac_input_mseeds","mseed2sac_output_sacs","mseed2sac_channels","mseed2sac_procs"]

integer_params = ["chb_dc_service_iris_edu","chb_dc_service_ncedc_org","chb_dc_service_scedc_caltech_edu",
                  "chb_dc_rtserve_beg_utexas_edu","chb_dc_eida_bgr_de","chb_dc_ws_resif_fr",
                  "chb_dc_seisrequest_iag_usp_br","chb_dc_eida_service_koeri_boun_edu_tr",
                  "chb_dc_eida_ethz_ch","chb_dc_geofon_gfz_potsdam_de","chb_dc_ws_icgc_cat",
                  "chb_dc_eida_ipgp_fr","chb_dc_fdsnws_raspberryshakedata_com","chb_dc_webservices_ingv_it",
                  "chb_dc_erde_geophysik_uni_muenchen_de","chb_dc_eida_sc3_infp_ro",
                  "chb_dc_eida_gein_noa_gr","chb_dc_www_orfeus_eu_org","chb_dc_auspass_edu_au",
                  "chb_obspy","chb_fetch","chb_mseed2sac_detrend","chb_mseed2sac_taper",
                  "cmb_mseed2sac_detrend_method","cmb_mseed2sac_taper_method","sb_mseed2sac_detrend_order",
                  "cmb_mseed2sac_final_sf","cmb_mseed2sac_resp_output","cmb_mseed2sac_resp_prefilter",
                  "sb_mseed2sac_bp_poles","sb_mseed2sac_bp_passes", "le_timelen", "le_mseed2sac_dspline"]

float_params = ["dsb_mseed2sac_max_taper", "sb_mseed2sac_bp_cp1", "sb_mseed2sac_bp_cp2",
                "le_minlat","le_maxlat","le_minlon","le_maxlon"]

intlist_params = ["pid"]



def read_config(maindir):
    maindir = os.path.abspath(maindir)
    config_file = os.path.join(maindir, 'ans.conf')
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
    except Exception as e:
        print(f"Error reading config file!\n{e}\n")
        return False
    # all main sections available?
    for section in ["setting","download","mseed2sac"]:
        if section not in config.sections():
            print(f"read_config(): Config section not available: '{section}'")
            return False
    # setting
    setting = {}
    for param in setting_params:
        val = config.get('setting',f"{param}")
        if param not in config.options('setting'):
            print(f"read_config(): Config parameter not available in [setting]: '{param}'")
            return False
        if param in integer_params and len(val):
            setting[f"{param}"] = int(val)
        elif param in float_params and len(val):
            setting[f"{param}"] = float(val)
        elif param in intlist_params and len(val):
            setting[f"{param}"] = array(val.split(), dtype=int).tolist()
        else:
            setting[f"{param}"] = val
    # download
    download = {}
    for param in download_params:
        if param not in config.options('download'):
            print(f"read_config(): Config parameter not available in [download]: '{param}'")
            return False
        if param in integer_params:
            download[f"{param}"] = int(config.get('download',f"{param}"))
        elif param in float_params:
            download[f"{param}"] = float(config.get('download',f"{param}"))
        elif param in intlist_params:
            download[f"{param}"] = config.get('download',f"{param}")
            download[f"{param}"] = array(download[f"{param}"].split(), dtype=int).tolist()
        else:
            download[f"{param}"] = config.get('download',f"{param}")
    # mseed2sac
    mseed2sac = {}
    for param in mseed2sac_params:
        if param not in config.options('mseed2sac'):
            print(f"read_config(): Config parameter not available in [mseed2sac]: '{param}'")
            return False
        mseed2sac[f"{param}"] = config.get('mseed2sac',f"{param}")
    mseed2sac_proc_sections = mseed2sac['mseed2sac_procs'].split()
    mseed2sac['mseed2sac_procs'] = []
    for section in mseed2sac_proc_sections:
        proc_params = {}
        for param in config.options(f'{section}'):
            if param in integer_params:
                proc_params[f"{param}"] = int(config.get(f"{section}",f"{param}"))
            elif param in float_params:
                proc_params[f"{param}"] = float(config.get(f"{section}",f"{param}"))
            elif param in intlist_params:
                proc_params[f"{param}"] = config.get(f"{section}",f"{param}")
                proc_params[f"{param}"] = array(proc_params[f"{param}"].split(), dtype=int).tolist()
            else:
                proc_params[f"{param}"] = config.get(f"{section}",f"{param}")
        mseed2sac['mseed2sac_procs'].append(proc_params)
    # put together the return dictionary
    parameters = {}
    parameters['setting'] = setting
    parameters['download'] = download
    parameters['mseed2sac'] = mseed2sac
    return parameters



def write_config(maindir, parameters):
    maindir = os.path.abspath(maindir)
    config_file = os.path.join(maindir, 'ans.conf')
    if not parameters:
        return False
    fopen = open(config_file, "w") 
    # setting
    fopen.write("[setting]\n")
    for key in parameters['setting'].keys():
        fopen.write(f"{key} = {parameters['setting'][key]}\n")
    # download
    fopen.write("\n[download]\n")
    for key in parameters['download'].keys():
        fopen.write(f"{key} = {parameters['download'][key]}\n")
    # mseed2sac
    fopen.write("\n[mseed2sac]\n")
    fopen.write(f"mseed2sac_input_mseeds = {parameters['mseed2sac']['mseed2sac_input_mseeds']}\n")
    fopen.write(f"mseed2sac_output_sacs = {parameters['mseed2sac']['mseed2sac_output_sacs']}\n")
    fopen.write(f"mseed2sac_channels = {parameters['mseed2sac']['mseed2sac_channels']}\n")
    nprocs = len(parameters['mseed2sac']['mseed2sac_procs'])
    proc_sections = []
    for i in range(nprocs):
        proc_sections.append(f"mseed2sac_proc_{i+1}")
    fopen.write(f"mseed2sac_procs = {' '.join(proc_sections)}\n")
    for i, section in enumerate(proc_sections):
        fopen.write(f"\n[{section}]\n")
        for key in parameters['mseed2sac']['mseed2sac_procs'][i].keys():
            if key in intlist_params:
                fopen.write(f"{key} = {' '.join(array(parameters['mseed2sac']['mseed2sac_procs'][i][key], dtype=str))}\n")
            else:
                fopen.write(f"{key} = {parameters['mseed2sac']['mseed2sac_procs'][i][key]}\n")
    fopen.close()
    return True



class Defaults:
    def __init__(self, maindir):
        self.maindir = os.path.abspath(maindir)

    
    def parameters(self):
        parameters = {}
        parameters['setting'] = self.setting()
        parameters['download'] = self.download()
        parameters['mseed2sac'] = self.mseed2sac()
        return parameters



    def setting(self):
        setting = {}
        setting['le_maindir'] = self.maindir
        setting['le_startdate'] = ""
        setting['le_enddate'] = ""
        setting['le_maxlat'] = ""
        setting['le_minlon'] = ""
        setting['le_maxlon'] = ""
        setting['le_minlat'] = ""
        if sys.platform in ['darwin', 'linux', 'linux2', 'cygwin']:
            setting['le_sac'] = '/usr/local/sac/bin/sac'
            setting['le_gmt'] = '/usr/bin/gmt'
            setting['le_perl'] = '/usr/bin/perl'
        else:
            setting['le_sac'] = ""
            setting['le_gmt'] = ""
            setting['le_perl'] = ""
        return setting


    def download(self):
        download = {}
        # data centers
        download['chb_dc_service_iris_edu'] = 2
        download['chb_dc_service_ncedc_org'] = 0
        download['chb_dc_service_scedc_caltech_edu'] = 0
        download['chb_dc_rtserve_beg_utexas_edu'] = 0
        download['chb_dc_eida_bgr_de'] = 0
        download['chb_dc_ws_resif_fr'] = 0
        download['chb_dc_seisrequest_iag_usp_br'] = 0
        download['chb_dc_eida_service_koeri_boun_edu_tr'] = 0
        download['chb_dc_eida_ethz_ch'] = 0
        download['chb_dc_geofon_gfz_potsdam_de'] = 0
        download['chb_dc_ws_icgc_cat'] = 0
        download['chb_dc_eida_ipgp_fr'] = 0
        download['chb_dc_fdsnws_raspberryshakedata_com'] = 0
        download['chb_dc_webservices_ingv_it'] = 0
        download['chb_dc_erde_geophysik_uni_muenchen_de'] = 0
        download['chb_dc_eida_sc3_infp_ro'] = 0
        download['chb_dc_eida_gein_noa_gr'] = 0
        download['chb_dc_www_orfeus_eu_org'] = 0
        download['chb_dc_auspass_edu_au'] = 0
        # download setting
        download['le_stalist'] = os.path.join(self.maindir, 'stations.dat')
        download['le_stameta'] = os.path.join(self.maindir, 'station_metafiles')
        download['le_stalocs'] = "00 10"
        download['le_stachns'] = "BHZ HHZ"
        download['le_timelen'] = 86400
        # download scripts
        download['chb_obspy'] = 2
        download['chb_fetch'] = 2
        return download


    def mseed2sac(self):
        mseed2sac = {}
        mseed2sac['mseed2sac_input_mseeds'] = os.path.join(self.maindir, 'mseedfiles')
        mseed2sac['mseed2sac_output_sacs'] = os.path.join(self.maindir, 'sacfiles')
        mseed2sac['mseed2sac_channels'] = "BHZ HHZ"
        mseed2sac['mseed2sac_procs'] = []
        # process 1 
        mseed2sac_proc_1 = {}
        mseed2sac_proc_1['pid'] = [1,1] # MSEED to SAC
        mseed2sac_proc_1['chb_mseed2sac_detrend'] = 2
        mseed2sac_proc_1['chb_mseed2sac_taper'] = 2
        mseed2sac_proc_1['cmb_mseed2sac_detrend_method'] = 3
        mseed2sac_proc_1['sb_mseed2sac_detrend_order'] = 4
        mseed2sac_proc_1['le_mseed2sac_dspline'] = 864000
        mseed2sac_proc_1['cmb_mseed2sac_taper_method'] = 0
        mseed2sac_proc_1['dsb_mseed2sac_max_taper'] = 0.050
        # process 2
        mseed2sac_proc_2 = {}
        mseed2sac_proc_2['pid'] = [2,1] # Remove channel
        mseed2sac_proc_2['le_mseed2sac_similar_channels'] = "BHZ HHZ"
        mseed2sac_proc_2['le_mseed2sac_channel2keep'] = "HHZ"
        # process 3  
        mseed2sac_proc_3 = {}
        mseed2sac_proc_3['pid'] = [3,1] # Decimate
        mseed2sac_proc_3['cmb_mseed2sac_final_sf'] = 0 # 1 Hz
        # process 4 
        mseed2sac_proc_4 = {}
        mseed2sac_proc_4['pid'] = [4,1] # Remove response
        mseed2sac_proc_4['le_mseed2sac_stametadir'] = os.path.join(self.maindir, 'station_metafiles')
        mseed2sac_proc_4['cmb_mseed2sac_resp_output'] = 1 # velocity
        mseed2sac_proc_4['cmb_mseed2sac_resp_prefilter'] = 1 # [0.001, 0.005, 45, 50]
        # append processes to the list
        mseed2sac['mseed2sac_procs'].append(mseed2sac_proc_1)
        mseed2sac['mseed2sac_procs'].append(mseed2sac_proc_2)
        mseed2sac['mseed2sac_procs'].append(mseed2sac_proc_3)
        mseed2sac['mseed2sac_procs'].append(mseed2sac_proc_4)
        return mseed2sac

