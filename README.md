PyBossa application for categorizing Usahidi reports
====================================================

This pybossa application allows you to categorize, and add/improve the
geo-localization of the collected reports in an Ushahidi server, using a simple
web interface.

![](http://i.imgur.com/6E63EkQ.png)

Categorizing the incident:
![](http://i.imgur.com/VDFYkvt.png)

Geolocating the incident:
![](http://i.imgur.com/UqBUqIu.png)

## Setting the application

This application uses the [PyBossa API](http://docs.pybossa.com/en/latest/user/tutorial.html) 
for creating the application, tutorial and uploading the tasks from a CSV file. 

In order to use this application you will need an
account in a PyBossa server (if you want to install your own server, check the
[official documentation](http://docs.pybossa.com). 

Once you have an account, you will need your associated API-KEY with your account.

![](http://i.imgur.com/tygQd0w.png)

Then, you will need to install the required dependencies for creating the
application in the PyBossa server, upload the tasks, etc, etc.

You can install the dependencies globally in your system, but we recommend to
do it locally in a [virtual
environment](http://pypi.python.org/pypi/virtualenv) which basically creates
a folder and stores there all the required libraries, keeping the installation
simple and not interfering with other libraries in your system.

Hence, the steps for installing the dependencies using a virtualenv will be:

    1.- Clone this repository or download the [ZIP file](https://github.com/PyBossa/app-ushahidi/archive/master.zip)
    2.- Access the folder that you have created by cloning the repository or by
    unzipping the ZIP file.
    3.- Run the following command to create the virtualenv: virtualenv env
    4.- The previous command will create a folder **env** with all the required
    libraries, now we need to activate this environment: . env/bin/activate
    5.- You should see in the promt that a **(env)** string is attached to it,
    something like: **(env)**username@machinename:~/app-ushahidi
    6.- Now you can install the dependencies for the application: pip install -r requirements.txt

Now you are done! All you have to do now is using it :-)

## Importing the incident reports into the application

In order to start working with the Ushahidi reports, you will need first to
import the reports into the PyBossa server, so this application can use them as
tasks. Ushahidi has a feature that exports the reports into a CSV file.

This CSV file can be re-used to import the tasks into the PyBossa application. 
In other words, each CSV row --incident-- will be converted as a task for this
PyBossa application. 

All you have to do is to run the following command:

```bash
    python createTasks.py -s SERVER -k API_KEY -c --data CSV_FILE --usahidi-server
USHAHIDI
```

**NOTE**: You need to specify thhe Ushahidi server from where you obtained the
CSV file with the reports, because the Categories and sub-categories will be gathered 
from that server, so you don't have to add them manually.

The previous command will **create the application**, **the tutorial** and 
**upload the incidents** to the PyBossa server.

If you have not modified the **app.json** file, your application will be hosted
in the PyBossa server: http://PYBOSSA/app/ushahidi (see [the documentation for
more details about the app.json file](http://docs.pybossa.com/en/latest/user/tutorial.html#configuring-the-name-short-name-thumbnail-etc)).

If there is already an application with that name, you can modify your
application name, by editing the [app.jon file](http://docs.pybossa.com/en/latest/user/tutorial.html#configuring-the-name-short-name-thumbnail-etc).

### Adding more incidents to categorize

If you need to add more incidents to categorize, all you have to do is to get
the new set of incidents in a new CSV file and run the following command:

```bash
    python createTasks.py -s SERVER -k API_KEY -x --data ushahidi.csv --ushahidi-server USHAHIDI
```

This will add new tasks to the server, and will be inmediately avaiable for the
users.

### Updating the tutorial and description of the application

In case that you need to modify the tutorial or description of the application,
you only need to edit the next two files:

 * **tutorial.html**
 * **long_description.html**

Then, run the next command:

```
    python createTasks.py -s SERVER -k API_KEY -t
```

## Categorizing the incident reports

Once the application has been created, now you can test it in your web-browser
by opening the following URL (if you have not modified the name of the
application): http://PYBOSSA-SERVER/app/ushahidi

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

```bash
    python getResults.py -s PYBOSSA -k API-KEY -r
```

And you will get all the results, even for not completed tasks, written to the 
file **results.csv**. If you only want the completed tasks, run it with this
argument:

```bash
    python getResults.py -s PYBOSSA -k API-KEY -c -r
```

And if you want to compute the canonical results (this will be done only for
completed tasks):

```bash
    python getResults.py -s PYBOSSA -k API-KEY -c -a
```

While this application is useful, you will need to run it by hand (or using
a Cron job) every time you want the latest results in the CSV file. If you want
to automate this process, check the next section.

**NOTE**: you can change the name of the file where you want to export the results
by using the -f argument.

### Using export.py for extracting data automatically

**NOTE**: You will need also to install the [mongoDB server](http://www.mongodb.org/)
if you want to use this method, as the application keeps a record of which tasks have 
been already saved, in order to save bandwith and not overload the PyBossa
server.

This application is a [service/daemon](http://en.wikipedia.org/wiki/Daemon_%28computing%29) 
that will run in the background polling
the PyBossa server for new answers and saving them into a CSV file as well as
exporting them to an Ushahidi server of your choice.

The application has the same arguments as the previous one, but this
application can be started and stopped as a server:

```bash
    python export.py --start -s PYBOSSA -k API-KEY -c -a
```

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

**Note: daemon.py by Sander Marechal**
