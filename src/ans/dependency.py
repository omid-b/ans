import os
import sys
import subprocess

def perl_warnings():
    warnings = []
    value = subprocess.call('perl --version',shell=True,
    stderr=subprocess.STDOUT,
    stdout=subprocess.DEVNULL)
    if value != 0:
        msg = "WARNING! perl is not installed on your machine; module 'download' will not work."
        warnings.append(msg)
    return warnings

def gmt_warnings():
    warnings = []
    value = subprocess.call('gmt --version',shell=True,
    stderr=subprocess.STDOUT,
    stdout=subprocess.DEVNULL)
    if value != 0:
        msg = "WARNING! GMT (Generic-mapping-tools) might not be installed on your machine; module 'plot' might not work."
        warnings.append(msg)
    return warnings

def sac_warnings():
    warnings = []
    value = subprocess.call('which sac ',shell=True,
    stderr=subprocess.STDOUT,
    stdout=subprocess.DEVNULL)
    if not os.path.isfile("/usr/local/sac/bin/sac") and value != 0:
        msg = "WARNING! SAC (Seismic Analysis Code) might not be installed on your machine!"
        warnings.append(msg)
    return warnings

def print_warnings():
    warnings = perl_warnings() +\
               gmt_warnings() + \
               sac_warnings()
    warnings = "\n".join(warnings)
    if len(warnings):
        print(f"{warnings}\n")
    else:
        pass

