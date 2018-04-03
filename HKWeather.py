# -*- coding: utf-8 -*-
import urllib2, urllib, json
import time
import datetime
import feedparser
import DB
import logging
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt

SLEEP_TIME = 60

class HKWeather(object):

        def __init__(self, main_app_log):

                if main_app_log is None:

                        self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                        self.logFile = 'logs/HKWeather.log'

                        self.my_handler = RotatingFileHandler(self.logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
                        self.my_handler.setFormatter(self.log_formatter)
                        self.my_handler.setLevel(logging.INFO)

                        self.app_log = logging.getLogger('root')
                        self.app_log.setLevel(logging.INFO)

                        self.app_log.addHandler(self.my_handler)

                else:
                        self.app_log = main_app_log

		self._humidity = ""
		self._temperature = ""

                self._db = DB.DB()
                self._db.load_settings()

                self.start_mos()
                self.process_loop()

	def get(self):
		self._humidity = ""
		self._temperature = ""
		targeturl = 'http://rss.weather.gov.hk/rss/CurrentWeather.xml' 

		d = feedparser.parse(targeturl) 

		if len(d.entries) > 0:
			desc =  d.entries[0].description.split('Air temperature : ')
			self._temperature =  desc[1][:2].strip()
			desc =  d.entries[0].description.split(' Relative Humidity : ')
			self._humidity =  desc[1][:3].strip()

			logging.info(self._humidity + "%")
			logging.info(self._temperature + "C")
		else:
			logging.info("No entries returned")

	def getunits(self, which_units):
		if which_units == "temperature":
			return (u'\N{DEGREE SIGN}' + 'C')

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


	def process_loop(self):
		x = 10
		while(1):
			try:
				#Data is refreshed every 10 minutes
				if x == 10:
					x = 0
					self.get()
				else:
					x = x + 1

				#This is broadcast every minute, if valid
				if len(self._temperature) > 0:
                                        message =  self._db.get_value("name") + "/HK Weather/Outside: " + self._temperature + self.getunits("temperature") + " " + self._humidity +  self.getunits("humidity")
                                        self.mos_client.publish(self._db.get_value("mostopic"), message)
                                        self.app_log.info("Sent - " + message)
                                else:
                                        self.app_log.info("Nothing Sent")
			except Exception as e:
                        	logging.exception('Exception: %s', e)
			finally:
				time.sleep(SLEEP_TIME)


def run_program(main_app_log):
	HKWeather(main_app_log)

if __name__ == '__main__':
	run_program(None)

