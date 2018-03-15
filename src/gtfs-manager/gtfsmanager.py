#!/usr/bin/python2.7
from gtfsmerge import *
import hashlib, tempfile, urllib2, shutil, os.path, logging, json, requests
from logging.handlers import RotatingFileHandler
from datetime import datetime
# For CHMOD
from stat import S_IREAD, S_IRGRP, S_IROTH
###################################################3
# Python3 NOT supported
# Purpose of this script it to download GTFS feeds based on the config file
# Only downloads feeds which are valid and recent.
#### PIP Installs: #########################
# pip install transitfeed datetime requests
############################################
# TransitFeed Info ######################################
API_KEY = '0f516303-aa10-4fa2-a186-295373e2e8df'
base_url = 'https://api.transitfeeds.com/v1/'
gtfs_arr = []
#########################################################

class GTFSManager:
    def __init__(self, name, path):

        # Initialize logging
        self.logfile()

        # Load config file with agencies
        self.config = self.load_config()

        # Check if ALL is true and loop and agencies
        if name is 'ALL' and url is 'ALL':
            self.data = []
            self.setpath(path)
            self.url = None
            self.agency = None
            return None
        elif (name is not None) and (path is not None):
            self.data = []
            self.agency = name
            self.url = None
            self.setpath(path)
            return None
        else:
            self.logger.error('Agency name and URL path not set!')
            return None

    def setpath(self, path):
        self.current_fname = 'gtfs_' + self.agency + '_current.zip'
        self.stored_fname = 'gtfs_' + self.agency + '_old.zip'
        self.merged_fname = path + 'gtfs_' + self.agency + '_merged.zip'
        self.html_output_path = 'merge-results_' + self.agency+ '.html'



    def load_config(self):
        directory = '/srv/tripplanner/gtfs-manager/src/gtfs-manager'
        filename = directory + '/config.json'
        if os.path.isfile(filename):
            with open(filename) as json_data:
                config = json.load(json_data)
                json_data.close()
            if len(config['gtfs_agencies']) > 0:
                self.config = config
                return config
        else:
            self.logger.error("Could not load config.json file")
            return False

    def logfile(self):
        # create a logging instance
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # create a file handler
        handler = logging.FileHandler('gtfs-manager.log')
        handler.setLevel(logging.INFO)

        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # add the handlers to the logger
        self.logger.addHandler(handler)

        # define a Handler which writes INFO messages or higher to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(logging.ERROR)

        # set a format which is simpler for console use
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)-8s %(message)s')

        # tell the handler to use this format
        console.setFormatter(formatter)

        # add the handler to the root logger
        self.logger.addHandler(console)

    def download_gtfs(self, filename, url):
        request = urllib2.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')

        try:
            zipfile = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            self.logger.error(self.name + ' - HTTPError = ' + str(e.code))
            return False
        except urllib2.URLError, e:
            self.logger.error(self.name + ' - URLError = ' + str(e.reason))
            return False
        except httplib.HTTPException, e:
            self.logger.error(self.name + ' - HTTPException')
            return False
        except Exception:
            import traceback
            self.logger.error(self.name + ' - Generic exception: ' + traceback.format_exc())
            return False
        output = open(filename,'wb')
        output.write(zipfile.read())
        output.close()
        self.logger.info('Successfully downloaded ' + filename + ' for ' + self.agency)
        return True

    def merge_gtfs(self, old_feed_path, new_feed_path, merged_feed_path):
        mem_db = True
        latest_version = None
        largest_stop_distance = 10
        largest_shape_distance = 10
        cutoff_date = None
        a_schedule = LoadWithoutErrors(old_feed_path, mem_db)
        b_schedule = LoadWithoutErrors(new_feed_path, mem_db)
        merged_schedule = transitfeed.Schedule()
        accumulator = HTMLProblemAccumulator()
        problem_reporter = MergeProblemReporter(accumulator)
        util.CheckVersion(problem_reporter, latest_version)

        feed_merger = FeedMerger(a_schedule, b_schedule, merged_schedule, problem_reporter)
        feed_merger.AddDefaultMergers()

        feed_merger.GetMerger(StopMerger).SetLargestStopDistance(float(largest_stop_distance))
        feed_merger.GetMerger(ShapeMerger).SetLargestShapeDistance(float(largest_shape_distance))

        if cutoff_date is not None:
            service_period_merger = feed_merger.GetMerger(ServicePeriodMerger)
            service_period_merger.DisjoinCalendars(cutoff_date)

        if feed_merger.MergeSchedules():
            feed_merger.GetMergedSchedule().WriteGoogleTransitFeed(merged_feed_path)
        else:
            merged_feed_path = None

        output_file = file(self.html_output_path, 'w')
        accumulator.WriteOutput(output_file, feed_merger, old_feed_path, new_feed_path, merged_feed_path)
        output_file.close()

    def compare_files(self, fname1, fname2):
        hash1 = hashlib.md5(open(fname1, 'rb').read()).hexdigest()
        hash2 = hashlib.md5(open(fname2, 'rb').read()).hexdigest()
        if hash1 == hash2:
            return True
        else:
            return False

    def is_gtfs_changed(self):
        if self.compare_files(self.stored_fname, self.current_fname):
            return False
        else:
            return True

    def merge(self, url):
        if not self.download_gtfs(self.current_fname, url):
            logging.error("Failed to download " + self.current_fname + " GTFS data from " + url)
            return False
        if os.path.isfile(self.stored_fname):
            if self.is_gtfs_changed():
                self.logger.info('Merging ' + self.current_fname + ' for ' + self.agency)
                if os.path.isfile(self.merged_fname):
                    os.remove(self.merged_fname)
                    self.merge_gtfs(self.stored_fname, self.current_fname, self.merged_fname)
                    shutil.copy2(self.current_fname, self.stored_fname)
                else:
                    if not os.path.isfile(self.merged_fname):
                        shutil.copy2(self.current_fname, self.merged_fname)
        else:
            shutil.copy2(self.current_fname, self.stored_fname)
            shutil.copy2(self.current_fname, self.merged_fname)
        return True

