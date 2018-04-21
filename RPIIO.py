#!/usr/bin/env python
#
# RPIIO for controlling RPI GPIO via Mosquitto
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
import time
import logging
import paho.mqtt.client as mqtt
import DB
from logging.handlers import RotatingFileHandler
import threading
import RPi.GPIO as GPIO

SLEEP_TIME = 1

class RPIIO(object) :
	def __init__(self, main_app_log):
		try:
	                if main_app_log is None:

        	                self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                	        self.logFile = 'logs/RPIIO.log'

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

	                GPIO.setmode(GPIO.BCM)

			# set up the outputs
			x = 1
			while(True):
				db_result = self._db.get_value("rpioout" + str(x))
				if (db_result is None):
					break

	        	        GPIO.setup(int(db_result), GPIO.OUT)
				x = x + 1

			# set up the inputs
			x = 1
			while(True):
				db_result = self._db.get_value("rpioin" + str(x))
				if (db_result is None):
					break

	        	        GPIO.setup(int(db_result), GPIO.IN)
				x = x + 1

			self.start_mosquitto()
        	        self.publish_loop()

                except Exception as e:
                        self.app_log.exception('Exception: %s', e)


	def on_connect(self, mosclient, userdata, flags, rc):
		try:
	        	self.app_log.info("Subscribing to topic: " + self._db.get_value("mostopic"))
		        mosclient.subscribe(self._db.get_value("mostopic"))
                except Exception as e:
                        self.app_log.exception('Exception: %s', e)

	def on_message(self, mosclient, userdata, msg):

		try:
	                messageparts = str(msg.payload).split("/")

        	        if len(messageparts)==3:
	                        #command is 1+, 2+ etc to turn high, 1-, 2- etc low
        	                if messageparts[0] == self._db.get_value("name") and  messageparts[1]=="RPIIOOUT":
					
	                                if (messageparts[2][-1:]=="+"): #Last character should be + or -
						command = GPIO.HIGH
					else:
						command = GPIO.LOW

					io = messageparts[2][:len(messageparts[2])-1]

		        	        rpioout = self._db.get_value("rpioout" + io)

                                       	GPIO.output(int(rpioout), command)

                except Exception as e:
                        self.app_log.exception('Exception: %s', e)

	def start_mosquitto(self):
		try:
	       		self.mos_client = mqtt.Client()
        	       	self.mos_client.on_connect = self.on_connect
               		self.mos_client.on_message = self.on_message

	               	if len(self._db.get_value("mospassword"))>0:
        	        	self.mos_client.username_pw_set(self._db.get_value("mosusername"),self._db.get_value("mospassword"))

	               	self.app_log.info("Connecting to: " + self._db.get_value("mosbrokeraddress"))

        	       	self.mos_client.connect(self._db.get_value("mosbrokeraddress"), int(self._db.get_value("mosbrokerport")), 60)

	               	self.app_log.info("Connected")
        	       	self.mos_client.loop_start()
                except Exception as e:
                        self.app_log.exception('Exception: %s', e)

	def publish_loop(self):
		while(1):
			try:
				x = 1
				while(True):
					db_result = self._db.get_value("rpioin" + str(x))
					if (db_result is None):
						break

		        	        if GPIO.input(int(db_result)): # button is released
                                		self.mos_client.publish(self._db.get_value("mostopic"), self._db.get_value("name") + "/RPIIOIN" + str(x) +  "/+")
		                                self.app_log.info(str(x) + " pressed")
 					else:
                                		self.mos_client.publish(self._db.get_value("mostopic"), self._db.get_value("name") + "/RPIIOIN" + str(x) +  "/-")
		                                self.app_log.info(str(x) + " not pressed")
                        
					x = x + 1

        	        except Exception as e:
                	        self.app_log.exception('Exception: %s', e)
			finally:
				time.sleep(SLEEP_TIME)
			time.sleep(SLEEP_TIME)
			

def run_program(main_app_log):
	RPIIO(main_app_log)

if __name__ == '__main__':
        run_program(None)


