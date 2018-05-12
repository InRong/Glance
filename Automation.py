#!/usr/bin/env python
#
# Automation for extending the system
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
#
#
from threading import Thread

import time
import logging
import paho.mqtt.client as mqtt
import DB
from logging.handlers import RotatingFileHandler
import Utils
import Event
import os


SLEEP_TIME = 1

class Automation(object) :
	def __init__(self, main_app_log):
		try:
	                if main_app_log is None:

        	                self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                	        self.logFile = 'logs/Automation.log'

	                        self.my_handler = RotatingFileHandler(self.logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
        	                self.my_handler.setFormatter(self.log_formatter)
                	        self.my_handler.setLevel(logging.INFO)

	                        self.app_log = logging.getLogger('root')
        	                self.app_log.setLevel(logging.INFO)

                	        self.app_log.addHandler(self.my_handler)

	                else:
        	                self.app_log = main_app_log

	                self.file_modified_time_at_last_read = time.time()

        	        self.motion_value = False
	                self.last_pir_time = time.time()
	        
		        self.light_value = 0
        	        self.last_light_message = ""

	                self.temperature_value = 0
        	        self.last_temperature_message = ""

	                self.humidity_value = 0
        	        self.last_humidity_message = ""

 		        self.last_event = None
        	        self.last_mins = 99
 
			self.db = DB.DB()
			self.read_settings()
			self.start_mosquitto()
        	        self.publish_loop()

                except Exception as e:
                        self.app_log.exception('Exception: %s', e)


        def read_settings(self):
                try:
                        #check if the database has changed, if so, re-read it.
                        filemodifiedtime = time.ctime(os.path.getmtime(self.db.get_file_path()))
                        if(filemodifiedtime == self.file_modified_time_at_last_read): #database has not changed sonce last time we read
                                return

                        if self.db.get_value("confirmationbeep") == "on" and self.started:
                                audio = Audio.Audio()
                                audio.play_beep()

                        self.file_modified_time_at_last_read = time.ctime(os.path.getmtime(self.db.get_file_path()))

                        self.db.load_settings()
                        self.app_log.info("settings reloaded")

                except Exception as e:
                        self.app_log.exception('Exception: %s', e)


	def on_connect(self, mosclient, userdata, flags, rc):
		try:
	        	self.app_log.info("Subscribing to topic: " + self.db.get_value("mostopic"))
		        mosclient.subscribe(self.db.get_value("mostopic"))
                except Exception as e:
                        self.app_log.exception('Exception: %s', e)

	def on_message(self, mosclient, userdata, msg):
		try:
	               	message_parts = str(msg.payload).split("/")
        	       	if len(message_parts)==3:
				#Receive an incoming message and perform an action accordingly.
                                incoming = message_parts[0] + "/" + message_parts[1] + "/"
				self.app_log.info("Incoming - " + str(msg.payload))

                                if incoming == self.db.get_message("motionsensor"):
                                        self.motion_value = (message_parts[2] == "on")
       	                                if self.motion_value:
               	                                self.trigger_action_on_motion()

                                #read the selected sensor data
                                elif incoming == self.db.get_message("lightsensor"):
                                        light_value =  int(message_parts[2])
                                        if light_value <= self.db.get_int_value("normallight"):
                                                if self.last_light_message!="lighton":
                                                        self.send_message_set("lighton")
                                                        self.last_light_message="lighton"

                                        elif light_value >= self.db.get_int_value("brightlight"):
                                                if self.last_light_message!="lightoff":
                                                        self.send_message_set("lightoff")
                                                        self.last_light_message="lightoff"

                                elif incoming == self.db.get_message("temperaturesensor"):
                                        temperature_value =  int(message_parts[2])

                                        if temperature_value <= self.db.get_int_value("cold"):
                                                if self.last_temperature_message!="tempon":
                                                        self.send_message_set("tempon")
                                                        self.last_temperature_message="tempon"

                                        elif self.temperature_value >= self.db.get_int_value("hot"):
                                                if self.last_temperature_message!="tempoff":
                                                        self.send_message_set("tempoff")
                                                        self.last_temperature_message="tempoff"

                                elif incoming == self.db.get_message("humiditysensor"):
                                        humidity_value =  int(message_parts[2])

                                        if humidity_value <= self.db.get_int_value("dry"):
                                                if self.last_humidty_message!="humidityon":
                                                        self.send_message_set("humidityon")
                                                        self.last_humidity_message="humidityon"

                                        elif humidity_value >= self.db.get_int_value("humid"):
                                                if self.last_humidity_message!="humidityoff":
                                                        self.send_message_set("humidityoff")
                                                        self.last_humidity_message="humidityoff"
 
                                elif message_parts[1] == "reboot":
                                	if message_parts[0] == self.db.get_value("name"):
                                        	os.system('reboot -f')
 

                except Exception as e:
                        self.app_log.exception('Exception: %s', e)

        def send_message_set(self, set_name):
                Thread(target=Utils.send_messages,args=(self.db, self.mos_client, self.app_log, set_name,)).start()

	def start_mosquitto(self):
		try:
	       		self.mos_client = mqtt.Client()
        	       	self.mos_client.on_connect = self.on_connect
               		self.mos_client.on_message = self.on_message

	               	if len(self.db.get_value("mospassword"))>0:
        	        	self.mos_client.username_pw_set(self.db.get_value("mosusername"),self.db.get_value("mospassword"))

	               	logging.info("Connecting to: " + self.db.get_value("mosbrokeraddress"))

        	       	self.mos_client.connect(self.db.get_value("mosbrokeraddress"), int(self.db.get_value("mosbrokerport")), 60)

	               	logging.info("Connected")
        	       	self.mos_client.loop_start()
                except Exception as e:
                        self.app_log.exception('Exception: %s', e)

        def trigger_action_on_motion(self):

                try:
                        if (time.time()-self.last_pir_time <=8): #only fire this once per high
                                return;

                        self.last_pir_time = time.time()

                        self.send_message_set("motionon")

                        self.send_message_set("motionon1")

                        if self.away:
                                Thread(target=Utils.send_motion_email,args=(self.db, self.app_log)).start()

                except Exception as e:
                        self.app_log.exception('Exception: %s', e)

	def publish_loop(self):
		while(1):
			try:
				self.read_settings()

        	                if (self.last_mins <> Utils.get_mins()): #check once a minute
                	                self.last_mins = Utils.get_mins()

	                                event_list = Event.EventList()
        	                        next_event = event_list.get_next_event(self.db)

	                                if next_event.get_mins_until_event()==0: #then the event is now.
        	                                self.app_log.info("time for event")
                	                        self.app_log.info(next_event.name + "on")
			                        self.send_message_set(next_event.name + "on")
                                	        self.last_event = next_event

				pass
        	        except Exception as e:
                	        self.app_log.exception('Exception: %s', e)
			finally:
				time.sleep(SLEEP_TIME)

def run_program(main_app_log):
	Automation(main_app_log)

if __name__ == '__main__':
        run_program(None)