def download_file(url, local_filename):
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_filename
######################
# @Info This checks the transitfeeds being downloaded via transitfeed api
#       If the feed is the latest and not currently valid ignore
#       If the feed is the latest and VALID add to array and use in merge
######################
def download_active():
    ## Setup the logger which will be logging to gtfs_update.log
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler('gtfs_update.log', maxBytes=10*1024*1024, backupCount = 10)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    ##########################################################################
    ## Get the current Date / Time
    present = datetime.now()
    ## Location of the config file which contains:
    # 1. Agency Name
    # 2. Agency ID
    # 3. Version Number
    config_file = '/srv/tripplanner/gtfs-manager/config'
    ## Open the config file and split each line into the above parameters
    with open(config_file) as f:
        ## Store feed information into processed_lines
        processed_lines = f.read().splitlines()
    tmp = tempfile.NamedTemporaryFile(dir='/srv/tripplanner/gtfs-manager', delete=False)
    sub_url = 'getFeedVersions'
    ## Loop through each agency via the config file
    for line in processed_lines:
        # Values stored within the config file separated by spaces
        agency, agency_id, most_recent = line.split(' ')
        logger.debug('Managing ' + agency + " gtfs.")
        most_recent = int(most_recent)
        payload = {'key': API_KEY, 'feed':agency_id}
        r = requests.get(base_url + sub_url, params=payload)
        # r.json()
        # Keep track of valid / invalid feeds per agency
        invalid_feeds = 0
        valid_feeds = 0
        ## Go through the different versions of the feeds
        for version in r.json()['results']['versions']:
            s_date = version['d']['s']
            f_date = version['d']['f']

            #     print(version['id'])
            # Is the feeds time before the present?  Is it valid?
            if (datetime(int(s_date[0:4]), int(s_date[4:6]), int(s_date[6:8])) < present and datetime(int(f_date[0:4]), int(f_date[4:6]), int(f_date[6:8]), 23) > present):
                valid_feeds += 1
                logger.debug('This ' + agency + " feed is valid")
                #  print(version['ts'])

                if(version['ts'] > most_recent):
                    logger.debug('This ' + agency + " feed is more recent.  Updating.")
                    most_recent = version['ts']
                    dl_url = version['url']
                    most_recent_id = version['id']
                    gtfs_arr.append([agency, dl_url])
                    print "ID: " + most_recent_id + " - - - URL: " + dl_url + " - - - UPDATED - - - :)"
                else:
                    logger.debug('This ' + agency + " feed is less recent.  Not updating.")
            else:
                invalid_feeds += 1
                logger.debug('This' + agency + "feed is invalid")
        # Display how many feeds were valid and invalid per agency
        print 'Valid Feeds: {0}'.format(valid_feeds)
        print 'Invalid Feeds: {0}'.format(invalid_feeds)
        # This is what will be replaced within the config file
        line = agency + ' ' + agency_id + ' ' + str(most_recent) + '\n'
        tmp.write(line.encode())
    tmp.close()
    os.chmod(tmp.name, S_IREAD|S_IRGRP|S_IROTH)
    os.rename(tmp.name, '/srv/tripplanner/gtfs-manager/config')
    print 'UPDATED: /srv/tripplanner/gtfs-manager/config'


def main():
    """Run the merge driver program."""
    usage = \
    """%prog [options] <Provider name> <GTFS feed URL>

    For more information see
    https://github.com/vta/gtfs-manager
    """

    parser = util.OptionParserLongError(usage=usage)
    parser.add_option('-o', '--output', dest='output_path', default='./', help=' Output directory for merged GTFS')
    # This will pull only active Feeds from TransitFeed via the API
    # Checks dates and ensures that only a VALID feed is being downloaded
    download_active()
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error('You did not provide all required command line arguments.')
    else:
        if args[0] == 'ALL' and args[1] == 'ALL':
            gtfsm = GTFSManager(args[0],options.output_path)
            #agencies = gtfsm.config['gtfs_agencies']
            for x in gtfs_arr:
                c = 0
                for z in x:
                    c += 1
                    if c == 1:
                        gtfsm.agency = z
                    else:
                        gtfsm.url = z
                #print "Agency: " + gtfsm.agency + "GTFSM URL: " + "[ " + x + " ]" + gtfsm.url
                gtfsm.setpath(options.output_path)
                gtfsm.logger.info('Managing GTFS feed for ' + gtfsm.agency)
                gtfsm.merge(gtfsm.url)
        else:
            gtfsm = GTFSManager(args[0], options.output_path)
            gtfsm.logger.info('Managing GTFS feed for ' + args[0])
            gtfsm.merge(args[1])

if __name__ == '__main__':
  util.RunWithCrashHandler(main)
