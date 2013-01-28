PyBossa application for categorizing Usahidi reports
====================================================

This pybossa application allows you to categorize, and add/improve the
geo-localization of the collected reports in an Ushahidi server, using a simple
web interface.

## Setting the application

This application uses the PyBossa API for creating the application, tutorial
and uploading the tasks. In order to use this application you will need an
account in a PyBossa server. Once you have an account, you will need your
associated API-KEY with your account.

Then, you will need to install several dependencies:

    pip install -e requirements.txt

Now you are done to start using it!

## Importing the incident reports into the application

In order to start working with the Ushahidi reports, you will need first to
import the reports into your PyBossa server. Ushahidi has a feature that
extracts the reports in a CSV file.

This CSV file can be used to import the tasks into the PyBossa application. All
you have to do is to run the following command:

python createTasks.py -s SERVER -k API_KEY -c --data CSV_FILE

This will create the application, the tutorial and upload the data to the
PyBossa server.

If you have not modified the **app.json** file, your application will be hosted
in the PyBossa server: http://PYBOSSA/app/ushahidi

If there is already an application with that name, you can modify your
application name, by editing the app.jon file.

## Categorizing the incident reports

The application has three simple steps:

1.- Add one or more categories (and its associated sub-categories) for the
report. The user can add as many as he wants, and in case of an error, he can
delete them before proceeding to the next step.

2.- If the report has been already geo-localized, the application will ask the
user if he can improve the location. The user will see a web map with the
current location marked by the report, and the user will be able to improve the
location by placing a new marker where he thinks it is the right location. If
the report does not have a location, the user will have to find it and place it
in the map with a marker.

3.- Once the step 1 and two are completed, the user will see a summary of his
categorization before submitting it. If he agrees with it, the user will be
able to submit the categorization by clicking in the button: Submit! Then a new
report will be loaded for the user.

## Exporting the categorized reports

The PyBossa-Ushahidi application has two ways of exporting the data out of the
PyBossa servers:

1.- CSV file
2.- Directly back to the Ushahidi server

The application has been designed in a way that both methods can be used at the
same time, or just the CSV exporting file facility.

The application has two apps that will be able to extract the data:

1.- getResults.py: this app exports the data into a CSV file
2.- export.py: this daemon/service app automatically exports data to a CSV file
and to the Ushahidi server of your choice.

Additionally, both applications can be tuned to export all the data (raw data),
or to compute the canonical answer for a given report. The canonical answer
basically creates a new report with the most voted categories and
sub-categories (when 95% of the answers are the same) and the average for the
latitude and longitude values.

### Using getResults.py for extracting data to a CSV file

This application is really simple to use, just run it like this:

python getResults.py -s PYBOSSA -k API-KEY 

And you will get all the results, even for not completed tasks, written to the 
file **results.csv**. If you only want the completed tasks, run it with this
argument:

python getResults.py -s PYBOSSA -k API-KEY -c

And if you want to compute the canonical results:

python getResults.py -s PYBOSSA -k API-KEY -c -a

While this application is useful, you will need to run it by hand (or using
a Cron job) every time you want the latest results in the CSV file. If you want
to automate this process, check the next section.

### Using export.py for extracting data automatically

This application is a service/daemon that will run in the background polling
the PyBossa server for new answers and saving them into a CSV file as well as
exporting them to an Ushahidi server.

The application has the same arguments as the previous one, but this
application can be started and stopped as a server:

python export.py --start -s PYBOSSA -k API-KEY -c -a

This will run every 5 minutes (the polling time can be changed using the -p
argument) a query to the PyBossa server, getting only the new completed tasks
and saving them into the CSV file. It will also export it to the Ushahidi
server of choice with the argument: --ushahidi-server

You can specify also where you want to save the CSV results file (-f argument).
You can for example specify your Public folder of your Dropbox account, and
then share the public link to that file with all your colleagues. This
configuration will allow you to share the latest completed results (with
canonical computed results) with all your colleagues without problems.

## License

See COPYING file


You can try the application [here](http://crowdcrafting.org/app/usahidi)

# Note: daemon.py by Sander Marechal
