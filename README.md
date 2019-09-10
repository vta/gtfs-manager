# gtfs-manager
This python script manages GTFS updates by merging the two GTFS feeds. It downloads current GTFS file, compares it with the previous one, that was downloaded before. If the GTFS feed has changed it merges both GTFS files into one, otherwise just keeps the latest one. 

```
Usage: 
  gtfsmanager.py [options] <Provider name | ALL> <GTFS feed URL | ALL>

Options:
  -h, --help                                show this help message and exit
  -o OUTPUT_PATH, --output=OUTPUT_PATH      Output directory for merged GTFS
  ALL ALL                                   ALL Provider Names & URLs from config.json
  ```

## Installtion
1. Create a data and temp directory if non existent:
  ```
mkdir -p /srv/opentripplanner/data && mkdir -p /srv/opentripplanner/data_tmp
  ```
2. Git clone this repository into the working OTP directory eg:
  ```
cd /srv/opentripplanner && git clone https://github.com/vta/gtfs-manager.git 
  ```
3. Create a copy from the config template and edit the file:
  ```
    cd /srv/opentripplaner/gtfs-manager/src/gtfs-manager/
    cp config.tmp.json conifig.json
    vim config.json
  ```
4. Edit the `load_data.sh` script to reflect your directories.
  ```
  vim /srv/opentripplaner/gtfs-manager/load_data.sh
  ```
5. Create a cron job to run nightly when the system less used:
  ```
  sudo vim /etc/crontab
  15 2 * * * otp_user /srv/opentripplaner/gtfs-manager/gtfs-loader.sh
  ```