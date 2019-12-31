#!/usr/bin/env python
#
# Module for interfacing the system with the I2CIO module PCF8574
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
import smbus
import paho.mqtt.client as mqtt
import DB
from logging.handlers import RotatingFileHandler
import threading

SLEEP_TIME = 1
ADDRESS = 0x27
buzzer = False


class SensorBoard(object) :
        def __init__(self, main_app_log):

                if main_app_log is None:

                        self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                        self.logFile = 'logs/SensorBoard.log'

                        self.my_handler = RotatingFileHandler(self.logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
                        self.my_handler.setFormatter(self.log_formatter)
                        self.my_handler.setLevel(logging.INFO)

                        self.app_log = logging.getLogger('root')
                        self.app_log.setLevel(logging.INFO)

                        self.app_log.addHandler(self.my_handler)

                else:
                        self.app_log = main_app_log

                self.beep_state = False
                self.last_beep_on = False
                self.beep_on = False

                self._last_written_value = 0 #initialize to start.
                self._bus = smbus.SMBus(1)

                self._db = DB.DB()
                self._db.load_settings()

                self.start_mos()

                self.write_byte(0x00)

                self.automation1_timer = threading.Timer(0.5,self.automation1())
                self.automation1_timer.start()

        def automation1(self):
                last_pir = ""
                result = ""
                mid = ""

                while(1):
                        try:

                                io_status = self.get()
                                self.app_log.info("sensor board io_status...")
                                self.app_log.info(io_status)

                                #deal with the PIR
                                if (io_status & 64):
                                        if last_pir != "on":
                                                last_pir = "on"
                                                result, mid = self.mos_client.publish(self._db.get_value("mostopic"), self._db.get_value("name") + "/PIR/on")
                                                self.app_log.info("sending on")
                                                self.app_log.info(mid)
                                else:
                                        if last_pir != "off":
                                                result, mid = self.mos_client.publish(self._db.get_value("mostopic"), self._db.get_value("name") + "/PIR/off")
                                                last_pir = "off"
                                                self.app_log.info("sending off")
                                                self.app_log.info(mid)


                                #deal with the buzzer
                                if self.beep_on:
                                        self.write_bit(7, self.beep_state)
                                        self.beep_state =  not self.beep_state
                                else:
                                        if self.last_beep_on: #the beeper (alarm) has just been switched off, so send the off command, so the beep does not stick on!
                                                self.write_bit(7, False)
#                                               self.beep_state =  False #and reset the beep_state, so thet sync (and the time display wil be properly on)

                                self.last_beep_on = self.beep_on

                        except Exception as e:
                                self.app_log.exception('Exception: %s', e)
                        finally:
                                time.sleep(SLEEP_TIME)

        def on_connect(self, mosclient, userdata, flags, rc):
                self.app_log.info("Subscribing to topic: " + self._db.get_value("mostopic"))
                mosclient.subscribe(self._db.get_value("mostopic"))

        def on_message(self, mosclient, userdata, msg):
                messageparts = str(msg.payload).split("/")
                if len(messageparts)==3:
                        incoming = messageparts[0] + "/" + messageparts[1]

                        #command is 1+, 2+ etc to turn high, 1-, 2- etc low
                        if messageparts[0] == self._db.get_value("name") and  messageparts[1] == "I2CIO":
                                self.app_log.info("Incoming - " + incoming + "/" + messageparts[2])

                                switch_on = (messageparts[2][-1:] == "+") #Last character should be + or -

                                if "buzzer" in messageparts[2]:
                                        self.beep_on = switch_on
                                else:
                                        self.write_bit(int(messageparts[2][:1]), switch_on)

        def start_mos(self):
                self.mos_client = mqtt.Client()
                self.mos_client.on_connect = self.on_connect
                self.mos_client.on_message = self.on_message

                if len(self._db.get_value("mospassword"))>0:
                        self.mos_client.username_pw_set(self._db.get_value("mosusername"),self._db.get_value("mospassword"))

                logging.info("Connecting to: " + self._db.get_value("mosbrokeraddress"))

                self.mos_client.connect(self._db.get_value("mosbrokeraddress"), int(self._db.get_value("mosbrokerport")), 60)

                logging.info("Connected")
                self.mos_client.loop_start()

        def get(self):
                return self._bus.read_byte(ADDRESS)

        def write_byte(self,to_write):
                self._bus.write_byte(ADDRESS, to_write)
                self._last_written_value = to_write

        def write_bit(self, bit, state):

                overlay_value = 2**bit

                if state == True:
                        to_write = self._last_written_value | overlay_value
                        self.write_byte(to_write)

                else:
                        to_write = self._last_written_value & (0xFF - overlay_value)
                        self.write_byte(to_write)

def run_program(main_app_log):
        sensor_board = SensorBoard(main_app_log)

if __name__ == '__main__':
        run_program(None)









