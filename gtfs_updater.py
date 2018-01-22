import requests
from datetime import datetime
import os
import tempfile

import logging
from logging.handlers import RotatingFileHandler


API_KEY = '0f516303-aa10-4fa2-a186-295373e2e8df'
base_url = 'https://api.transitfeeds.com/v1/'


def download_file(url, local_filename):
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_filename

def update_gtfs(agency, dl_url):
    print(agency, dl_url)
    download_file(dl_url, 'data/' + agency+'_gtfs.zip')


if __name__ == "__main__":


    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler('gtfs_update.log', maxBytes=10*1024*1024, backupCount = 10)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # # define a Handler which writes INFO messages or higher to the sys.stderr
    # console = logging.StreamHandler()
    # console.setLevel(logging.ERROR)

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    updated = False
    present = datetime.now()

    config_file = 'config'
    with open(config_file) as f:
        processed_lines = f.read().splitlines()

    tmp = tempfile.NamedTemporaryFile(dir='.', delete=False)
    sub_url = 'getFeedVersions'

    for line in processed_lines:
        agency, agency_id, most_recent = line.split(' ')
        logger.debug('Managing ' + agency + " gtfs.")
        print(agency_id)
        most_recent = int(most_recent)
        payload = {'key': API_KEY, 'feed':agency_id}
        r = requests.get(base_url + sub_url, params=payload)
        # r.json()

        for version in r.json()['results']['versions']:
            s_date = version['d']['s']
            f_date = version['d']['f']

            #     print(version['id'])
            # Is the feeds time before the present?  Is it valid?
            if (datetime(int(s_date[0:4]), int(s_date[4:6]), int(s_date[6:8])) < present and
               datetime(int(f_date[0:4]), int(f_date[4:6]), int(f_date[6:8]), 23) > present):
                print('Valid Feed')
                logger.debug('This ' + agency + " feed is valid")
            #  print(version['ts'])

                if(version['ts'] > most_recent):
                    logger.debug('This ' + agency + " feed is more recent.  Updating.")
                    most_recent = version['ts']
                    print('more_recent')
                    dl_url = version['url']
                    most_recent_id = version['id']        
                    update_gtfs(agency, dl_url)
                    updated = True
                else:
                    print('less recent')
                    logger.debug('This ' + agency + " feed is less recent.  Not updating.")
            else:
                print('Invalid Feed')
                logger.debug('This' + agency + "feed is invalid")
        line = agency + ' ' + agency_id + ' '+ str(most_recent) + '\n'
        tmp.write(line.encode())
    tmp.close()
    logger.debug('Updating config file.')
    os.replace(tmp.name, 'config')

    if(updated):
        print('update otp')