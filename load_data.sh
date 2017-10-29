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
OTP_DIR="/srv/vta.amigocloud.com"
DATA_DIR="$OTP_DIR/data"
GTFSM="python $OTP_DIR/gtfs-manager/src/gtfs-manager/gtfsmanager.py"
GTFSM_TEMP_DIR="$OTP_DIR/data_tmp"

# Change working directory to data folder and confirm
cd $DATA_DIR
pwd

# Safely use curl with options to download OpenStreetMap latest map archive with error handling
curl -f -L -w "HTTP Result Code: %{http_code}\nContent-Type: %{content_type}\nFilesize: %{size_download}\nTotal Time: %{time_total}" -o map.osm.bz2 https://s3.amazonaws.com/metro-extracts.mapzen.com/san-francisco-bay_california.osm.bz2
res=$?
if test "$res" != "0"; then
    printf "ERROR Curl fetch of OpenStreetMap failed - exit code: $res"
elif test "$res" == "0"; then
    rm -f map.osm
    bunzip2 map.osm.bz2
    res=$?
    if test "$res" != "0"; then
        printf "ERROR OSM archive is corrupted - exit code: $res"
     	exit $res
    fi
fi

# Change to data tmp directory and confirm
cd $GTFSM_TEMP_DIR
pwd

# Execute GTFS Manager for all agency feeds from config file
$GTFSM -o $DATA_DIR/ ALL ALL

# Change directory to OpenTripPlanner and confirm
cd $OTP_DIR/OTP
pwd

# Java startup configuration for OpenTripPlanner instance
jrun="java -Xmx3G -Xverify:none -jar $OTP_DIR/OTP/target/otp-1.0.0-shaded.jar --build $OTP_DIR/data --cache $OTP_DIR/ned/ --verbose"

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
sudo /usr/bin/supervisorctl restart vta:vta_otp

exit 0
