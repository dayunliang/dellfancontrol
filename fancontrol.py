#!/bin/python
# -*- coding: utf-8 -*-

# Fan Control program for ESXI only - can be modified for any linux
# Must pre-install IPMITOOL vib
# No LANPLUS as doing IPMI on local BMC only
# When doing LANPLUS and remote servers, any netowrk
# issue could cause a system to overheat. Run Localy
#
# WARNING - Temp ranges are specific to the TDP of my CPU
#           Please go to intel ARK for your CPU and check the 
#           TDP (Thermal Design Power) 
#           then subtract about 15 degrees C for returntoauto

# fancontrol.py
# Input - none, paramters are embeded in script
# Output - send all messages to syslog (/var/log/syslog.log)
#          You can use the ESXI GUI and search for fancontrol.py
__author__ = 'Garrett Gauthier'
__copyright__ = 'Copyright 2022, Garrett Gauthier'
__credits__ = ['Garrett Gauthier', 'Others soon?']
__license__ = 'GNU 3.0'
__version__ = '1.0'
__versiondate__ = '10/09/2022'
__maintainer__ = 'gauthig@github'
__github__ = 'https://github.com/gauthig/dellfancontrol'
__status__ = 'Production'


import sys
import re
import os
import time
import subprocess
import syslog

pausetime=10
ipmiexe="/opt/ipmitool/ipmitool" 
temp = 0.0
prevtemp = 0.0
fanmode = "static"
logmsg=""
#User variable based on your system / CPU
#Temps are in Celsius
#To change speed setting, change only the last two digits in hex.
#Speeds are percentage of full power in Hex, i.e 46 = 70% power, 15 = 20%
fanauto="0x30 0x30 0x01 0x01" #Let the BIOS manage fan speed
#fanmanual=["0x30", "0x30", "0x01", "0x00"] #Enable manual/static fan speed
fanmanual=" 0x30 0x30 0x01 0x00 "
returntoauto=62.0   #sets temp to return automatic control to the BIOS
temp1=38.0
temp2=42.0
temp3=48.0
temp4=52.0
fanspeed0="0x30 0x30 0x02 0xff 0x10"  #Default speed
fanspeed1="0x30 0x30 0x02 0xff 0x14"  # Greater than or equal to temp1
fanspeed2="0x30 0x30 0x02 0xff 0x1f"  # Greater than or equal to temp2
fanspeed3="0x30 0x30 0x02 0xff 0x2a"  # Greater than or equal to temp3
fanspeed4="0x30 0x30 0x02 0xff 0x46"  # Greater than or equal to temp4



def autofan():
    subprocess.run(ipmiexe + rawtxt + [hex(fanauto)], capture_output=True)
    return 

def setfanspeed(setspeed):
    #First ensrue IPMI is set to manual/static fan setting
    fanmode = 'static'
    ipmiproc = ipmiexe + " raw " + fanmanual
    p=subprocess.Popen(ipmiproc,  stdout=subprocess.PIPE, shell=True )
    (output, err) = p.communicate()
    p_status = p.wait()

    #Second set the static speed
    ipmiproc = ipmiexe + " raw " + setspeed
    p=subprocess.Popen(ipmiproc,  stdout=subprocess.PIPE, shell=True )
    (output, err) = p.communicate()
    p_status = p.wait()
    logmsg="Detected threshold change from " + str(prevtemp) + "C to " + str(temp) + "C"
    syslog.syslog(syslog.LOG_INFO, logmsg)
    logmsg="Set fanspped to " + setspeed[-4:]
    syslog.syslog(syslog.LOG_INFO, logmsg)
    return

def getcputemp():
    curtemp=0
    try:
        ipmiproc = ipmiexe + " sensor reading Temp"
        p=subprocess.Popen(ipmiproc,  stdout=subprocess.PIPE, shell=True )
        (output, err) = p.communicate()
        p_status = p.wait()
        parsetemp=re.compile('(\d+(\.\d+)?)')
        curtemp=float(parsetemp.search(output.decode()).group())
    except Exception as ipmierror:
            autofan()
            logmsg="Cannot get IPMI temp" 
            syslog.syslog(syslog.LOG_ERR, logmsg)   
    return curtemp

if __name__ == '__main__':
    logmsg="Starting fan control - Interval of " + str(pausetime)
    syslog.syslog(syslog.LOG_INFO, logmsg)
    while True:
        try:
            temp=getcputemp()    
        except Exception as ipmierror:
            autofan()
            logmsg="Cannot get IPMI temp" 
            syslog.syslog(syslog.LOG_ERR, logmsg)

        if temp != prevtemp:
            try:
                if temp >= returntoauto and fanmode == "static":
                    autofan()
                    fanmode = "auto"
                elif temp >= temp4 and prevtemp < temp4:
                    setfanspeed(fanspeed4)
                elif temp >= temp3 and prevtemp < temp3:
                    setfanspeed(fanspeed3)
                elif temp >= temp2 and prevtemp < temp2:
                    setfanspeed(fanspeed2)
                elif temp >= temp1 and prevtemp < temp1:
                    setfanspeed(fanspeed1)
                elif temp < temp1:
                    setfanspeed(fanspeed0)            
            except Exception as ipmierror:
                autofan()
                logmsg="Setting fan speed failed" 
                syslog.syslog(syslog.LOG_ERR, logmsg)   
        prevtemp = temp
        time.sleep(pausetime)

sys.exit()
