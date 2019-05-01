#!/bin/bash
###
#
# GTFS Manager Load Data and Rebuild OpenTripPlanner Graph object daily script
#
# @author LinuxWebExpert - see GitHub
# @date 10/01/2017
# @see https://github.com/vta/
#
###
MAILTO=""
OTP_DIR="/srv/tripplanner"
DATA_DIR="$OTP_DIR/data"
GTFSM="python $OTP_DIR/gtfs-manager/src/gtfs-manager/gtfsmanager.py"
GTFSM_TEMP_DIR="$OTP_DIR/data_tmp"

# Change working directory to data folder and confirm
cd $DATA_DIR
pwd

# Safely use curl with options to download OpenStreetMap latest map archive with error handling
#

# NO - wrong - don't use static maps - give the public the latest data...
# Reverting since it's obvious it's been baked into the code :(
# 
# Meeting set to address this issue and find proper solution
#
curl -f -L -w "HTTP Result Code: %{http_code}\nContent-Type: %{content_type}\nFilesize: %{size_download}\nTotal Time: %{time_total}" -o map.osm.bz2 https://s3-us-west-2.amazonaws.com/gis-busstops-inventory/OSM+bayarea+network+older+prod+version/map.osm.bz2

##
# Correct way to do it...
# Or at least we thought..
#
# https://download.geofabrik.de/north-america/us/california-latest.osm.bz2
#
# And tried...
#
#wget -c https://openmaptiles.com/download/WyJjMGYzYjk4Yy1iYjU4LTQ5ZGItOWYzZi0zNjRiZDQxZGJhYWEiLCItMSIsODY3NV0.D6oTYA.2RDL0eOy6PmFo0dpTWPhTeNOspE/osm-2017-07-03-v3.6.1-california_san-francisco-bay.mbtiles?usage=open-source
#
# And tried really hard too...
#
#https://download.geofabrik.de/north-america/us/california/norcal-latest.osm.bz2
#
# Sadly all the kings horses...
#
#curl -f -L -w "HTTP Result Code: %{http_code}\nContent-Type: %{content_type}\nFilesize: %{size_download}\nTotal Time: %{time_total}" -o map.osm.bz2 https://download.geofabrik.de/north-america/us/california/norcal-latest.osm.bz2
#
# And all the kings men...
#
#curl -f -L -w "HTTP Result Code: %{http_code}\nContent-Type: %{content_type}\nFilesize: %{size_download}\nTotal Time: %{time_total}" -o map.osm.bz2 https://openmaptiles.com/download/WyJjMGYzYjk4Yy1iYjU4LTQ5ZGItOWYzZi0zNjRiZDQxZGJhYWEiLCItMSIsODY3NV0.D6oTYA.2RDL0eOy6PmFo0dpTWPhTeNOspE/osm-2017-07-03-v3.6.1-california_san-francisco-bay.mbtiles?usage=open-source
#
# Could not put humpty dumpty...
#
#curl -f -L -w "HTTP Result Code: %{http_code}\nContent-Type: %{content_type}\nFilesize: %{size_download}\nTotal Time: %{time_total}" -o map.osm.bz2 https://download.geofabrik.de/north-america/us/california-latest.osm.bz2
#
# Back together again! :(
#
##
#last=`date -R | sed 's/\+0000/GMT/'`
#
#curl -f -L -w "HTTP Result Code: %{http_code}\nContent-Type: %{content_type}\nFilesize: %{size_download}\nTotal Time: %{time_total}" --header "If-Modified-Since: $last" -o map.osm.bz2 https://download.geofabrik.de/north-america/us/california-latest.osm.bz2
#
# Be a pro - don't be a bro!
#
####
res=$?
if test "$res" != "0"; then
    printf "ERROR Curl fetch of OpenStreetMap failed - exit code: $res"
elif test "$res" == "0"; then
	minimumsize=100
	actualsize=$(du -k "map.osm.bz2" | cut -f 1)
	if [ $actualsize -ge $minimumsize ]; then
		rm -f map.osm
		bunzip2 map.osm.bz2
		res=$?
		if test "$res" != "0"; then
			printf "ERROR OSM archive is corrupted - exit code: $res"
			exit $res
		fi
	fi
fi

# Change to data tmp directory and confirm
cd $GTFSM_TEMP_DIR
pwd

# Execute GTFS Manager for all agency feeds from config file
$GTFSM -o $DATA_DIR/ ALL ALL

# Change directory to OpenTripPlanner and confirm
cd $OTP_DIR/otp
pwd

##
# Java startup configuration for OpenTripPlanner instance
#
# Increased memory to 4G to handle more transitfeeds and graph objects
##
jrun="java -Xmx4G -Xverify:none -jar $OTP_DIR/otp/otp-1.2.0-shaded.jar --build $OTP_DIR/data/ --cache $OTP_DIR/otp/ned --verbose"

# Captures today's date for log file
now=`date +%F`

# Execute Java OpenTripPlanner rebuild of Graph.obj with a log handler
$jrun
res=$?
echo "JRUN RESULT CODE: $res\n"
if test "$res" != "0"; then
    printf "ERROR Java build of Graph.obj failed - exit code: $res"
else
    # Copy the new Graph.obj to OpenTripPlanner default directory
    cp -v $DATA_DIR/Graph.obj $DATA_DIR/graphs/default/
    res=$?
    if test "$res" != "0"; then
        printf "ERROR Cannot copy new Graph.obj to default directory - exit code: $res"
    fi
fi

# Restart the supervisor service to reload the new Graph.obj
/usr/bin/supervisorctl restart vta:vta_otp

exit 0
