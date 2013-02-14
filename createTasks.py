#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.


import json
from optparse import OptionParser
import pbclient
import requests


def get_categories(url):
    """Gets Ushahidi categories from the server"""
    url = url + "/api?task=categories"
    r = requests.get(url)
    data = r.json()
    categories = data['payload']['categories']
    return categories

def task_formatter(app_config, row, n_answers, categories):
    """
    Creates tasks for the application

    :arg integer app_id: Application ID in PyBossa.
    :returns: Task ID in PyBossa.
    :rtype: integer
    """
    # Each row has the following format
    # row[0] = INCIDENT ID,
    # row[1] = INCIDENT TITLE,
    # row[2] = INCIDENT DATE
    # row[3] = LOCATION
    # row[4] = DESCRIPTION
    # row[5] = CATEGORY
    # row[6] = LATITUDE
    # row[7] = LONGITUDE
    # row[8] = APPROVED
    # row[9] = VERIFIED

    incident = dict(id=row[0],
                    title=row[1],
                    date=row[2],
                    location=row[3],
                    description=row[4],
                    category=row[5],
                    latitude=row[6],
                    longitude=row[7],
                    approved=row[8],
                    verified=row[9])
    categories = categories

    return dict(question=app_config['question'],
                n_answers=int(n_answers),
                incident=incident,
                categories=categories)


if __name__ == "__main__":
    # Arguments for the application
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    # URL where PyBossa listens
    parser.add_option("-s", "--server", dest="api_url",
                      help="PyBossa URL http://domain.com/", metavar="URL")
    # API-KEY
    parser.add_option("-k", "--api-key", dest="api_key",
                      help="PyBossa User API-KEY to interact with PyBossa",
                      metavar="API-KEY")
    # Create App
    parser.add_option("-c", "--create-app", action="store_true",
                      dest="create_app",
                      help="Create the application",
                      metavar="CREATE-APP")
    # Update template for tasks and long_description for app
    parser.add_option("-t", "--update-template", action="store_true",
                      dest="update_template",
                      help="Update Tasks template",
                      metavar="UPDATE-TEMPLATE")

    # Update tasks question
    parser.add_option("-q", "--update-tasks",
                      dest="update_tasks",
                      help="Update Tasks question",
                      metavar="UPDATE-TASKS")

    parser.add_option("-x", "--extra-task", action="store_true",
                      dest="add_more_tasks",
                      help="Add more tasks",
                      metavar="ADD-MORE-TASKS")

    # Modify the number of TaskRuns per Task
    # (default 30)
    parser.add_option("-n", "--number-answers",
                      dest="n_answers",
                      help="Number of answers per task",
                      metavar="N-ANSWERS")

    parser.add_option("-u", "--ushahidi-server",
                      dest="ushahidi_server",
                      help="Ushahidi server",
                      metavar="Ushahidi server")

    parser.add_option("-d", "--data",
                      dest="csv_file",
                      help="CSV file with incident reports to import",
                      metavar="CSV file")

    parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
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
        options.api_url = 'http://localhost:5000/'
    pbclient.set('endpoint', options.api_url)

    if not options.api_key:
        parser.error("You must supply an API-KEY to create an \
                      applicationa and tasks in PyBossa")
    else:
        pbclient.set('api_key', options.api_key)

    if (options.create_app or options.add_more_tasks) and not options.ushahidi_server:
        parser.error("You must supply the Ushahidi server from where you want \
                     to categorize the reports")

    if (options.verbose):
        print('Running against PyBosssa instance at: %s' % options.api_url)
        print('Using API-KEY: %s' % options.api_key)

    if not options.n_answers:
        options.n_answers = 2

    if options.create_app:
        import csv
        pbclient.create_app(app_config['name'],
                            app_config['short_name'],
                            app_config['description'])
        app = pbclient.find_app(short_name=app_config['short_name'])[0]
        app.long_description = open('long_description.html').read()
        app.info['task_presenter'] = open('template.html').read()
        app.info['thumbnail'] = app_config['thumbnail']
        app.info['tutorial'] = open('tutorial.html').read()

        categories = get_categories(options.ushahidi_server)
        pbclient.update_app(app)

        if not options.csv_file:
            options.csv = 'ushahidi.csv'

        with open(options.csv_file, 'rb') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            # Each row has the following format
            # # <- ID
            # INCIDENT TITLE
            # INCIDENT DATE
            # LOCATION
            # DESCRIPTION
            # CATEGORY
            # LATITUDE
            # LONGITUDE
            # APPROVED
            # VERIFIED
            for row in csvreader:
                if row[0] != '#':
                    task_info = task_formatter(app_config, row,
                                               options.n_answers,
                                               categories)
                    pbclient.create_task(app.id, task_info)
    else:
        app = pbclient.find_app(short_name=app_config['short_name'])[0]
        if options.add_more_tasks:
            categories = get_categories(options.ushahidi_server)
            import csv
            if not options.csv_file:
                options.csv_file = 'ushahidi.csv'
            with open(options.csv_file, 'rb') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',')
                # Each row has the following format
                # # <- ID
                # INCIDENT TITLE
                # INCIDENT DATE
                # LOCATION
                # DESCRIPTION
                # CATEGORY
                # LATITUDE
                # LONGITUDE
                # APPROVED
                # VERIFIED
                for row in csvreader:
                    if row[0] != 'tweetid':
                        task_info = task_formatter(app_config, row,
                                                   options.n_answers,
                                                   categories)
                        pbclient.create_task(app.id, task_info)

    if options.update_template:
        print "Updating app tutorial, description and task presenter..."
        app = pbclient.find_app(short_name=app_config['short_name'])[0]
        app.long_description = open('long_description.html').read()
        app.info['task_presenter'] = open('template.html').read()
        app.info['tutorial'] = open('tutorial.html').read()
        app.info['thumbnail'] = app_config['thumbnail']
        pbclient.update_app(app)
        print "Done!"

    if options.update_tasks:
        print "Updating task n_answers"
        app = pbclient.find_app(short_name=app_config['short_name'])[0]
        n_tasks = 0
        offset = 0
        limit = 100
        tasks = pbclient.get_tasks(app.id, offset=offset, limit=limit)
        while tasks:
            for task in tasks:
                print "Updating task: %s" % task.id
                if ('n_answers' in task.info.keys()):
                    del(task.info['n_answers'])
                task.n_answers = int(options.update_tasks)
                pbclient.update_task(task)
                n_tasks += 1
            offset = (offset + limit)
            tasks = pbclient.get_tasks(app.id, offset=offset, limit=limit)
        print "%s Tasks have been updated!" % n_tasks

    if not options.create_app and not options.update_template\
       and not options.add_more_tasks and not options.update_tasks:
        parser.error("Please check --help or -h for the available options")
