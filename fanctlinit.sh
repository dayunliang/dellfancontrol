#!/bin/sh
#
#service init script for /opt/fanctl/fanctl.py
#
#github repo - https://github.com/gauthig/dellfanctl
#Version  1.0

PIDFILE="/var/run/fanctl.pid"
fanctl="/opt/fanctl/fanctl.py"
LOGFILE="/var/log/fanctl.log"

log() {
   echo "$1"
   logger -t NUT "$1"
}

start() {
   if [ ! -f "${PIDFILE}" ]; then
      "${fanctl}" > "${LOGFILE}" 2>&1 &        
      PID="$!"
      if [ -n "${PID}" ]; then
          if (echo "${PID}" > "${PIDFILE}"); then
              log "fanctl started"
          else
              kill -USR1 "${PID}"
              log "fanctl unable to create pid file"
          fi
      fi
   else
        PID="$(cat "${PIDFILE}")"
        if (ps aux 2> /dev/null || ps) | grep -q "${PID}"; then
             log "fanctl is already running"
         else                     
             rm -f "${PIDFILE}"            
             start
         fi  
   fi
}

stop() {
   if [ -f "${PIDFILE}" ] ; then
      PID="$(cat "${PIDFILE}")"
      kill -USR1 "${PID}" && \
      rm -f "${PIDFILE}"
   else
      log "fanctl is not running"
   fi
}

case "${1}" in
   "start")
      start
   ;;
   "stop")
      stop
   ;;
   "status")
      if [ -f "${PIDFILE}" ] ; then
         PID="$(cat "${PIDFILE}")"
         if (ps aux 2> /dev/null || ps) | grep -q "${PID}"; then
             log "fanctl is running, pid ${PID}"
         else
             rm -f "${PIDFILE}"
             log "fanctl terminated for unknown cause"
         fi
         exit 0
      else
         log "fanctl not running"
         exit 3
      fi
   ;;
   "restart")
      stop
      start
   ;;
   *)
      echo "Usage: $(basename "${0}") {start|stop|status|restart}"
      exit 1
   ;;
esac
