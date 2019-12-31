# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Module for extending functionality to UK Weather
#
# by Peter Juett
# References: http://rss.weather.gov.hk/rsse.html
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
import urllib.request, urllib.error, urllib.parse, urllib.request, urllib.parse, urllib.error, json
import time
import datetime
import feedparser
import DB
import logging
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt

SLEEP_TIME = 60

class UKWeather(object):

        def __init__(self, main_app_log):

                if main_app_log is None:

                        self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                        self.logFile = 'logs/UKWeather.log'

                        self.my_handler = RotatingFileHandler(self.logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
                        self.my_handler.setFormatter(self.log_formatter)
                        self.my_handler.setLevel(logging.INFO)

                        self.app_log = logging.getLogger('root')
                        self.app_log.setLevel(logging.INFO)

                        self.app_log.addHandler(self.my_handler)

                else:
                        self.app_log = main_app_log

                self.days=3
                self._humidity=[[] for _ in range(self.days)]
                self._temp=[[] for _ in range(self.days)]
                self._day=[[] for _ in range(self.days)]
                self._wind=[[] for _ in range(self.days)]
                self._sun=[[] for _ in range(self.days)]
                self._rise=[[] for _ in range(self.days)]
                self._set=[[] for _ in range(self.days)]
                for day in range(self.days):
                   self._humidity[day] = ""
                   self._temp[day] = ""
                   self._day[day] = ""
                   self._wind[day] = ""
                   self._sun[day] = ""
                   self._rise[day] = ""
                   self._set[day] = ""

                self._db = DB.DB()
                self._db.load_settings()

                self.start_mos()
                self.process_loop()

        def get(self):
                for day in range(self.days):
                   self._humidity[day] = ""
                   self._temp[day] = ""
                   self._day[day] = ""
                   self._wind[day] = ""
                   self._sun[day] = ""
                   self._rise[day] = ""
                   self._set[day] = ""

                targeturl = 'https://weather-broker-cdn.api.bbci.co.uk/en/forecast/rss/3day/2649660'

                d = feedparser.parse(targeturl) 

                if len(d.entries) > 0:
                    results=len(d.entries)
                    if (self.days<results):
                        results = self.days   # Use the lowest of #results or number of storage locations...
                    for day in range(results):
                        desc =  d.entries[day].title
                        desc = desc.replace("Maximum","Max").replace("Minimum","Min").replace("Temperature","Temp")
                        self._day[day] =  desc
                        desc =  d.entries[day].summary_detail.value.split(', ')
                        for item in desc:
                            pair = item.split(": ") 
                            if pair[0] == "Wind Direction":
                                self._wind[day] = pair[1]
                            if pair[0] == "Wind Speed":
                                self._wind[day] = self._wind[day]+"("+pair[1]+")"
                            if pair[0] == "Humidity":
                                self._humidity[day] = pair[1]
                            if pair[0] == "Sunrise":
                                self._sun[day] = "Sunrise:"+pair[1]
                                self._rise[day] = "Sunrise:"+pair[1]
                            if pair[0] == "Sunset":
                                self._sun[day] = self._sun[day] + " Sunset:" + pair[1]
                                self._set[day] =  "Sunset:" + pair[1]
                            #if pair[0] == "Pressure":
                            #    self._press[day] = pair[1]
                            #if pair[0] == "UV Risk":
                            #    self._uv[day] = pair[1]

                        logging.info(self._humidity[0])
                        logging.info(self._day[0])
                    if (len(self._rise[0]) == 0):
                        self._rise[0] = self._rise[1]
                else:
                        logging.info("No entries returned")

        def getunits(self, which_units):
                if which_units == "temperature":
                        return ('\N{DEGREE SIGN}' + 'C')

                if which_units == "humidity":
                        return ("%")

        def on_connect(self, mosclient, userdata, flags, rc):
                self.app_log.info("Subscribing to topic: " + self._db.get_value("mostopic"))
                mosclient.subscribe(self._db.get_value("mostopic"))

        def on_message(self, mosclient, userdata, msg):
                pass

        def start_mos(self):
                self.mos_client = mqtt.Client()
                self.mos_client.on_connect = self.on_connect
                self.mos_client.on_message = self.on_message

                if len(self._db.get_value("mospassword"))>0:
                        self.mos_client.username_pw_set(self._db.get_value("mosusername"),self._db.get_value("mospassword"))

                mos_broker_address = self._db.get_value("mosbrokeraddress")

                self.app_log.info("Connecting to: " + mos_broker_address)

                self.mos_client.connect(mos_broker_address, int(self._db.get_value("mosbrokerport")), 60)

                self.app_log.info("Connected")
                self.mos_client.loop_start()


        def publish_data(self, data):
                try:
                      self.mos_client.publish(self._db.get_value("mostopic"), data)
                      self.app_log.info("Sent - " + data)
                except Exception as e:
                      logging.exception('Exception: %s', e)


        def process_loop(self):
                max = 60
                x = max
                while(1):
                        try:
                                #Data is refreshed every 60 minutes
                                if x == max:
                                        x = 0
                                        self.get()
                                else:
                                        x = x + 1

                                #This is broadcast every minute, if valid
                                if len(self._day[0]) > 0:
                                        message = self._db.get_value("name") + "/UK Weather Summary/" + self._day[x%self.days]
                                        self.publish_data(message)
                                        message = self._db.get_value("name") + "/UK Weather Humidity/" + self._humidity[0]
                                        self.publish_data(message)
                                        message = self._db.get_value("name") + "/UK Weather Wind/" + self._wind[0]
                                        self.publish_data(message)
                                        message = self._db.get_value("name") + "/UK Weather Temp/" + self._temp[0]
                                        self.publish_data(message)
                                        message = self._db.get_value("name") + "/UK Weather Sun/" + self._sun[0]
                                        self.publish_data(message)
                                        for day in range(self.days):
                                             message = self._db.get_value("name") + "/UK Weather Summary" + str(day) +"/" + self._day[day]
                                             self.publish_data(message)
                                             message = self._db.get_value("name") + "/UK Weather Huimidity" + str(day) +"/" + self._humidity[day]
                                             self.publish_data(message)
                                             message = self._db.get_value("name") + "/UK Weather Wind" + str(day) +"/" + self._wind[day]
                                             self.publish_data(message)
                                             message = self._db.get_value("name") + "/UK Weather Temp" + str(day) +"/" + self._temp[day]
                                             self.publish_data(message)
                                             message = self._db.get_value("name") + "/UK Weather Sun" + str(day) +"/" + self._sun[day]
                                             self.publish_data(message)
                                             message = self._db.get_value("name") + "/UK Weather Sunrise" + str(day) +"/" + self._rise[day]
                                             self.publish_data(message)
                                             message = self._db.get_value("name") + "/UK Weather Sunset" + str(day) +"/" + self._set[day]
                                             self.publish_data(message)
                                else:
                                        self.app_log.info("Nothing Sent")
                        except Exception as e:
                                logging.exception('Exception: %s', e)
                        finally:
                                time.sleep(SLEEP_TIME)


def run_program(main_app_log):
        UKWeather(main_app_log)

if __name__ == '__main__':
        run_program(None)

