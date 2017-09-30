#!/bin/bash
OTP_DIR="/srv/vta.amigocloud.com"
DATA_DIR="$OTP_DIR/data"
GTFSM="python $OTP_DIR/gtfs-manager/src/gtfs-manager/gtfsmanager.py"
GTFSM_TEMP_DIR="$OTP_DIR/data_tmp"

cd $DATA_DIR

# OSM DATA for SF Bay Area
#curl -L -o map.osm.bz2 https://s3.amazonaws.com/metro-extracts.mapzen.com/san-francisco-bay_california.osm.bz2
#rm -f map.osm
#bunzip2 map.osm.bz2

cd $GTFSM_TEMP_DIR

pwd

$GTFSM -o $DATA_DIR/ ALL ALL

# VTA. use Google file instead
#$GTFSM -o $DATA_DIR/ VTA http://www.vta.org/sfc/servlet.shepherd/document/download/069A0000001NUea
#$GTFSM -o $DATA_DIR/ VTA http://transitfeeds.com/p/vta/45/latest/download

#Caltrain
#$GTFSM -o $DATA_DIR/ Caltrain http://transitfeeds.com/p/caltrain/122/20170324/download

# BART
#$GTFSM -o $DATA_DIR/ BART http://transitfeeds.com/p/bart/58/latest/download

# Golden Gate Transit
#$GTFSM -o $DATA_DIR/ GGT http://transitfeeds.com/p/golden-gate-bridge-highway-transportation-district/349/latest/download
#$GTFSM -o $DATA_DIR/ SFFarries http://transitfeeds.com/p/golden-gate-bridge-highway-transportation-district/344/latest/download

#samTrans
#$GTFSM -o $DATA_DIR/ samTrans http://transitfeeds.com/p/samtrans/144/latest/download

#Marin Transit
#$GTFSM -o $DATA_DIR/ Marin http://transitfeeds.com/p/marin-transit/345/latest/download

#Sonoma County
#$GTFSM -o $DATA_DIR/ Sonoma http://transitfeeds.com/p/sonoma-county-transit/419/latest/download

# AC Transit
#$GTFSM -o $DATA_DIR/ ACTransit http://transitfeeds.com/p/ac-transit/121/latest/download


# Santa Cruz
#$GTFSM -o $DATA_DIR/ SantaCruz http://transitfeeds.com/p/santa-cruz-metro/343/latest/download

# SF Muni (same as SFMTA?)
#$GTFSM -o $DATA_DIR/ SFMuni http://transitfeeds.com/p/sfmta/60/latest/download

#County Connection
#$GTFSM -o $DATA_DIR/ CountyConnection http://transitfeeds.com/p/county-connection/222/latest/download

# San Benito County
#$GTFSM -o $DATA_DIR/ SanBenito http://transitfeeds.com/p/san-benito-county-express/491/latest/download

#Stanford Marguerite Shuttle
#$GTFSM -o $DATA_DIR/ StanfordMarguerite https://transportation-forms.stanford.edu/google/google_transit.zip

#ACE Transit
#$GTFSM -o $DATA_DIR/ ACE "http://api.511.org/transit/datafeeds?api_key=ac488e3a-7283-44be-b910-24fd237a5abb&operator_id=CE"

#Capitol Cooridoor
#$GTFSM -o $DATA_DIR/ CC "http://api.511.org/transit/datafeeds?api_key=ac488e3a-7283-44be-b910-24fd237a5abb&operator_id=CC"

cd $OTP_DIR/OTP

pwd
jrun="java -Xmx3G -Xverify:none -jar $OTP_DIR/OTP/target/otp-1.0.0-shaded.jar --build $OTP_DIR/data --cache $OTP_DIR/ned/ --verbose"
now=`date +%F`
$jrun 2>&1 | tee $OTP_DIR/logs/otp_output-$now\.log



mv $DATA_DIR/Graph.obj $DATA_DIR/graphs/default/

#sudo /usr/bin/supervisorctl restart vta:vta_otp &

exit

