from gtfsmerge import *
import hashlib
import urllib2
# import shelve
import shutil
import os.path
import logging
import json

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

def main():
    """Run the merge driver program."""
    usage = \
    """%prog [options] <Provider name> <GTFS feed URL>

    For more information see
    https://github.com/vta/gtfs-manager
    """

    parser = util.OptionParserLongError(usage=usage)
    parser.add_option('-o', '--output', dest='output_path', default='./',
                      help=' Output directory for merged GTFS')
    (options, args) = parser.parse_args()

    if len(args) < 2:
        parser.error('You did not provide all required command line arguments.')
    else:
        if args[0] == 'ALL' and args[1] == 'ALL':
            gtfsm = GTFSManager(args[0],options.output_path)
            agencies = gtfsm.config['gtfs_agencies']
            for x in range(len(agencies)):
                gtfsm.agency = agencies[x]['agency']
                gtfsm.url = agencies[x]['url']
                gtfsm.setpath(options.output_path)
                gtfsm.logger.info('Managing GTFS feed for ' + gtfsm.agency)
                gtfsm.merge(gtfsm.url)
        else:
            gtfsm = GTFSManager(args[0], options.output_path);
            gtfsm.logger.info('Managing GTFS feed for ' + args[0])
            gtfsm.merge(args[1])

if __name__ == '__main__':
  util.RunWithCrashHandler(main)
