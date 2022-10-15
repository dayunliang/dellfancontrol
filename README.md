# Fan Control program for Dell servers
Another Dell IPMI Fan Control Script, 5 settings, both ESXI and Linux hosts
 

## WARNING - Temp ranges are specific to the TDP of my CPU
<br>          Please go to intel ARK for your CPU and check the 
<br>          TDP (Thermal Design Power) 
<br>          then subtract about 20-10 degrees C for returntoauto
<br>          this allows the BIOS to manage high temps
##        tested on R630 with e5-2697a V4

## Still in progress - here is what is completed and works

Features
- [X] Two versions, one for running directly on ESXI server and one for any linux host/guest
- [X] Exapnd to 5 temp settings
- [X] Retuturn to BIOS DELL BIOS/IPMI control when a threashold is reached
- [X] ESXI specifc INIT file for stop/start/status/reload
- [X] Output goes to syslog
- [X] aded PID file
- [ ] Temp, ID, Server  and other parms in a json file
- [ ] init script for systemd 
- [X] PEP 8 style guide

## Requirements
- Must have IPMITOOL installed
<br> ubuntu/debian apt install ipmitool -y
<br> ESXI - must find and install ipmitool vib and install.  usaly in /opt/ipmitool
<br>PIP is not required, using standard python libaries


## Usage
Modify the use paramters in the .py file
### Linux
     /fanctl.py
or
    add a cron file using crontab -e
    @reboot /usr/bin/python3 /home/installeddir/fanctl.py
<br>
### ESXI
put both esxifanctl.py and fanctlinit.sh int the same directory (maybe /opt/fanctl)
chmod +x fanctlinit.sh esxifanctl.py
./fanctl start

## Output of program 
All output is directed to syslog or syslog.log (esxi)
<br><b>start message</b> 
<br><b>temp threshold change messages with fan speed in hex</b> 

