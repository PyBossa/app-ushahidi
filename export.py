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
import time
import requests
from optparse import OptionParser
from collections import Counter
from pymongo import MongoClient

import pbclient

from daemon import Daemon

def push_to_ushahidi(server, data):
    """Push an incident to an Ushahidi server"""
    payload = {}
    payload['incident_title'] = data.info['title']
    payload['incident_description'] = data.info['description']

    tmp = time.strptime(data.info['date'], "%Y-%m-%d %H:%M:%S")

    payload['incident_date'] = time.strftime("%Y-%m-%d", tmp)
    payload['incident_hour'] = time.strftime("%H", tmp)
    payload['incident_minute'] = time.strftime("%M", tmp)
    payload['incident_ampm'] = time.strftime("%p", tmp)
    payload['incident_category'] = data.info['category']
    payload['latitude'] = data.info['latitude']
    payload['longitude'] = data.info['longitude']
    payload['location_name'] = data.info['location']

    r = requests.post(server + "?task=report", payload)
    print r.url
    print r.status_code


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
        tmp = ""
        for c in a.info['category']:
            if c:
                tmp += c + ","
        line.append(tmp)
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

        if (self.options.polling):
            polling_time = float(self.options.polling)
        else:
            polling_time = float(1)

        if (self.options.csv_file):
            csv_file_name = self.options.csv_file
        else:
            csv_file_name = "/tmp/results.csv"


        if (self.options.results):
            app = pbclient.find_app(short_name=app_name)[0]

        # Connect to the server
        connection = MongoClient('localhost', 27017)

        # Create DB
        db = connection[app_name]
        # Now get the task runs
        print "Creating CSV file"
        with open(csv_file_name, "a+b") as myfile:
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
                # Update task status by requesting new tasks
                requests.get(self.options.api_url + "/api/app/" + str(app.id) + "/newtask")
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
                                    most_common_category = []
                                    #most_common_sub_category = None
                                    categories = []
                                    for a in answers:
                                        for cat in a.info['category']:
                                            categories.append(cat)
                                    c = Counter(categories)
                                    for item in c.most_common():
                                        cat = item[0]
                                        votes = item[1]
                                        if votes >= (int(t.n_answers)*0.95):
                                            most_common_category.append(cat)

                                    canonical_answer.info['category'] = most_common_category
                                    #if c.most_common()[0][1] >= 2:
                                    #    most_common_category = c.most_common()[0][0]
                                    #    sub_categories = []
                                    #    for a in answers:
                                    #        for cat in a.info['category']:
                                    #            if cat == most_common_category:
                                    #                for sc in a.info['category'][cat]['sub-categories']:
                                    #                    sub_categories.append(sc)
                                    #    c2 = Counter(sub_categories)
                                    #    if c2.most_common()[0][1] >= 2:
                                    #        most_common_sub_category = [c2.most_common()[0][0]]
                                    #    else:
                                    #        most_common_sub_category = list(c2)
                                    #sub_categories = {'sub-categories':
                                    #                  most_common_sub_category}
                                    #canonical_answer.info['category'] = {
                                    #    most_common_category: sub_categories}

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
                                        if a.info['latitude'] != 'dontKnow' and a.info['longitude']!= 'dontKnow':
                                            latitudes.append(float(a.info['latitude']))
                                            longitudes.append(float(a.info['longitude']))
                                    if (len(latitudes)>0) and (len(longitudes)>0):
                                        most_common_latitude = float( sum(latitudes)/len(latitudes))
                                        most_common_longitude = float( sum(longitudes)/len(longitudes))
                                        canonical_answer.info['latitude'] = most_common_latitude
                                        canonical_answer.info['longitude'] = most_common_longitude
                                    else:
                                        canonical_answer.info['latitude'] = None
                                        canonical_answer.info['longitude'] = None
                                    line = format_csv_row(t,canonical_answer)
                                    print "saving answer"
                                    f.writerow(line)
                                    db_task['saved'] = 1
                                    db.tasks.save(db_task)
                                    print "submitting answer to Ushahidi"
                                    push_to_ushahidi("http://uchaguzi.co.ke/", canonical_answer)
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
                time.sleep(60 * polling_time)

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
    parser.add_option("--polling", dest="polling", help="Polling time in minutes (default 5 minutes)")
    parser.add_option("-f", "--file", dest="csv_file", help="CSV file to export results")

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
