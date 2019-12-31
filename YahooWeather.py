# -*- coding: utf-8 -*-

#!/usr/bin/env python
#
# Module for integrating Yahoo Weather with the system
#
# by Peter Juett
# References:
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

import urllib.request, urllib.error, urllib.parse, urllib.request, urllib.parse, urllib.error, json
import time
import datetime
import traceback
import os
import DB
import logging
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt

SLEEP_TIME = 60

class YahooWeather(object):

        def __init__(self, main_app_log):

                if main_app_log is None:

                        self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                        self.logFile = 'logs/YahooWeather.log'

                        self.my_handler = RotatingFileHandler(self.logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
                        self.my_handler.setFormatter(self.log_formatter)
                        self.my_handler.setLevel(logging.INFO)

                        self.app_log = logging.getLogger('root')
                        self.app_log.setLevel(logging.INFO)

                        self.app_log.addHandler(self.my_handler)

                else:
                        self.app_log = main_app_log

                self._weather_text = ""
                self._temperature = ""

                self._db = DB.DB()
                self._db.load_settings()

                self.start_mos()
                self.process_loop()

        def get(self, woeid, temperaturescale):
                self._weather_text = ""
                self._temperature = ""
        
                baseurl = "https://query.yahooapis.com/v1/public/yql?"
                yql_query = "select item.condition from weather.forecast where woeid = " + woeid + " and u='" + temperaturescale + "'"
                yql_url = baseurl + urllib.parse.urlencode({'q':yql_query}) + "&format=json"
                result = urllib.request.urlopen(yql_url).read()
                data = json.loads(result)
                self.app_log.info(data)
                self._weather_text = data['query']['results']['channel']['item']['condition']['text']
                self._temperature = data['query']['results']['channel']['item']['condition']['temp'] + '\N{DEGREE SIGN}' + 'C'

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

        def process_loop(self):
                x = 0
                while(1):
                        try:
                                #Data is refreshed every 10 minutes
                                x = x + 1
                                if x == 1:
                                        self.get('2165423', 'c')
                                elif x==10:             
                                        x = 0;  
                                #This is broadcast every minute, if valid
                                if len(self._temperature) > 0:
                                        message =  self._db.get_value("name") + "/HK Weather/" + self._temperature + " " + self._weather_text
                                        self.mos_client.publish(self._db.get_value("mostopic"), message)
                                        self.app_log.info("Sent " + self._temperature + " " + self._weather_text)
                                else:
                                        self.app_log.info("Nothing Sent")
                        
                        except Exception as e:
                                self.app_log.exception('Exception: %s', e)
                        finally:
                                time.sleep(SLEEP_TIME)

def run_program(main_app_log):
         YahooWeather(main_app_log)

if __name__ == '__main__':
        run_program(None)



