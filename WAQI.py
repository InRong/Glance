import json, requests
from requests.exceptions import ConnectionError
import time
import datetime
import logging
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt
import DB

import sys

SLEEP_TIME = 30

class WAQI(object):

	def __init__(self, main_app_log):

		if main_app_log is None:

		        self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

        		self.logFile = 'logs/WAQI.log'

	        	self.my_handler = RotatingFileHandler(self.logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
        		self.my_handler.setFormatter(self.log_formatter)
        		self.my_handler.setLevel(logging.INFO)

	        	self.app_log = logging.getLogger('root')
        		self.app_log.setLevel(logging.INFO)

	        	self.app_log.addHandler(self.my_handler)

		else:
	        	self.app_log = main_app_log

		self._PM10 = ""		
		self._Humidity = "" 		
		self._Pressure = ""		
		self._SO2 = "" 		
		self._PM25 = "" 		
		self._Wind = "" 		
		self._Temperature = "" 		
		self._O3 = "" 	
		self._NO2 = "" 		
		self._Time = "" 		
		self._DominentPol = "" 		
		self._AQI = ""
		self._City = ""

                self._db = DB.DB()
                self._db.load_settings()
 
                self.start_mosquito()
 		self.process_loop()

	def get_aq(self):
        	url = requests.get('http://api.waqi.info/feed/here/?token=' + self._db.get_value("WAQItoken"))

		self.app_log.info(url.text)


       		aq = json.loads(url.text)

		self.app_log.info(aq)

		self._PM10 = str( aq['data']['iaqi']['pm10']['v'])		
		self._Humidity = str( aq['data']['iaqi']['h']['v'])		
		self._Pressure = str( aq['data']['iaqi']['p']['v'])		
		self._SO2 = str( aq['data']['iaqi']['so2']['v'])		
		self._PM25 = str( aq['data']['iaqi']['pm25']['v'])		
		self._Wind = str( aq['data']['iaqi']['w']['v'])		
		self._Temperature = str( aq['data']['iaqi']['t']['v'])		
		self._O3 = str( aq['data']['iaqi']['o3']['v'])		
		self._NO2 = str( aq['data']['iaqi']['no2']['v'])		
		self._Time = str(aq['data']['time'])		
		self._DominentPol = str(aq['data']['dominentpol'])		
		self._AQI = str(aq['data']['aqi'])		
		self._City = str(aq['data']['city']['name'])		

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
			message =  self._db.get_value("name") + "/" + data_item + "/" + value
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
				self.get_aq()
		
				#This is broadcast every minute, if valid
				if len(self._AQI) > 0:
					aq_value = int(self._AQI)
					aq_desc = ""
	
					if aq_value < 51:
						aq_desc = "Good"		
						self.broadcast_send("WAQI_AQI_HML", "green" )
					elif aq_value < 101:
						aq_desc = "Moderate"		
						self.broadcast_send("WAQI_AQI_HML", "yellow" )
					elif aq_value < 151:
						aq_desc = "Unhealthy for Sensitive Groups"
						self.broadcast_send("WAQI_AQI_HML", "amber" )
					elif aq_value < 201:
						aq_desc = "Unhealthy"		
						self.broadcast_send("WAQI_AQI_HML", "red" )
					elif aq_value < 300:
						aq_desc = "Very Unhealthy"		
						self.broadcast_send("WAQI_AQI_HML", "red" )
					elif aq_value > 299:
						aq_desc = "Hazardous"		
						self.broadcast_send("WAQI_AQI_HML", "H" )

					self.broadcast_send("WAQI_AQI_" + self._City, "AQ: " + self._AQI + " (" + aq_desc + ")")


			except Exception as e:
                        	self.app_log.exception('Exception: %s', e)
			finally:
				time.sleep(SLEEP_TIME)


def run_program(main_app_log):
	aq = WAQI(main_app_log)

if __name__ == '__main__':
        run_program(None)



