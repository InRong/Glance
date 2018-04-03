#!/usr/bin/env python
#
# Module for controlling the HUE lighting system
#
# by Peter Juett
# References: https://developers.meethue.com/
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

import time
import logging
import paho.mqtt.client as mqtt
import DB
from logging.handlers import RotatingFileHandler
import requests
import json

SLEEP_TIME = 5

commands = {
	'on'       : '{"on":true}',
	'off'      : '{"on":false}',
}

class HUE(object) :

        def __init__(self, main_app_log):

                if main_app_log is None:

                        self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                        self.logFile = 'logs/HUE.log'

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
		self.start_mos()
		self.process_loop()

	def on_connect(self, mosclient, userdata, flags, rc):
               	self.app_log.info("Subscribing to topic: " + self._db.get_value("mostopic"))
               	mosclient.subscribe(self._db.get_value("mostopic"))

	def send_command(self, user, in_ip, light, in_cmd):
		message = "http://" + in_ip + "/api/" + user + "/lights/" + light  + "/state"
		payload = commands[in_cmd]
        	self.app_log.info("Sending put command to Hue hub - " + message)
        	self.app_log.info("...with payload - " + payload)

		try:
		        r = requests.put(message, data=payload)
        		self.app_log.info(r.status_code)
        		self.app_log.info(r.content)
                except Exception as e:
                        self.app_log.exception('Exception: %s', e)

	def get_status(self, ip, light):
		message = "http://" + ip + "/api/" + self._db.get_value("hueuser")  + "/lights/" + light
		try:
			r = requests.get(message)
			data = r.json()
			if data["state"]["reachable"]:
				return data["state"]["on"]
			else:
				return -1 #Not reachable, so we do not know the state

                except Exception as e:
                        self.app_log.exception('Exception: %s', e)

	def on_message(self, mosclient, userdata, msg):
               	messageparts = str(msg.payload).split("/")
               	if len(messageparts)==3 and messageparts[1] == "HUE":
			full_command =  messageparts[2]
			commd = full_command[-1]
			light = full_command[-2][:1]
			ip =  full_command[0:len(messageparts[2])-1]
			self.app_log.info(ip + " - " + full_command)
			if commd == "+":
				self.send_command(self._db.get_value("hueuser"), self._db.get_value("huehubip"), light, "on")
			elif commd == "-":
				self.send_command(self._db.get_value("hueuser"), self._db.get_value("huehubip"), light, "off")

        def on_disconnect(client, userdata, rc):
            if rc != 0:
                self.app_log.info("Unexpected disconnection")

        def on_publish(self, client, userdata, mid):
                self.app_log.info("on_publish - published " + str(mid))

        def start_mos(self):
                self.mos_client = mqtt.Client()
                self.mos_client.on_connect = self.on_connect
                self.mos_client.on_disconnect = self.on_disconnect
                self.mos_client.on_publish = self.on_publish

	def start_mos(self):
       		self.mos_client = mqtt.Client()
               	self.mos_client.on_connect = self.on_connect
               	self.mos_client.on_message = self.on_message
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
		light = 1

		ip = self._db.get_value("huehubip")

		while True:
			value = ""

			try:
				value = self.get_status(ip, str(light))
	                except Exception as e:
                	        self.app_log.exception('Exception: %s', e)

			#share the status of the light
			if value!= -1: #-1 is not reachable. 
				if value:
					self.broadcast_send("HUE_STATE", ip + "-" + str(light) + "+")
					self.app_log.info("sending message - " + "HUE_STATE" + ip + "-" + str(light) + "+")
				else:
					self.broadcast_send("HUE_STATE", ip + "-" + str(light) + "-")
					self.app_log.info("sending message - " + "HUE_STATE" + ip + "-" + str(light) + "-")
				
			#we look at the status of two lights. Need to extend if more lights required. 
			if light ==1:
				light = 2
			else:
				light = 1

			time.sleep(SLEEP_TIME)

def run_program(main_app_log):
        HUE(main_app_log)

if __name__ == '__main__':
        run_program(None)










