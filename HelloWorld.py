import time
import logging
import paho.mqtt.client as mqtt
import DB
from logging.handlers import RotatingFileHandler
import threading

SLEEP_TIME = 1

class HelloWorld(object) :
	def __init__(self, main_app_log):
		try:
	                if main_app_log is None:

        	                self.log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                	        self.logFile = 'logs/HelloWorld.log'

	                        self.my_handler = RotatingFileHandler(self.logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
        	                self.my_handler.setFormatter(self.log_formatter)
                	        self.my_handler.setLevel(logging.INFO)

	                        self.app_log = logging.getLogger('root')
        	                self.app_log.setLevel(logging.INFO)

                	        self.app_log.addHandler(self.my_handler)

	                else:
        	                self.app_log = main_app_log

			self._data = "Hello World"

			self._db = DB.DB()
			self._db.load_settings()
			self.start_mosquito()
        	        self.publish_loop()

                except Exception as e:
                        app_log.exception('Exception: %s', e)


	def on_connect(self, mosclient, userdata, flags, rc):
		try:
	        	self.app_log.info("Subscribing to topic: " + self._db.get_value("mostopic"))
		        mosclient.subscribe(self._db.get_value("mostopic"))
                except Exception as e:
                        app_log.exception('Exception: %s', e)

	def on_message(self, mosclient, userdata, msg):
		try:
	               	messageparts = str(msg.payload).split("/")
        	       	if len(messageparts)==3:
				#Receive an incoming message and perform an action accordingly.
                       		if messageparts[0] == self._db.get_value("name"):
					self.app_log.info("Incoming - " + str(msg.payload))
					if messageparts[1] == "SetHelloWorld":
						self.set_data(messageparts[2])
                except Exception as e:
                        app_log.exception('Exception: %s', e)

	def start_mosquito(self):
		try:
	       		self.mos_client = mqtt.Client()
        	       	self.mos_client.on_connect = self.on_connect
               		self.mos_client.on_message = self.on_message

	               	if len(self._db.get_value("mospassword"))>0:
        	        	self.mos_client.username_pw_set(self._db.get_value("mosusername"),self._db.get_value("mospassword"))

	               	logging.info("Connecting to: " + self._db.get_value("mosbrokeraddress"))

        	       	self.mos_client.connect(self._db.get_value("mosbrokeraddress"), int(self._db.get_value("mosbrokerport")), 60)

	               	logging.info("Connected")
        	       	self.mos_client.loop_start()
                except Exception as e:
                        app_log.exception('Exception: %s', e)

	def get_data(self):
		try:
	        	return self._data #For use in a real situation, this would be replaced with code to get the data e.g. GPIO status
                except Exception as e:
                        app_log.exception('Exception: %s', e)

	def set_data(self,new_data):
		try:
			self._data = new_data
                except Exception as e:
                        app_log.exception('Exception: %s', e)

	def publish_loop(self):
		while(1):
			try:
				#share the data every second by sending the data onto the Mosquito 
				#Message format is <source host>/<Message Name>/<Message Value>
				#In our case here, initially, "Bedroom Touch/HelloWorld/Hello World"
	                	self.mos_client.publish(self._db.get_value("mostopic"), self._db.get_value("name") + "/HelloWorld/" + self.get_data())
        	        except Exception as e:
                	        app_log.exception('Exception: %s', e)
			finally:
				time.sleep(SLEEP_TIME)

def run_program(main_app_log):
	HelloWorld(main_app_log)

if __name__ == '__main__':
        run_program(None)


