#!/usr/bin/env python
#
# Copyright 2018 Peter Juett
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

# References (Wireshark reverse engineering) https://github.com/softScheck/tplink-smartplug/blob/master/tplink-smartplug.py

import time
import logging
import paho.mqtt.client as mqtt
import DB
from logging.handlers import RotatingFileHandler
import socket
import json

SLEEP_TIME = 3

ips = [None]*10

class HS100(object) :

        # Predefined Smart Plug Commands
        commands = {            'info'     : '{"system":{"get_sysinfo":{}}}',
                                'on'       : '{"system":{"set_relay_state":{"state":1}}}',
                                'off'      : '{"system":{"set_relay_state":{"state":0}}}',
                                'cloudinfo': '{"cnCloud":{"get_info":{}}}',
                                'wlanscan' : '{"netif":{"get_scaninfo":{"refresh":0}}}',
                                'time'     : '{"time":{"get_time":{}}}',
                                'schedule' : '{"schedule":{"get_rules":{}}}',
                                'countdown': '{"count_down":{"get_rules":{}}}',
                                'antitheft': '{"anti_theft":{"get_rules":{}}}',
                                'reboot'   : '{"system":{"reboot":{"delay":1}}}',
                                'reset'    : '{"system":{"reset":{"delay":1}}}'
        }

        def __init__(self, main_app_log):

                if main_app_log is None:

                        self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                        self.logFile = './logs/HS100.log'

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

                self.socket_count = 0

                #Set up the socket ip addresses from the database
                while(self.socket_count < 10):
                        ip = self._db.get_value("hs100ip" + str(self.socket_count))
                        if ip == "":
                                break
                
                        ips[self.socket_count] = ip
                        self.socket_count = self.socket_count + 1 

                self.start_mos()
                self.process_loop()

        # Encryption and Decryption of TP-Link Smart Home Protocol
        # XOR Autokey Cipher with starting key = 171
        def encrypt(self, string):
                key = 171
                result = "\0\0\0\0"
                for i in string:
                        a = key ^ ord(i)
                        key = a
                        result += chr(a)
                return result

        def decrypt(self, string):
                key = 171
                result = ""
                for i in string:
                        a = key ^ ord(i)
                        key = ord(i)
                        result += chr(a)
                return result

        def send_command(self, in_ip, in_cmd):
                ip = in_ip
                cmd = self.commands[in_cmd]

                # Send command and receive reply
                try:
                        self.app_log.info("Sending command to HS100 -  " + ip + " " + cmd)
                        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock_tcp.connect((ip, 9999))
                        sock_tcp.settimeout(2)
                        sock_tcp.send(self.encrypt(cmd))
                        data = sock_tcp.recv(2048)
                        sock_tcp.close()
                        self.app_log.info("Command sent -  " + ip + " " + cmd)
                        return self.decrypt(data[4:])
                except (socket.error, socket.timeout) as err:
                        self.app_log.exception('Exception: %s', err)
                        return -1

        def get_relay_state(self, ip):
                self.app_log.info("get_relay_state with ip - " + ip)
                value = self.send_command(ip, "info")
                if value == -1: #error
                        return value
                data  = json.loads(value)
                return data['system']['get_sysinfo']['relay_state']

        def on_connect(self, mosclient, userdata, flags, rc):
                self.app_log.info("Subscribing to topic: " + self._db.get_value("mostopic"))
                mosclient.subscribe(self._db.get_value("mostopic"))

        def on_message(self, mosclient, userdata, msg):
                messageparts = str(msg.payload).split("/")
                if len(messageparts)==3 and messageparts[1] == "HS100":
                        full_command =  messageparts[2]
                        commd = full_command[-1]
                        self.app_log.info("Message received on mqtt: " + full_command)
                        ip =  full_command[0:len(messageparts[2])-1]
                        self.app_log.info(ip + " - " + full_command)
                        if commd == "+":
                                self.send_command(ip, 'on')
                        elif commd == "-":
                                self.send_command(ip, 'off')

        def on_disconnect(client, userdata, rc):
            if rc != 0:
                self.app_log.info("Unexpected disconnection")

        def on_publish(self, client, userdata, mid):
                self.app_log.info("on_publish - published " + str(mid))

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
#                       self.mos_client.loop_forever()



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
                #Poll for state change of device, so we can keep the swiches updates with the status - in case another type of switch was used. 
                while True:
                        value = ""

                        try:
                                self.app_log.info ("getting relay state for: " + ips[x])
                                value = self.get_relay_state(ips[x])
                        except Exception as e:
                                self.app_log.exception('Exception: %s', e)

                        self.app_log.info ("value is " + str(value))
                        
                        #send a message on change of state of the device
                        if value == 1:
                                self.broadcast_send("HS100_STATE", ips[x] + "+")
                                self.app_log.info("sending relay state - " + "/HS100_STATE/"  + ips[x] + "+")
                        elif value == 0 or value == -1:
                                self.broadcast_send("HS100_STATE", ips[x] + "-")
                                self.app_log.info("sending relay state - " + "/HS100_STATE/"  + ips[x] + "-")

                        time.sleep(SLEEP_TIME)

                        if x == self.socket_count-1:
                                x = 0
                        else:
                                x = x + 1

def run_program(main_app_log):
        HS100(main_app_log)

if __name__ == '__main__':
        run_program(None)









