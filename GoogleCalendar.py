#!/usr/bin/env python
#
# Module for adding Google Calendar Functionality. 
#
# by Peter Juett
# References:https://developers.google.com/calendar/quickstart/python
#
# Copyright 2018
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import logging
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt
import DB

import datetime
import time
import pytz
import os
from dateutil import parser

SLEEP_TIME = 60

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

class Calendar(object):

        def __init__(self, main_app_log):

                if main_app_log is None:

                        self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                        self.logFile = 'logs/GoogleCalendar.log'

                        self.my_handler = RotatingFileHandler(self.logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
                        self.my_handler.setFormatter(self.log_formatter)
                        self.my_handler.setLevel(logging.INFO)

                        self.app_log = logging.getLogger('root')
                        self.app_log.setLevel(logging.INFO)

                        self.app_log.addHandler(self.my_handler)

                else:
                        self.app_log = main_app_log

                self._db = DB.DB()
                self._db.load_settings()

                self.start_mosquito()
                self.process_loop()

        def on_connect(self, mosclient, userdata, flags, rc):
                self.app_log.info("Subscribing to topic: " + self._db.get_value("mostopic"))
                mosclient.subscribe(self._db.get_value("mostopic"))

        def on_disconnect(self, client, userdata, rc):
            if rc != 0:
                self.app_log.info("Unexpected disconnection")

        def on_publish(self, client, userdata, mid):
                self.app_log.info("on_publish - published " + str(mid))

        def start_mosquito(self):
                self.mos_client = mqtt.Client()
                self.mos_client.on_connect = self.on_connect
                self.mos_client.on_disconnect = self.on_disconnect
                self.mos_client.on_publish = self.on_publish

                if len(self._db.get_value("mospassword"))>0:
                        self.mos_client.username_pw_set(self._db.get_value("mosusername"),self._db.get_value("mospassword"))

                mos_broker_address = self._db.get_value("mosbrokeraddress") 

                self.app_log.info("Connecting to: " + mos_broker_address)

                self.mos_client.connect(mos_broker_address, int(self._db.get_value("mosbrokerport")), 60)

                self.app_log.info("Connected")
                self.mos_client.loop_start()

	def broadcast_send(self, data_item, value):
                result = 0
                mid = 0
 
                if data_item is None:
                        self.app_log.info("data_item is None")
                        return

                if value is None:
                        self.app_log.info("value is None")
                        return

                self.app_log.info("publishing: " + data_item + " " + value)

                try:
                        message =  self._db.get_value("name") + "/" + data_item + "/"  + value
                        result, mid = self.mos_client.publish(self._db.get_value("mostopic"), message)
                        if result == mqtt.MQTT_ERR_SUCCESS:
                                self.app_log.info("published OK, Message ID = " + str(mid))
                        elif result == mqtt.MQTT_ERR_NO_CONN:
                                self.app_log.info("publish failed, no connection")
                        else:
                                self.app_log.info("publish failed, result code = " + str(result))
                except Exception as e:
                        self.app_log.exception('Exception: %s', e)

        def process_loop(self):
                while(1):
                        try:
				self.get()
                        except Exception as e:
                                self.app_log.exception('Exception: %s', e)

                        finally:
                                time.sleep(SLEEP_TIME)

	def get_credentials(self):
	    """Gets valid user credentials from storage.

	    If nothing has been stored, or if the stored credentials are invalid,
	    the OAuth2 flow is completed to obtain the new credentials.

	    Returns:
        	Credentials, the obtained credential.
	    """
	    home_dir = os.path.expanduser('~')
	    credential_dir = os.path.join(home_dir, '.credentials')
	    if not os.path.exists(credential_dir):
        	os.makedirs(credential_dir)
	    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

	    store = Storage(credential_path)
	    credentials = store.get()
	    if not credentials or credentials.invalid:
	        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        	flow.user_agent = APPLICATION_NAME
	        if flags:
        	    credentials = tools.run_flow(flow, store, flags)
	        else: # Needed only for compatibility with Python 2.6
        	    credentials = tools.run(flow, store)
	        print('Storing credentials to ' + credential_path)
	    return credentials

	def get(self):
	    """Shows basic usage of the Google Calendar API.

	    Creates a Google Calendar API service object and outputs a list of the next
	    10 events on the user's calendar.
	    """
	    credentials = self.get_credentials()
	    http = credentials.authorize(httplib2.Http())
	    service = discovery.build('calendar', 'v3', http=http)

	    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

            self.app_log.info('Getting the upcoming 5 events')

	    eventsResult = service.events().list(
        	calendarId='primary', timeMin=now, maxResults=5, singleEvents=True,
	        orderBy='startTime').execute()
	    events = eventsResult.get('items', [])

            x = 1				
	    if not events:
                self.app_log.info('No upcoming events found.')
	    for event in events:
        	start = event['start'].get('dateTime', event['start'].get('date'))
		next_event = self.process_text(start, event['summary'])
		self.broadcast_send('Calendar' + str(x), next_event)

		if x == 1:
			next_two_events = next_event
		elif x == 2:
			next_two_events =  next_two_events + ", " + next_event
	                self.broadcast_send('Calendar1and2', next_two_events)

	        x = x + 1

	def process_text(self, start_time, summary):
            
            self.app_log.info(start_time)

	    this_time =	parser.parse(start_time)
            self.app_log.info(this_time.strftime("%a %b %d %Y %H:%M:%S --- %z"))
            tz_len = len(this_time.strftime("%z"))

	    out_text = start_time[5:16].replace("T"," ") 

            if tz_len > 0:		
		    tz = pytz.timezone(self._db.get_value("pytztimezone"))
        	    now = datetime.datetime.now(tz)
	    else:
        	    now = datetime.datetime.now() #daily events can have no timezone info....

            self.app_log.info (now.strftime("%a %b %d %Y %H:%M:%S --- %z"))

	    today_date = now.strftime("%m-%d")

            tomorrow_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%m-%d")

	    delta = this_time - now

	    #Replace with today or tomorrow, as applicable
	    out_text = out_text.replace(today_date,"").replace(tomorrow_date,"Tomorrow")

	    if (delta.days < 7): #if it is soon, then use the day of the week instead of date...
	    	out_text = out_text.replace(this_time.strftime("%m-%d"),this_time.strftime("%a"))

            out_text = out_text + " " + summary

	    return out_text	


def run_program(main_app_log):
	Calendar(main_app_log)

if __name__ == '__main__':
	run_program(None)
