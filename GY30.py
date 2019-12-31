#!/usr/bin/env python
#
# Module for adding GY30 light sensor functionality
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
import logging 
import datetime
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt
import DB

SLEEP_TIME = 0.5

DEVICE = 0x23 

ONE_TIME_HIGH_RES_MODE_1 = 0x20

NORMAL_MIN = 50
BRIGHT_MIN = 500

BRIGHT = 2
NORMAL = 1
DARK = 0

class GY30(object):

        def __init__(self, main_app_log):
                if main_app_log is None:

                        self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                        self.logFile = 'logs/GY30.log'

                        self.my_handler = RotatingFileHandler(self.logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
                        self.my_handler.setFormatter(self.log_formatter)
                        self.my_handler.setLevel(logging.INFO)

                        self.app_log = logging.getLogger('root')
                        self.app_log.setLevel(logging.INFO)

                        self.app_log.addHandler(self.my_handler)

                else:
                        self.app_log = main_app_log

                self.light_value = 0

                self._db = DB.DB()
                self._db.load_settings()

                self.start_mosquito()
                self.process_loop()

        def get(self, addr=DEVICE):
                try:
                        self._bus = smbus.SMBus(1)  
                        data = self._bus.read_i2c_block_data(addr,ONE_TIME_HIGH_RES_MODE_1)
                        self.light_value = int ((data[1] + (256 * data[0])) / 1.2)
                except Exception as e:
                        app_log.exception('Exception: %s', e)


        def on_connect(self, mosclient, userdata, flags, rc):
                self.app_log.info("Subscribing to topic: " + self._db.get_value("mostopic"))
                mosclient.subscribe(self._db.get_value("mostopic"))

        def on_disconnect(client, userdata, rc):
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
                x = 0
                old_value = 0

                while(1):
                        try:
                                self.get()      
                                message = str(self.light_value) 
                                if old_value != self.light_value or x == 0:
                                        self.broadcast_send('light', message)

                                old_value = self.light_value

                                logging.info(message)
                                if x < 10:
                                        x = x + 1
                                else:
                                        x = 0

                        except Exception as e:  
                                app_log.exception('Exception: %s', e)

                        finally:
                                time.sleep(SLEEP_TIME)
def run_program(main_app_log):
        GY30(main_app_log)

if __name__ == "__main__":
        run_program(None)
