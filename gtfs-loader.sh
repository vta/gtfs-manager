#!/bin/bash
MAILTO=""
TIME="\t%E real,\t%U user,\t%S sys,\t%k signals"
/usr/bin/time -a -o /srv/vta.amigocloud.com/logs/time-`date +%F`.log /bin/bash -x /srv/vta.amigocloud.com/gtfs-manager/load_data.sh >> /srv/vta.amigocloud.com/logs/load_data-`date +%F`.log
