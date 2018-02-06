#!/bin/bash
MAILTO=""
TIME="\t%E real,\t%U user,\t%S sys,\t%k signals"
/usr/bin/time -a -o /srv/tripplanner/logs/time-`date +%F`.log /bin/bash -x /srv/tripplanner/gtfs-manager/load_data.sh >> /srv/tripplanner/logs/load_data-`date +%F`.log
