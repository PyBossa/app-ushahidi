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
import json
from optparse import OptionParser
from collections import Counter

import pbclient


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


if __name__ == "__main__":
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
    parser.add_option("-f", "--file", dest="csv_file", help="CSV file to export results")

    (options, args) = parser.parse_args()

    # Load app details
    try:
        app_json = open('app.json')
        app_config = json.load(app_json)
        app_json.close()
    except IOError as e:
        print "app.json is missing! Please create a new one"
        exit(0)

    if not options.api_url:
        options.api_url = 'http://localhost:5000'

    pbclient.set('endpoint', options.api_url)

    if not options.api_key:
        parser.error("You must supply an API-KEY to create an applicationa and tasks in PyBossa")
    else:
        pbclient.set('api_key', options.api_key)

    if (options.verbose):
        print('Running against PyBosssa instance at: %s' % options.api_url)
        print('Using API-KEY: %s' % options.api_key)

    if (options.results):
        offset = 0
        limit = 100

        app = pbclient.find_app(short_name=app_config['short_name'])[0]
        if options.completed:
            completed_tasks = pbclient.find_tasks(app.id,
                                                  state="completed",
                                                  offset=offset,
                                                  limit=limit)
        else:
            completed_tasks = pbclient.find_tasks(app.id,
                                                  offset=offset,
                                                  limit=limit)

        # Now get the task runs
        import csv
        if not (options.csv_file):
            options.csv_file = "results.csv"

        f = csv.writer(open(options.csv_file, "wb"))
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

        while completed_tasks:
            for t in completed_tasks:
                print "Getting answers for task %s: " % t.id
                answers = pbclient.find_taskruns(app.id, task_id=int(t.id))

                if options.average:
                    canonical_answer = copy.deepcopy(answers[0])
                    canonical_answer.task_id = t.id
                    canonical_answer.id = 0
                    canonical_answer.info['category'] = None
                    canonical_answer.info['location'] = None
                    canonical_answer.info['latitude'] = None
                    canonical_answer.info['longitude'] = None
                    # First Categories and sub-categories
                    most_common_category = []
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
                else:
                    for a in answers:
                        line = format_csv_row(t, a)
                        f.writerow(line)

            offset = offset + limit
            if options.completed:
                completed_tasks = pbclient.find_tasks(app.id,
                                                      state="completed",
                                                      offset=offset,
                                                      limit=limit)
            else:
                completed_tasks = pbclient.find_tasks(app.id,
                                                      offset=offset,
                                                      limit=limit)
