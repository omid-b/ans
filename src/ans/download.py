import os
from urllib import request
from . import config
import obspy
import shutil
import subprocess


pkg_dir, _ = os.path.split(__file__)
fetch_data_script = os.path.join(pkg_dir, "data", "FetchData-2018.337")


#==== MAIN FUNCTIONS ====#

def download_stations(maindir):
    maindir = os.path.abspath(maindir)
    stalist = os.path.split(config.read_config(maindir)['download']['le_stalist'])[1]
    print(f"  Generating list of stations: '{stalist}'")
    stations = Stations(maindir) 
    datacenters = stations.get_datacenters()
    stalist = stations.request_stalist()
    stations.write_stalist(stalist, datacenters)
    print("\nDone!\n")


def download_metafiles(maindir):
    maindir = os.path.abspath(maindir)
    stations = Stations(maindir) 
    stations.download_xml_files()
    print("\nDone!\n")


#========================#


class Stations:

    def __init__(self,maindir):
        self.maindir = os.path.abspath(maindir)
        self.config = config.read_config(self.maindir)
        self.stalist_file = self.config['download']['le_stalist']
        self.stalist_fname = os.path.split(self.stalist_file)[1]


    def get_datacenters(self):
        datacenters = []
        if self.config['download']['chb_dc_auspass_edu_au']:
            datacenters.append("http://auspass.edu.au:8080/fdsnws/station/1")
        if self.config['download']['chb_dc_eida_sc3_infp_ro']:
            datacenters.append("http://eida-sc3.infp.ro/fdsnws/station/1")
        if self.config['download']['chb_dc_eida_service_koeri_boun_edu_tr']:
            datacenters.append("http://eida-service.koeri.boun.edu.tr/fdsnws/station/1")
        if self.config['download']['chb_dc_eida_bgr_de']:
            datacenters.append("http://eida.bgr.de/fdsnws/station/1")
        if self.config['download']['chb_dc_eida_ethz_ch']:
            datacenters.append("http://eida.ethz.ch/fdsnws/station/1")
        if self.config['download']['chb_dc_eida_gein_noa_gr']:
            datacenters.append("http://eida.gein.noa.gr/fdsnws/station/1")
        if self.config['download']['chb_dc_eida_ipgp_fr']:
            datacenters.append("http://eida.ipgp.fr/fdsnws/station/1")
        if self.config['download']['chb_dc_erde_geophysik_uni_muenchen_de']:
            datacenters.append("http://erde.geophysik.uni-muenchen.de/fdsnws/station/1")
        if self.config['download']['chb_dc_geofon_gfz_potsdam_de']:
            datacenters.append("http://geofon.gfz-potsdam.de/fdsnws/station/1")
        if self.config['download']['chb_dc_rtserve_beg_utexas_edu']:
            datacenters.append("http://rtserve.beg.utexas.edu/fdsnws/station/1")
        if self.config['download']['chb_dc_seisrequest_iag_usp_br']:
            datacenters.append("http://seisrequest.iag.usp.br/fdsnws/station/1")
        if self.config['download']['chb_dc_service_iris_edu']:
            datacenters.append("http://service.iris.edu/fdsnws/station/1")
        if self.config['download']['chb_dc_service_ncedc_org']:
            datacenters.append("http://service.ncedc.org/fdsnws/station/1")
        if self.config['download']['chb_dc_service_scedc_caltech_edu']:
            datacenters.append("http://service.scedc.caltech.edu/fdsnws/station/1")
        if self.config['download']['chb_dc_webservices_ingv_it']:
            datacenters.append("http://webservices.ingv.it/fdsnws/station/1")
        if self.config['download']['chb_dc_ws_icgc_cat']:
            datacenters.append("http://ws.icgc.cat/fdsnws/station/1")
        if self.config['download']['chb_dc_ws_resif_fr']:
            datacenters.append("http://ws.resif.fr/fdsnws/station/1")
        if self.config['download']['chb_dc_www_orfeus_eu_org']:
            datacenters.append("http://www.orfeus-eu.org/fdsnws/station/1")
        if self.config['download']['chb_dc_fdsnws_raspberryshakedata_com']:
            datacenters.append("https://fdsnws.raspberryshakedata.com/fdsnws/station/1")
        return datacenters


    def get_channels(self):
        channels = self.config['download']['le_stachns'].split()
        if not len(channels):
            print("Error! Station channels to download are not specified!\n")
            exit(1)
        return channels


    def get_dates(self):
        startdate = self.config['setting']['le_startdate']
        enddate = self.config['setting']['le_enddate']
        if not len(startdate) or not len(enddate):
            print("Error! Project start/end dates are not specified!\n")
            exit(1)
        return [startdate, enddate]


    def get_latitudes(self):
        minlat = self.config['setting']['le_minlat']
        maxlat = self.config['setting']['le_maxlat']
        return [minlat, maxlat]


    def get_longitude(self):
        minlon = self.config['setting']['le_minlon']
        maxlon = self.config['setting']['le_maxlon']
        return [minlon, maxlon]


    def request_stalist(self):
        datacenters = self.get_datacenters()
        channels = self.get_channels()
        dates = self.get_dates()
        region_lat = self.get_latitudes()
        region_lon = self.get_longitude()
        stalist = {
        'net':[],
        'sta':[],
        'lat':[],
        'lon':[],
        'elv':[],
        'site':[],
        'start':[],
        'end':[]
        }
        for k, chn in enumerate(channels):
            for datacenter in datacenters:
                stations_xml = os.path.join(self.maindir, '.ans',f"{self.stalist_fname}.{chn}_{datacenter.split('/')[2]}.xml")
                url = f"{datacenter}/query?starttime={dates[0]}T00:00:00&endtime={dates[1]}T23:59:59&minlat={region_lat[0]}&maxlat={region_lat[1]}&minlon={region_lon[0]}&maxlon={region_lon[1]}&channel={chn}"
                try:
                    req = request.Request(url)
                    resp = request.urlopen(req).read().decode('utf-8')
                    fopen = open(stations_xml,'w')
                    fopen.write(f"{resp}")
                    fopen.close()
                    inv = obspy.read_inventory(stations_xml,format="STATIONXML")
                    # store requested information
                    for i in range(len(inv)):
                        for j in range(len(inv[i])):
                            sta = inv[i][j].code
                            if sta not in stalist['sta']:
                                stalist['net'].append(inv[i].code)
                                stalist['sta'].append(inv[i][j].code)
                                stalist['lat'].append(inv[i][j]._latitude)
                                stalist['lon'].append(inv[i][j]._longitude)
                                stalist['elv'].append(inv[i][j]._elevation)
                                stalist['site'].append(inv[i][j].site.name)
                                stalist['start'].append(str(inv[i][j].start_date).split('.')[0])
                                stalist['end'].append(str(inv[i][j].end_date).split('.')[0])
                except Exception:
                    if os.path.isfile(stations_xml):
                        os.remove(stations_xml)
        return stalist


    def write_stalist(self, stalist, datacenters):
        nsta = len(stalist['sta'])
        output_lines = ["#Network | Station | Latitude | Longitude | Elevation | Sitename | StartTime | EndTime", "",
        "# Datacenters:"]
        for dc in datacenters:
            output_lines.append(f"#{dc}")
        output_lines.append("")
        for i in range(nsta):
            net = str(stalist['net'][i]).strip()
            sta = str(stalist['sta'][i]).strip()
            lat = str(stalist['lat'][i]).strip()
            lon = str(stalist['lon'][i]).strip()
            elv = str(stalist['elv'][i]).strip()
            site = str(stalist['site'][i]).strip()
            start = str(stalist['start'][i]).strip()
            end = str(stalist['end'][i]).strip()
            output_lines.append(f"{net}|{sta}|{lat}|{lon}|{elv}|{site}|{start}|{end}")
        # write output
        fopen = open(os.path.join(self.maindir, self.stalist_fname),'w')
        for line in output_lines:
            fopen.write(f"{line}\n")
        fopen.close()


    def read_stalist(self):

        if not os.path.isfile(self.stalist_file):
            print(f"Error! Could not find station list: '{self.stalist_fname}'")
            exit(1)
        fopen = open(self.stalist_file,'r')
        flines = fopen.read().splitlines()
        fopen.close()
        stalist_lines = []
        for line in flines:
            line = line.strip()
            if line not in stalist_lines \
            and len(line) \
            and line[0] != '#':
                stalist_lines.append(line)
        # generate stalist dict
        stalist = {
        'net':[],
        'sta':[],
        'lat':[],
        'lon':[],
        'elv':[],
        'site':[],
        'start':[],
        'end':[]
        }
        try:
            for line in stalist_lines:
                line = line.split('|')
                stalist['net'].append(line[0])
                stalist['sta'].append(line[1])
                stalist['lat'].append(line[2])
                stalist['lon'].append(line[3])
                stalist['elv'].append(line[4])
                stalist['site'].append(line[5])
                stalist['start'].append(line[6])
                stalist['end'].append(line[7])
        except Exception:
            print(f"Read station list format Error!")
            exit(1)
        return stalist


    def download_xml_files(self):
        dates = self.get_dates()
        channels = self.get_channels()
        stalist = self.read_stalist()
        download_list = self.gen_download_list(stalist)
        PERL = self.config['setting']['le_perl']
        # make (or remake) metafilesdir
        metafilesdir = self.config['download']['le_stameta']
        if os.path.isdir(metafilesdir):
            shutil.rmtree(metafilesdir)
        os.mkdir(metafilesdir)

        # start downloading
        starttime = f"{dates[0]},00:00:00"
        endtime = f"{dates[1]},23:59:59"

        for i, chn in enumerate(channels):
            print(f"\nDownload station meta files for channel: {chn}\n")
            for j, netsta in enumerate(download_list[i]):
                net = netsta.split('.')[0]
                sta = netsta.split('.')[1]
                outfile = os.path.join(metafilesdir, f"{net}.{sta}.{chn}")
                bash_cmd = f"{PERL} {fetch_data_script} -S {sta} -N {net} -C {chn} -s {starttime} -e {endtime} -X {outfile} -q\n"
                print(f" meta data ({j+1} of {len(download_list[i])}):  {net}.{sta}.{chn}")
                subprocess.call(bash_cmd, shell=True)

        # # generate/update station file
        # if os.path.isfile(self.stalist_file):
        #     shutil.copyfile(self.stalist_file,
        #     os.path.join(self.maindir,f"{self.stalist_fname}.backup"))
        # self.write_stalist(stalist)
        # print(f"\nNumber of stations: {len(stalist['net'])}\n")
        # print(f"\nDone!\n")


    def gen_download_list(self, stalist):
        datacenters = self.get_datacenters()
        channels = self.get_channels()
        dates = self.get_dates()
        region_lat = self.get_latitudes()
        region_lon = self.get_longitude()
        metafilesdir = self.config['download']['le_stameta']
        download_list = [[] for i in range(len(channels))]
        for k, chn in enumerate(channels):
            for datacenter in datacenters:
                stations_xml = os.path.join(metafilesdir, f"{self.stalist_fname}.{chn}_{datacenter.split('/')[2]}.xml")
                url = f"{datacenter}/query?starttime={dates[0]}T00:00:00&endtime={dates[1]}T23:59:59&minlat={region_lat[0]}&maxlat={region_lat[1]}&minlon={region_lon[0]}&maxlon={region_lon[1]}&channel={chn}"
                try:
                    req = request.Request(url)
                    resp = request.urlopen(req).read().decode('utf-8')
                    fopen = open(stations_xml,'w')
                    fopen.write(f"{resp}")
                    fopen.close()
                    inv = obspy.read_inventory(stations_xml,format="STATIONXML")
                    for i in range(len(inv)):
                        for j in range(len(inv[i])):
                            net = inv[i].code
                            sta = inv[i][j].code
                            if net in stalist['net'] and sta in stalist['sta']:
                                download_list[k].append(f"{net}.{sta}")
                except Exception:
                    if os.path.isfile(stations_xml):
                        os.remove(stations_xml)
        return download_list

