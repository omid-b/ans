import os
import sys
import subprocess

def perl_warnings():
    warnings = []
    value = subprocess.call('perl --version',shell=True,
    stderr=subprocess.STDOUT,
    stdout=subprocess.DEVNULL)
    if value != 0:
        msg = "WARNING! command 'perl' is not recognized on this terminal enviroment."
        warnings.append(msg)
    return warnings

def gmt_warnings():
    warnings = []
    value = subprocess.call('gmt --version',shell=True,
    stderr=subprocess.STDOUT,
    stdout=subprocess.DEVNULL)
    if value != 0:
        msg = "WARNING! command 'gmt' is not recognized on this terminal enviroment."
        warnings.append(msg)
    return warnings

def sac_warnings():
    warnings = []
    value = subprocess.call('which sac ',shell=True,
    stderr=subprocess.STDOUT,
    stdout=subprocess.DEVNULL)
    if value != 0:
        msg = "WARNING! command 'sac' is not recognized on this terminal enviroment."
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

