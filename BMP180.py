
#!/usr/bin/env python
#
# Module provided BMP180 sensor support
#
# by Peter Juett
# References:https://learn.adafruit.com/bmp085/downloads
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
import datetime
import Adafruit_BMP.BMP085 as BMP085
import time
import logging
import paho.mqtt.client as mqtt
import DB
from logging.handlers import RotatingFileHandler

SLEEP_TIME = 10

class BMP180(object) :

        def __init__(self, main_app_log):
                if main_app_log is None:

                        self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                        self.logFile = 'logs/BMP180.log'

                        self.my_handler = RotatingFileHandler(self.logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
                        self.my_handler.setFormatter(self.log_formatter)
                        self.my_handler.setLevel(logging.INFO)

                        self.app_log = logging.getLogger('root')
                        self.app_log.setLevel(logging.INFO)

                        self.app_log.addHandler(self.my_handler)

                else:
                        self.app_log = main_app_log

                self._sensor = BMP085.BMP085()
                self._temperature = ""
                self._pressure = ""
                self._altitude = ""

                self._db = DB.DB()
                self._db.load_settings()

                self.start_mos()
                self.process_loop()

        def get(self):
                self._temperature = str(int(self._sensor.read_temperature()))
                self._pressure = str(int(self._sensor.read_pressure()))
                self._altitude = '{0:0.1f}'.format(self._sensor.read_altitude())

        def getunits(self, which_units):
                if which_units == "temperature":
                        return ('\N{DEGREE SIGN}' + 'C')

                if which_units == "pressure":
                        return ("Pa")

                if which_units == "altitude":
                        return ("m")

        def process_loop(self):
                while(1):
                        try:
                                self.get()
                                if len(self._temperature)>0:
                                        self.broadcast_send("temperature from BMP180", "Inside: " + self._temperature + self.getunits("temperature"))
                                        self.broadcast_send("pressure from BMP180", self._pressure + self.getunits("pressure"))
                                        self.broadcast_send("altitude from BMP180", self._altitude + self.getunits("altitude"))
                        except Exception as e:
                                self.app_log.exception('Exception: %s', e)
                        finally:
                                time.sleep(SLEEP_TIME)

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
def run_program(main_app_log):
        BMP180(main_app_log)

if __name__=="__main__":
        BMP180(None)





