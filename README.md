
# Fan Control program for Dell servers
Another Dell IPMI Fan Control Script, 5 settings, both ESXI and Linux hosts
Service scritps for either systemd or SysV
 

## WARNING - Temp ranges are specific to the TDP of my CPU
<pre>
<br>          Please go to intel ARK for your CPU and check the 
<br>          TDP (Thermal Design Power) 
<br>          then subtract about 20-10 degrees C for returntoauto
<br>          this allows the BIOS to manage high temps
<br>          tested on R630 with e5-2697a V4
<br>          Monitor the temps and speeds to fine tune your system
<br>          on systemd just use journalctl -t fanctl to see what temp changes are triggered
</pre>
## Still in progress - here is what is completed and works

Features
- [X] Two versions, one for running directly on ESXI server and one for any linux host/guest
- [X] Exapnd to 5 temp settings
- [X] Retuturn to BIOS DELL BIOS/IPMI control when a threashold is reached
- [X] ESXI specifc INIT file for stop/start/status/reload
- [X] Output goes to syslog
- [X] aded PID file
- [ ] Temp, ID, Server  and other parms in a json file
- [X] init script for systemd 
- [X] PEP 8 style guide

## Requirements
- Must have IPMITOOL installed
<br> ubuntu/debian apt install ipmitool -y
<br> ESXI - must find and install ipmitool vib and install.  usaly in /opt/ipmitool
<br>PIP is not required, using standard python libaries


## Usage
Modify the use paramters in the .py file
### Linux
     Manualy just run fanctl.py to test (python3 ./fancctl.py)

<br>

### Systemd  - Setup as a service
<br>
<br>DO NOT USE rc.local if your system is systemd, upgrade to current stack
<pre>
<br>Install fanctl.service to /etc/systemd/service
<br>Install fanctl.py /root or anywhere you want to place this script
<br>If you chagned the install from /root, then update the fanctl.service to correct location

<br>Reload the service files to include the new service.
<br>    sudo systemctl daemon-reload
- Start your service
<br>    sudo systemctl start your-service.service
- To check the status of your service
<br>    sudo systemctl status example.service
- To enable your service on every reboot
<br>    sudo systemctl enable example.service
<br>
</pre>
Modify the after section to a servcie you want to start after.  This is setup for Proxmox ()
<br>

### ESXI
<br>Put both esxifanctl.py and fanctlinit.sh int the same directory (maybe /opt/fanctl)
<br>chmod +x fanctlinit.sh esxifanctl.py
<br>./fanctl start
### SysV - old school
<br>Install fanctlinit.sh to /etc/rc.local

## Output of program 
<br>All output is directed to syslog or syslog.log (esxi)
<br><b>start message</b> 
<br><b>temp threshold change messages with fan speed in hex</b> 

