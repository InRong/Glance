# glance

# I have forked this project from the HK centric version of peterhk1 to produce another regional specific version.. This time UK.
# I hope to make it more generic in the future, but am going to make it work for me first....
# I intend to keep up to date with any changes PeterJ makes to his, and incorporate anything useful into here, but please feel to nudge me if I miss anything.


Installation Instructions

1.	Download the latest Kivypie  and install to SD card. Insert into RPI, connect to the network and powerup! 

2.	Upgrade to latest versions of the packages

sudo apt-get update 
sudo apt-get dist-upgrade -y

Then test Kivy is working OK - run the simple example from https://kivy.org/#home 

sudo nano test.py and paste in the following (between the ---). 

------------------
from kivy.app import App 
from kivy.uix.button import Button 

class TestApp(App): 
    def build(self): 
        return Button(text='Hello World') 

TestApp().run() 

------------------

Then run with 

sudo python test.py

You should see a big “Hello World button”. Push it, it should change colour when pressed. 

Hit ctrl + C to exit the app. 

3.	Install Mosquito MQTT for the communications. 

Use this….
sudo wget http://repo.mosquitto.org/debian/mosquitto-jessie.list
sudo apt-get install mosquitto
sudo apt-get install mosquitto-clients -y
also 
sudo pip install --upgrade pip
sudo pip install paho-mqtt
Test Mosquito
Subscribe to a test topic in one SSH window
mosquitto_sub -t test_topic 
Send a test message on the test topic in another SSH window. 
mosquitto_pub -t test_topic -m "Hello"

4.	Install SQLite3 for the database. 

sudo apt-get install sqlite3

5.	Install and test Apache for the web server and PHP for the server side web page processing. 

sudo apt-get install apache2 -y

sudo apt-get install libapache2-mod-php5 -y

sudo apt-get install php5-sqlite

Make sure you give permissions for the web folder.
sudo chown www-data:www-data -R /var/www/html

Test the web server is working – from a browser on your network try

http://<Your Raspberry Pi Ip address>/index.html

You should see an Apache web page appear. 

After test, delete the test file

sudo rm /var/www/html/index.html


6.	Copy the python source files and web source files to the /home/sysop/Glance and /var/www/html/GlanceWeb folders respectively. Also copy Clock, Music, Pictures and Inspiration sub-folders and contents and create the logs subfolder.

a)	Install source modules and dependencies. 

From /home/sysop/

git clone https://github.com/InRong/Glance.git

Create the logs directory.
mkdir Glance/logs

b)	Install web pages and database

cd /var/www/html/

sudo git clone https://github.com/peterjhk1/GlanceWeb.git

7.	Configure the Raspberry Pi
sudo raspi-config 

Set the pi hostname to ‘bedroomtouch’ 
Set the timezone as required
Select ‘wait for network at boot’
Activate I2C (under interface options)
reboot to set the hostname

8.	Install ALL the required dependencies

a)	For the Calendar module

https://developers.google.com/calendar/quickstart/python
sudo pip install --upgrade google-api-python-client
Install timezone and dateutil module  

sudo pip install pytz	
sudo pip install python-dateutil

	       To authorize the script for your calendar for the first time, follow the instructions for the secret json file and create and run
sudo python google_quickstart.py --noauth_local_webserver
	
b)	For the BMP180 module
https://learn.adafruit.com/using-the-bmp085-with-raspberry-pi/using-the-adafruit-bmp-python-library
c)	For the Audio module
For translating numbers to words
cd ..
sudo git clone https://github.com/pwdyson/inflect.py.git

d)	For the Hk Weather
sudo pip install feedparser

9.	 Customize the database 
The database file is /var/www/html/GlanceWeb/clp.db
cd /var/www/html/GlanceWeb/
Type
sudo sqlite3 clp.db
select * from settings
select * from messages

