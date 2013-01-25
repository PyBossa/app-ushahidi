#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2013 Citizen Cyberscience Centre
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import copy
import csv
import sys
import time
import datetime
from optparse import OptionParser
from collections import Counter
from pymongo import MongoClient

import pbclient

from daemon import Daemon

def format_csv_row(t, a):
    line = []
    if t.id:
        line.append(t.id)
    else:
        line.append("")

    if t.info['incident']['id']:
        line.append(t.info['incident']['id'].encode('utf-8', 'ignore'))
    else:
        line.append("")

    if t.info['incident']['title']:
        line.append(t.info['incident']['title'].encode('utf-8', 'ignore'))
    else:
        line.append("")

    if t.info['incident']['date']:
        line.append(t.info['incident']['date'].encode('utf-8', 'ignore'))
    else:
        line.append("")

    if t.info['incident']['location']:
        line.append(t.info['incident']['location'].encode('utf-8', 'ignore'))
    else:
        line.append("")

    if t.info['incident']['description']:
        line.append(t.info['incident']['description'].encode('utf-8', 'ignore'))
    else:
        line.append("")

    # Answers
    if a.info['category']:
        line.append(a.info['category'])
    else:
        line.append(0)

    if a.info['latitude']:
        line.append(a.info['latitude'])
    else:
        line.append("")

    if a.info['longitude']:
        line.append(a.info['longitude'])
    else:
        line.append(0)

    if a.info['approved']:
        line.append(a.info['approved'].encode('utf-8', 'ignore'))
    else:
        line.append("")

    if a.info['verified']:
        line.append(a.info['verified'])
    else:
        line.append(0)

    return line


