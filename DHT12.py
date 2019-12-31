#!/usr/bin/env python
#
# Module for adding DHT12 sensor functionality
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
import smbus
import time
import datetime
import logging
import paho.mqtt.client as mqtt
import DB
from logging.handlers import RotatingFileHandler

SLEEP_TIME = 10

class DHT12(object):

        def __init__(self, main_app_log):
                if main_app_log is None:

                        self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                        self.logFile = 'logs/DHT12.log'

                        self.my_handler = RotatingFileHandler(self.logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
                        self.my_handler.setFormatter(self.log_formatter)
                        self.my_handler.setLevel(logging.INFO)

                        self.app_log = logging.getLogger('root')
                        self.app_log.setLevel(logging.INFO)

                        self.app_log.addHandler(self.my_handler)

                else:
                        self.app_log = main_app_log

                self._device = 0x5c
                self._bus = smbus.SMBus(1)
                self._temperature = ""
                self._humidity = ""

                self._db = DB.DB()
                self._db.load_settings()

                self.start_mos()
                self.process_loop()


        def get(self):
                data = self._bus.read_i2c_block_data(self._device, 0x00, 5)

                if data[0] + data[1] + data[2] + data[3] == data[4]:

                        if data[3] > 4: #needs rounding up
                                self._temperature = str(data[2] + 1)
                        else:
                                self._temperature = str(data[2])

                        if data[1] > 4: #needs rounding up
                                self._humidity = str(data[0] + 1)
                        else:
                                self._humidity = str(data[0])
                else:
                        self._temperature = ""
                        self._humidity = ""

        def get_units(self, which_units):
                if which_units == "temperature":
                        return ('\N{DEGREE SIGN}' + 'C')

                if which_units == "humidity":
                        return ("%")


        def on_connect(self, mosclient, userdata, flags, rc):
                self.app_log.info("Subscribing to topic: " + self._db.get_value("mostopic"))
                mosclient.subscribe(self._db.get_value("mostopic"))

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
                                if len(self._temperature)>0:
                                        message = "Inside: " + self._temperature  + self.get_units("temperature") + " " +  self._humidity + self.get_units("humidity")
                                        self.broadcast_send("DHT Temp and Hum", message)
                        except Exception as e:
                                self.app_log.exception('Exception: %s', e)
                        finally: 
                                time.sleep(SLEEP_TIME)

def run_program(main_app_log):
        DHT12(main_app_log)

if __name__ == "__main__":
        run_program(None)
