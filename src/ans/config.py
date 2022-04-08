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


def read_config(config_file):
    try:
        config = configparser.ConfigParser()
        config.read(os.path.abspath(config_file))
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
        if param not in config.options('setting'):
            print(f"read_config(): Config parameter not available in [setting]: '{param}'")
            return False
        if param in integer_params:
            setting[f"{param}"] = int(config.get('setting',f"{param}"))
        elif param in float_params:
            setting[f"{param}"] = float(config.get('setting',f"{param}"))
        elif param in intlist_params:
            setting[f"{param}"] = config.get('setting',f"{param}")
            setting[f"{param}"] = array(setting[f"{param}"].split(), dtype=int).tolist()
        else:
            setting[f"{param}"] = config.get('setting',f"{param}")
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



def write_config(config_file):
    pass


    



class Defaults:
    def __init__(self, maindir):
        self.maindir = maindir

    def setting(self):
        parameters = {}
        parameters['le_maindir'] = self.maindir
        parameters['le_startdate'] = ""
        parameters['le_enddate'] = ""
        parameters['le_maxlat'] = ""
        parameters['le_minlon'] = ""
        parameters['le_maxlon'] = ""
        parameters['le_minlat'] = ""
        if sys.platform in ['darwin', 'linux', 'linux2', 'cygwin']:
            if os.system('which sac') == 0:
                parameters['le_sac'] = subprocess.check_output("which sac", shell=True).decode("utf-8").split('\n')[0]
            else:
                parameters['le_sac'] = '/usr/local/sac/bin/sac'
            if os.system('which gmt') == 0:
                parameters['le_gmt'] = subprocess.check_output("which gmt", shell=True).decode("utf-8").split('\n')[0]
            else:
                parameters['le_gmt'] = '/usr/bin/gmt'
            if os.system('which perl') == 0:
                parameters['le_perl'] = subprocess.check_output("which perl", shell=True).decode("utf-8").split('\n')[0]
            else:
                parameters['le_perl'] = '/usr/bin/perl'
        elif sys.platform in ['win32']:
            if os.system('where sac') == 0:
                parameters['le_sac'] = subprocess.check_output("where sac", shell=True).decode("utf-8").split('\n')[0]
            else:
                parameters['le_sac'] = ""
            if os.system('where gmt') == 0:
                parameters['le_gmt'] = subprocess.check_output("where gmt", shell=True).decode("utf-8").split('\n')[0]
            else:
                parameters['le_gmt'] = ""
            if os.system('where perl') == 0:
                parameters['le_perl'] = subprocess.check_output("where perl", shell=True).decode("utf-8").split('\n')[0]
            else:
                parameters['le_perl'] = os.path.join("C:","Strawberry","perl","bin","perl.exe")
        else:
            parameters['le_sac'] = ""
            parameters['le_gmt'] = ""
            parameters['le_perl'] = ""
        return parameters


    def download(self):
        parameters = {}
        # data centers
        parameters['chb_dc_service_iris_edu'] = 2
        parameters['chb_dc_service_ncedc_org'] = 2
        parameters['chb_dc_service_scedc_caltech_edu'] = 2
        parameters['chb_dc_rtserve_beg_utexas_edu'] = 2
        parameters['chb_dc_eida_bgr_de'] = 2
        parameters['chb_dc_ws_resif_fr'] = 2
        parameters['chb_dc_seisrequest_iag_usp_br'] = 2
        parameters['chb_dc_eida_service_koeri_boun_edu_tr'] = 2
        parameters['chb_dc_eida_ethz_ch'] = 2
        parameters['chb_dc_geofon_gfz_potsdam_de'] = 2
        parameters['chb_dc_ws_icgc_cat'] = 2
        parameters['chb_dc_eida_ipgp_fr'] = 2
        parameters['chb_dc_fdsnws_raspberryshakedata_com'] = 2
        parameters['chb_dc_webservices_ingv_it'] = 2
        parameters['chb_dc_erde_geophysik_uni_muenchen_de'] = 2
        parameters['chb_dc_eida_sc3_infp_ro'] = 2
        parameters['chb_dc_eida_gein_noa_gr'] = 2
        parameters['chb_dc_www_orfeus_eu_org'] = 2
        parameters['chb_dc_auspass_edu_au'] = 2
        # download setting
        parameters['le_stalist'] = os.path.join(self.maindir, 'stations.dat')
        parameters['le_stameta'] = os.path.join(self.maindir, 'station_metafiles')
        parameters['le_stalocs'] = ["00","10"]
        parameters['le_stachns'] = ["BHZ","HHZ"]
        parameters['le_timelen'] = 86400
        # download scripts
        parameters['chb_obspy'] = 2
        parameters['chb_fetch'] = 2
        return parameters


    def mseed2sac(self):
        parameters = {}
        parameters['mseed2sac_input_mseeds'] = os.path.join(self.maindir, 'mseedfiles')
        parameters['mseed2sac_output_sacs'] = os.path.join(self.maindir, 'sacfiles')
        parameters['mseed2sac_channels'] = ["BHZ","HHZ"]
        parameters['mseed2sac_procs'] = []
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
        mseed2sac_proc_2['le_mseed2sac_similar_channels'] = ["BHZ","HHZ"]
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
        parameters['mseed2sac_procs'].append(mseed2sac_proc_1)
        parameters['mseed2sac_procs'].append(mseed2sac_proc_2)
        parameters['mseed2sac_procs'].append(mseed2sac_proc_3)
        parameters['mseed2sac_procs'].append(mseed2sac_proc_4)
        return parameters

