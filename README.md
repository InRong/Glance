# glance

Installation Instructions

1.	Download the latest Kivypie  and upgrade to latest versions of the packages

Then run the simple example from https://kivy.org/#home 

from kivy.app import App 
from kivy.uix.button import Button 

class TestApp(App): 
    def build(self): 
        return Button(text='Hello World') 

TestApp().run() 

2.	Install Mosquito MQTT for the communications. 

Use this….
sudo wget http://repo.mosquitto.org/debian/mosquitto-jessie.list
  sudo apt-get install mosquitto
sudo apt-get install mosquitto-clients
also 
sudo pip install paho-mqtt
Test Mosquito
Subscribe to a test topic in one SSH window
mosquitto_sub -V mqttv311 -t test_topic 
Send a test message on the test topic in another SSH window. 
mosquitto_pub -V mqttv311 -t test_topic -m "Hello"

3.	Install SQLite3 for the database. 
sudo apt-get install sqlite3

4.	Install and test Apache for the web server and PHP for the server side web page processing. 
sudo apt-get install apache2 -y
sudo apt-get install libapache2-mod-php5

sudo apt-get install php5-sqlite


5.	Copy the python source files and web source files to the Glance and /var/www/html folders respectively. Also copy Music, Pictures and Inspiration sub-folders and contents and create the logs subfolder.

6.	Install the required dependencies as follows

a)	For the Calendar module

https://developers.google.com/calendar/quickstart/python
pip install --upgrade google-api-python-client
Install timezone and dateutil module  

sudo pip install pytz	
sudo pip install python-dateutil

	       To authorize the script for your calendar for the first time, run
sudo python google_quickstart.py --noauth_local_webserver
	
b)	For the BMP180 module
https://learn.adafruit.com/using-the-bmp085-with-raspberry-pi/using-the-adafruit-bmp-python-library
c)	For the Audio module
For translating numbers to words
sudo git clone https://github.com/pwdyson/inflect.py.git

d)	For the Hk Weather
sudo pip install feedparser

# Glance
