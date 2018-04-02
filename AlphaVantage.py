# -*- coding: utf-8 -*-
import urllib2, urllib, json
import time
import datetime
import traceback
import os
import DB
import logging
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt
import decimal

SLEEP_TIME = 60

class AlphaVantage(object):

	def __init__(self, main_app_log):
		self._symbol = ""
		self._stock_last_refreshed = ""
		self._close =  ""

		self._from_currency =  ""
		self._to_currency =  ""
		self._exchange_rate = ""
		self._currency_last_refreshed = ""

		if main_app_log is None:
	                self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

        	        self.logFile = 'logs/AlphaVantage.log'

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

	def get_stock(self, symbol):
		self._symbol = symbol
		self._stock_last_refreshed = ""
		self._close = ""
	
		baseurl = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=" + symbol + "&apikey=" + self._db.get_value("alphavantageapikey")
		result = urllib2.urlopen(baseurl).read()
		data = json.loads(result)
		self.app_log.info(data)

		self._symbol =  data['Meta Data']['2. Symbol']
		self._stock_last_refreshed =  data['Meta Data']['3. Last Refreshed']
		self._close = data['Time Series (Daily)'][self._stock_last_refreshed]['4. close']
		D = decimal.Decimal
		self._closef = D(self._close)


	def get_currency(self, from_currency, to_currency):
		self._from_currency = from_currency
		self._to_currency = to_currency
		self._exchange_rate = ""
		self._currency_last_refreshed = ""
	
		baseurl = "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=" + from_currency + "&to_currency=" + to_currency + "&apikey=" + self._db.get_value("alphavantageapikey")
		result = urllib2.urlopen(baseurl).read()
		data = json.loads(result)
		self.app_log.info(data)

		self._from_currency =  data['Realtime Currency Exchange Rate']['1. From_Currency Code']
		self._to_currency =  data['Realtime Currency Exchange Rate']['3. To_Currency Code']
		self._exchange_rate = data['Realtime Currency Exchange Rate']['5. Exchange Rate']
		D = decimal.Decimal
		self._exchange_ratef = D(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
		self._currency_last_refreshed = data['Realtime Currency Exchange Rate']['6. Last Refreshed']


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

				self.get_currency(self._db.get_value("alphavantagefromcurrency1"), self._db.get_value("alphavantagetocurrency1"))
		
				if len(self._exchange_rate) > 0:
               	                        message =  self._db.get_value("name") + "/AlphaVantage Exchange Rate/" + self._from_currency + self._to_currency + " " + "{:.2f}".format(self._exchange_ratef)
					self.mos_client.publish(self._db.get_value("mostopic"), message)
					self.app_log.info("Sent " + message)
				else:
					self.app_log.info("Nothing Sent")

				if len(self._currency_last_refreshed) > 0:
                       	                message =  self._db.get_value("name") + "/AlphaVantage Exchange Rate Last Refreshed/" + self._from_currency + self._to_currency + " Date " + self._currency_last_refreshed
					self.mos_client.publish(self._db.get_value("mostopic"), message)
					self.app_log.info("Sent " + message)

				else:
					self.app_log.info("Nothing Sent")

				self.get_stock(self._db.get_value("alphavantagestock1"))
				#This is broadcast every minute, if valid
				if len(self._close) > 0:
               	                        message =  self._db.get_value("name") + "/AlphaVantage Stock Close/" + self._symbol + " Close " + "{:.2f}".format(self._closef)
					self.mos_client.publish(self._db.get_value("mostopic"), message)
					self.app_log.info("Sent " + message)
				else:
					self.app_log.info("Nothing Sent")

				if len(self._stock_last_refreshed) > 0:
                       	                message =  self._db.get_value("name") + "/AlphaVantage Stock Last Refreshed/" + self._symbol + " Date " + self._stock_last_refreshed
					self.mos_client.publish(self._db.get_value("mostopic"), message)
					self.app_log.info("Sent " + message)
				else:
					self.app_log.info("Nothing Sent")

		
                	except Exception as e:
                        	self.app_log.exception('Exception: %s', e)
	                finally:
        	                time.sleep(SLEEP_TIME)

def run_program(main_app_log):
        AlphaVantage(main_app_log)

if __name__ == '__main__':
        run_program(None)