class my_daemon(Daemon):
    options = None

    def run(self):
        # Configure client
        print "Running"
        if not self.options.api_url:
            self.options.api_url = 'http://localhost:5000'

        pbclient.set('endpoint', self.options.api_url)

        if not self.options.api_key:
            parser.error("You must supply an API-KEY to create an applicationa and tasks in PyBossa")
        else:
            pbclient.set('api_key', self.options.api_key)

        if (self.options.verbose):
            print('Running against PyBosssa instance at: %s' % self.options.api_url)
            print('Using API-KEY: %s' % self.options.api_key)

        if (self.options.app):
            app_name = self.options.app
        else:
            app_name = 'ushahidi'

        if (self.options.results):
            app = pbclient.find_app(short_name=app_name)[0]

        # Connect to the server
        connection = MongoClient('localhost', 27017)

        # Create DB
        db = connection[app_name]
        # Now get the task runs
        print "Creating CSV file"
        with open("/tmp/results.csv", "a+b") as myfile:
            f = csv.writer(myfile)
            f.writerow(['taskid',
                        'incident id',
                        'incident title',
                        'incident date',
                        'location',
                        'description',
                        'category',
                        'latitude',
                        'longitude',
                        'approved',
                        'verified'])
            while True:
                # Do stuff
                offset = 0
                limit = 100
                if self.options.completed:
                    completed_tasks = pbclient.find_tasks(app.id,
                                                          state="completed",
                                                          offset=offset,
                                                          limit=limit)
                else:
                    completed_tasks = pbclient.find_tasks(app.id,
                                                          offset=offset,
                                                          limit=limit)



                while completed_tasks:
                    for t in completed_tasks:
                        db_task = db.tasks.find_one({"id": t.id,
                                                     "state": "completed"})
                        if db_task:
                            if db_task['saved'] == 0:
                                print "Getting answers for task %s: " % t.id
                                answers = pbclient.find_taskruns(app.id, task_id=int(t.id))

                                if self.options.average:
                                    canonical_answer = copy.deepcopy(answers[0])
                                    canonical_answer.task_id = t.id
                                    canonical_answer.id = 0
                                    canonical_answer.info['category'] = None
                                    canonical_answer.info['location'] = None
                                    canonical_answer.info['latitude'] = None
                                    canonical_answer.info['longitude'] = None
                                    # First Categories and sub-categories
                                    most_common_category = "No canonical result"
                                    most_common_sub_category = None
                                    categories = []
                                    for a in answers:
                                        for cat in a.info['category'].keys():
                                            categories.append(cat)
                                    c = Counter(categories)
                                    if c.most_common()[0][1] >= 2:
                                        most_common_category = c.most_common()[0][0]
                                        sub_categories = []
                                        for a in answers:
                                            for cat in a.info['category'].keys():
                                                if cat == most_common_category:
                                                    for sc in a.info['category'][cat]['sub-categories']:
                                                        sub_categories.append(sc)
                                        c2 = Counter(sub_categories)
                                        if c2.most_common()[0][1] >= 2:
                                            most_common_sub_category = [c2.most_common()[0][0]]
                                        else:
                                            most_common_sub_category = list(c2)
                                    sub_categories = {'sub-categories':
                                                      most_common_sub_category}
                                    canonical_answer.info['category'] = {
                                        most_common_category: sub_categories}

                                    # Second the Location
                                    most_common_location = "No canonical result"
                                    locations = []
                                    for a in answers:
                                        locations.append(a.info['location'])
                                    c = Counter(locations)
                                    if c.most_common()[0][1] >= 2:
                                        most_common_location = c.most_common()[0][0]
                                    canonical_answer.info['location'] = most_common_location

                                    # Third the Latitude and Longitude
                                    latitudes = []
                                    longitudes = []
                                    for a in answers:
                                        latitudes.append(float(a.info['latitude']))
                                        longitudes.append(float(a.info['longitude']))
                                    most_common_latitude = float( sum(latitudes)/len(latitudes))
                                    most_common_longitude = float( sum(longitudes)/len(longitudes))
                                    canonical_answer.info['latitude'] = most_common_latitude
                                    canonical_answer.info['longitude'] = most_common_longitude
                                    line = format_csv_row(t,canonical_answer)
                                    print "saving answer"
                                    f.writerow(line)
                                    db_task['saved'] = 1
                                    db.tasks.save(db_task)
                                else:
                                    for a in answers:
                                        print "saving answer"
                                        line = format_csv_row(t, a)
                                        f.writerow(line)
                                        db_task['saved'] = 1
                                        db.tasks.save(db_task)
                        else:
                            db.tasks.insert({"id": t.id,
                                             "date": datetime.datetime.utcnow(),
                                             "state": t.state,
                                             "saved": 0})
                    offset = offset + limit
                    if self.options.completed:
                        completed_tasks = pbclient.find_tasks(app.id,
                                                              state="completed",
                                                              offset=offset,
                                                              limit=limit)
                    else:
                        completed_tasks = pbclient.find_tasks(app.id,
                                                              offset=offset,
                                                              limit=limit)

                myfile.flush()
                time.sleep(10)

if __name__ == "__main__":
    daemon = my_daemon('/tmp/daemon-example.pid', stdout="/tmp/out.txt", stderr="/tmp/err.txt")
    # Arguments for the application
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)

    parser.add_option("-s", "--url", dest="api_url", help="PyBossa URL http://domain.com/", metavar="URL")
    parser.add_option("-k", "--api-key", dest="api_key", help="PyBossa User API-KEY to interact with PyBossa", metavar="API-KEY")
    parser.add_option("-r", "--results", dest="results", action="store_true",
                      help="Create the application",
                      metavar="RESULTS")

    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
    parser.add_option("-c", "--completed", action="store_true", dest="completed")
    parser.add_option("-a", "--average", action="store_true", dest="average")
    parser.add_option("--start", action="store_true", dest="start")
    parser.add_option("--stop", action="store_true", dest="stop")
    parser.add_option("--restart", action="store_true", dest="restart")
    parser.add_option("--app", dest="app", help="App name")

    (options, args) = parser.parse_args()

    daemon.options = options

    if options.start:
        print "Starting daemon"
        daemon.start()
    elif options.stop:
        daemon.stop()
    elif options.restart:
        daemon.restart()
    else:
        print "Unknown command"
        sys.exit(2)
    sys.exit(0)