'HUE user and HUB IP
insert into settings (setting,value) VALUES ('hueuser', '<your value>');
insert into settings (setting,value) VALUES ('huehubip', '<your value>');

'TP Link HS100 socket IP addresses
insert into settings (setting,value) VALUES ('hs100ip0', '<your value>');
insert into settings (setting,value) VALUES ('hs100ip1', '<your value>');
insert into settings (setting,value) VALUES ('hs100ip2', '<your value>');

'Air Quality token from WAQI
insert into settings (setting,value) VALUES ('WAQItoken', '<your value>');

'Stock quote and currency exchange value from Aphavantage
insert into settings (setting,value) VALUES ('alphavantageapikey', '<your value>');
insert into settings (setting,value) VALUES ('alphavantagestock1', 'MSFT');
insert into settings (setting,value) VALUES ('alphavantagefromcurrency1', 'USD');
insert into settings (setting,value) VALUES ('alphavantagetocurrency1', 'JPY');

'For RPIIO - 
insert into settings (setting,value) VALUES ('rpiioout1', '21');
insert into settings (setting,value) VALUES ('rpiioout2', '6');
insert into settings (setting,value) VALUES ('rpiioin1', '4');
insert into settings (setting,value) VALUES ('rpiioin2', '17');

insert into messages (host, name, value, description, display,action) values ('Bedroom Touchscreen','RPIIOOUT','1+','LED 1 On','0','1');
insert into messages (host, name, value, description, display,action) values ('Bedroom Touchscreen','RPIIOOUT','1-','LED 1 Off','0','1');
insert into messages (host, name, value, description, display,action) values ('Bedroom Touchscreen','RPIIOOUT','2+','LED2 On','0','1');
insert into messages (host, name, value, description, display,action) values ('Bedroom Touchscreen','RPIIOOUT','2-','LED2 Off','0','1');
insert into messages (host, name, value, description, display,action) values ('Bedroom Touchscreen','RPIIOIN1','','Switch 1','1','0');
insert into messages (host, name, value, description, display,action) values ('Bedroom Touchscreen','RPIIOIN2','','Switch 2','1','0');


insert into settings (setting,value) VALUES ('nighttime', '23:00');
insert into settings (setting,value) VALUES ('morningtime', '6:00');
insert into settings (setting,value) VALUES ('afternoontime', '12:00');
insert into settings (setting,value) VALUES ('eveningtime', '19:00');


insert into messages (host, name, value, description, display,action) values ('','If Morning','if','If Morning','0','1');
insert into messages (host, name, value, description, display,action) values ('','If Afternoon','if','If Afternoon','0','1');
insert into messages (host, name, value, description, display,action) values ('','If Evening','if','If Evening','0','1');
insert into messages (host, name, value, description, display,action) values ('','If Night','if','If Night','0','1');

Also Note that there is a timezone in the DB. I am not yet sure of the consequences of leaving it, so I recommend changing it to your local
e.g.:
sqlite> select * from settings where setting='pytztimezone';
1446|pytztimezone|Asia/Hong_Kong

update settings set value='Europe/London' where setting='pytztimezone';


Note that a restart may be necessary after the database update (if you have Glance running that is). 

10.	To make the system autorun at boot, 
sudo nano /etc/rc.local
Add the lines (before exit 0)
cd /home/sysop/Glance/
sudo python launcher.py &

	

Troubleshooting
==============

Google Calendar:

 If you get the following in the GoogleCalendar.log file

HttpError: <HttpError 403 when requesting https://www.googleapis.com/calendar/v3/users/me/calendarList?alt=json returned "Project xxxxxxxxxx is not found and cannot be used for API calls. If it is recently created, enable Calendar API by visiting https://console.developers.google.com/apis/api/calendar.googleapis.com/overview?project=xxxxxxxxxx then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.">

 Then paste the enclosed URL into a browser, click on Library on the left, and find the Google Calendar API. Click this, and then select Enable. Restart the google calendar element once that ha completed.
