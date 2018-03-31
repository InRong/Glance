import kivy 
kivy.require('1.0.6') 

from threading import Thread 

from kivy.app import App 
from kivy.clock import Clock 
from kivy.graphics import Color, Rectangle 

from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import Screen, ScreenManager 
from kivy.uix.popup import Popup

import paho.mqtt.client as mqtt
import datetime
import utils
import DB
import time
import os
import myemail
import Event

import logging
from logging.handlers import RotatingFileHandler

main_application = None
app_log = None

class DataLabel(Label):
	def update(self, dt):
		if self.id=="35":
			if (utils.is_odd_seconds() or main_application.db.get_value('flashingtime') == "off"):
				self.text = ":"
				if main_application.db.get_value("timestyle")=="12" and len(utils.get_time_h_12())<2:
					self.pos_hint={'x':-0.33, 'y':0.15}
				else:
					self.pos_hint={'x':-0.28, 'y':0.15}
			else:
				self.text = ""
		else:	
			self.text = main_application.display_text[int(self.id)]

class PIRImage(Image):
	def update(self, dt):
#		if motion_value:		
		if main_application.display_text[12]=="on":		
			self.opacity = 1.0
		else:
			self.opacity = 0

class IndicatorImage(Image):

	def update(self, dt):
		pic = self.get_picture()

		if pic!="":		
			self.source = pic
			self.opacity = 1.0
		else:
			self.opacity = 0

	def get_picture(self):
		if main_application.air_quality == "green":
			return "Pictures/greensmiley.jpg"
		elif main_application.air_quality == "yellow":
			return "Pictures/ambersmiley.jpg"
		elif main_application.air_quality == "amber":
			return "Pictures/ambersmiley.jpg"
		elif main_application.air_quality == "red":
			return "Pictures/redsmiley.jpg"

		return ""

class MyToggleButton(ToggleButton):
	def callback(self, event):
		if self.state == "down":
			main_application.send_message_set("button" + self.id + "on")
		else:
			main_application.send_message_set("button" + self.id + "off")

class MyButton(Button):
	def callback(self, event):
		main_application.send_message_set("button" + self.id + "on")

class MainScreen(Screen):
	def __init__ (self,**kwargs):

		app_log.info("started")

		data_label = [None]*12

     		self._touch_down_x = 0
       		self._touch_down_y = 0

        	super (MainScreen, self).__init__(**kwargs)

		layout = FloatLayout(size=(800, 600))

		data_label[1] = DataLabel(id="1", font_size='46pt', pos_hint={'x':0, 'y':0.44})
    		data_label[1].color = [1.0,1.0,1.0,1.0]
		Clock.schedule_interval(data_label[1].update, 1)

		data_label[2] = DataLabel(id="2", font_size='22pt', pos_hint={'x':0, 'y':0.33})
    		data_label[2].color = [1.0,1.0,1.0,1.0]
		Clock.schedule_interval(data_label[2].update, 1)

		if main_application.db.get_value("timestyle")=="12":
			data_label[3] = DataLabel(id="3", font_size='96pt', pos_hint={'x':-0.28, 'y':0.13})
    			data_label[3].color = [1.0,1.0,0.0,1.0]
			Clock.schedule_interval(data_label[3].update, 0.1)

			colon_label = DataLabel(id="35", font_size='96pt', pos_hint={'x':-0.32, 'y':0.15})
    			colon_label.color = [1.0,1.0,0.0,1.0]
			Clock.schedule_interval(colon_label.update, 0.1)
		else:
			data_label[3] = DataLabel(id="3", font_size='96pt', pos_hint={'x':-0.28, 'y':0.13})
    			data_label[3].color = [1.0,1.0,0.0,1.0]
			Clock.schedule_interval(data_label[3].update, 0.1)

			colon_label = DataLabel(id="35", font_size='96pt', pos_hint={'x':-0.28, 'y':0.15})
    			colon_label.color = [1.0,1.0,0.0,1.0]
			Clock.schedule_interval(colon_label.update, 0.1)

		data_label[4] = DataLabel(id="4", font_size='22pt',  pos_hint={'x':-0.28, 'y':-0.02})
   		data_label[4].color = [1.0,1.0,0,1.0]
		Clock.schedule_interval(data_label[4].update, 1)

		data_label[5] = DataLabel(id="5", font_size='22pt', pos_hint={'x':-0.28, 'y':-0.10})
    		data_label[5].color = [1.0,1.0,1.0,1.0]
		Clock.schedule_interval(data_label[5].update, 1)

		data_label[6] = DataLabel(id="6", font_size='22pt', pos_hint={'x':-0.28, 'y':-0.18})
    		data_label[6].color = [1.0,1.0,1.0,1.0]
		Clock.schedule_interval(data_label[6].update, 1)


		data_label[7] = DataLabel(id="7", font_size='36pt',  pos_hint={'x':0.21, 'y':0.19})
   		data_label[7].color = [0,1.0,0,1.0]
		Clock.schedule_interval(data_label[7].update, 1)

		data_label[8] = DataLabel(id="8", font_size='36pt', pos_hint={'x':0.21, 'y':0.07})
    		data_label[8].color = [0,1.0,0,1.0]
		Clock.schedule_interval(data_label[8].update, 1)

		data_label[9] = DataLabel(id="9",font_size='36pt', pos_hint={'x':0.21, 'y':-0.05})
    		data_label[9].color = [0,1.0,0,1.0]
		Clock.schedule_interval(data_label[9].update, 1)

		data_label[10] = DataLabel(id="10", font_size='36pt', pos_hint={'x':0.21, 'y':-0.17})
    		data_label[10].color = [0,1.0,0,1.0]
		Clock.schedule_interval(data_label[10].update, 1)


		data_label[11] = DataLabel(id="11", font_size='22pt', pos_hint={'x':0, 'y':-0.29})
    		data_label[11].color = [1.0,1.0,1.0,1.0]
		Clock.schedule_interval(data_label[11].update, 1)

		#get the button count
		main_application.button_count = 0
		for btn_loop in range(0, 8):
			str_btn_loop = str(btn_loop)
			if len(main_application.db.get_value("button" + str_btn_loop  + "alias"))>0:
				main_application.button_count = main_application.button_count + 1
			else:
				break

		button_position = round(1.00 / main_application.button_count,2)
		button_size = button_position - 0.01

		for btn_loop in range(0, main_application.button_count):
			str_btn_loop = str(btn_loop)
			alias = main_application.db.get_value("button" + str_btn_loop  + "alias")
			button_type = main_application.db.get_value("button" + str_btn_loop  + "type")
			if len(alias)>0:
				if button_type == "button":
					main_application.settings_buttons[btn_loop] = MyButton(id=str_btn_loop, text=alias ,size_hint=(button_size, 0.1), pos_hint={'x':0.01 + (btn_loop * button_position), 'y':0.02})
				else:
					main_application.settings_buttons[btn_loop] = MyToggleButton(id=str_btn_loop, text=alias ,size_hint=(button_size, 0.1), pos_hint={'x':0.01 + (btn_loop * button_position), 'y':0.02})

				main_application.settings_buttons[btn_loop].bind(on_press=main_application.settings_buttons[btn_loop].callback)
				layout.add_widget(main_application.settings_buttons[btn_loop])
			else:
				break
		
		#Images
		pir_image = PIRImage(source = 'Pictures//pir.jpg', pos_hint={'x':-0.42, 'y':0.38})
		Clock.schedule_interval(pir_image.update, 0.1)

		indicator_image = IndicatorImage(pos_hint={'x':0.42, 'y':0.38})
		Clock.schedule_interval(indicator_image.update, 1)

		Clock.schedule_interval(main_application.automation1, 0.5)

		for x in range(1, 12):
			layout.add_widget(data_label[x])

		layout.add_widget(colon_label)
		layout.add_widget(pir_image)
		layout.add_widget(indicator_image)

		self.add_widget(layout)


        def on_touch_down(self, touch):
		if touch.y > 90: #above the button area
			if not main_application.get_screen():#if the screen is off
				main_application.send_message_set("screensingletouchon")
			else:
				main_application.send_message_set("screensingletouchoff")

		main_application.last_event = None

		super(MainScreen, self).on_touch_down(touch)


class MyApp(App):
	global app_log

	def build(self):
		#Initialization
		self.last_pir_time = time.time()
		self.away = False
		self.started = False

		self.display_text=[None]*13
		self.display_update = [None]*13
		self.settings_buttons = [None]*10
		for x in range(1,8):
			self.settings_buttons[x] = ""

		for x in range(0, 13):
			self.display_text[x]=""
			self.display_update[x]=time.time()

		self.light_value = 0
		self.last_light_message = ""

		self.temperature_value = 0
		self.last_temperature_message = ""

		self.humidity_value = 0
		self.last_humidity_message = ""

		self.motion_value = False

		self.last_event = None

		self.button_count = 0

		self.STALE_DATA_SECONDS = 700		

		self.last_mins = 99
		self.air_quality = ""

		self.file_modified_time_at_last_read = time.time()

		#end initialisation

		self.db = DB.DB()
		self.read_settings()

		self.my_screenmanager = ScreenManager()

		self.main_screen = MainScreen(name='main_screen')
		self.my_screenmanager.add_widget(self.main_screen)

		self.start_mosquitto()

		self.started = True

		return self.my_screenmanager

	def read_settings(self):
		try:
			if self.db.get_value("confirmationbeep") == "on" and self.started:
				audio.play_beep()

			self.file_modified_time_at_last_read = time.ctime(os.path.getmtime(self.db.get_file_path()))	

			self.db.load_settings()
			app_log.info("settings reloaded")
        
	        except Exception as e:
        	        app_log.exception('Exception: %s', e)

	def start_mosquitto(self):
		try:
			self.mos_client = mqtt.Client()
			self.mos_client.on_connect = self.on_connect
			self.mos_client.on_message = self.on_message

			if len(self.db.get_value("mospassword"))>0:
				self.mos_client.username_pw_set(self.db.get_value("mosusername"),self.db.get_value("mospassword"))

	                mos_broker_address = self.db.get_value("mosbrokeraddress")

			app_log.info("Connecting to " + mos_broker_address)

	                self.mos_client.connect(mos_broker_address, int(self.db.get_value("mosbrokerport")), 60)

			self.mos_client.loop_start()
	        except Exception as e:
               		app_log.exception('Exception: %s', e)


	# The callback for when the client receives a CONNACK response from the server.
	def on_connect(self, mosclient, userdata, flags, rc):
    		app_log.info("Connected with result code "+str(rc))

	    	# Subscribing in on_connect() means that if we lose the connection and
    		# reconnect then subscriptions will be renewed.
		try:    
			app_log.info("Subscribing to topic: " + self.db.get_value("mostopic"))
			mosclient.subscribe(self.db.get_value("mostopic"))
	        except Exception as e:
        	        app_log.exception('Exception: %s', e)

	# The callback for when a PUBLISH message is received from the server.
	def on_message(self, mosclient, userdata, msg):
		try:
			msg_payload = str(msg.payload) 

			message_parts = msg_payload.split("/")

			app_log.info(message_parts)

			if len(message_parts)==3:
				incoming = message_parts[0] + "/" + message_parts[1] + "/" 

				#read the selected sensor data			
				if incoming == self.db.get_message("lightsensor"):
					light_value =  int(message_parts[2])
					if light_value <= self.db.get_int_value("normallight"):
						if self.last_light_message!="lighton":
							self.send_message_set("lighton")
							self.last_light_message="lighton"

					elif light_value >= self.db.get_int_value("brightlight"):
						if self.last_light_message!="lightoff":
							self.send_message_set("lightoff")
							self.last_light_message="lightoff"

				elif incoming == self.db.get_message("temperaturesensor"):
					temperature_value =  int(message_parts[2])
				
					if temperature_value <= self.db.get_int_value("cold"):
						if self.last_temperature_message!="tempon":
							self.send_message_set("tempon")
							self.last_temperature_message="tempon"

					elif self.temperature_value >= self.db.get_int_value("hot"):
						if self.last_temperature_message!="tempoff":
							self.send_message_set("tempoff")
							self.last_temperature_message="tempoff"

				elif incoming == self.db.get_message("humiditysensor"):
					humidity_value =  int(message_parts[2])

					if humidity_value <= self.db.get_int_value("dry"):
						if self.last_humidty_message!="humidityon":
							self.send_message_set("humidityon")
							self.last_humidity_message="humidityon"

					elif humidity_value >= self.db.get_int_value("humid"):
						if self.last_humidity_message!="humidityoff":
							self.send_message_set("humidityoff")
							self.last_humidity_message="humidityoff"

				elif incoming == self.db.get_message("motionsensor"):
					self.motion_value = (message_parts[2] == "on")
					if self.motion_value:
						self.trigger_action_on_motion()						

				#If it is a screen command for this host
				elif message_parts[1] == "screen": 
					if message_parts[0] == self.db.get_value("name"):
						app_log.info ("screen message, value is " + message_parts[2][-1:])
						self.set_screen(message_parts[2][-1:]=="+")
				
				elif message_parts[1] == "dismiss popup": 
					self.popup.dismiss()

				elif message_parts[1] == "popup": 
					if last_event is not None:
						if not self.get_screen():#if the screen is off, turn it on
							self.set_screen(True)

						self.popup = Popup(title='Alert!!!', content=Label(text=last_event.friendly_name + " " + last_event.description), size_hint=(None, None), size=(200, 200))
						self.popup.bind(on_dismiss=self.popup_callback)
						self.popup.open()

				elif incoming == self.db.get_message('indicatorswitch'):
					self.air_quality =  message_parts[2]
					app_log.info ("air quality is " + self.air_quality)


				#Populate the display strings
				for x in range(1, 13):
					if self.db.get_message("display" + str(x)) == incoming: 
						self.display_text[x] = message_parts[2]
						self.display_update[x] = time.time()


				#synch up the toggle buttons for related messages from elsewhere. 
				for x in range(0, self.button_count):
					if  self.db.get_value("button" + str(x) + "type")=="togglebutton":
						button_on_message = self.db.get_message("button" + str(x) + "on-0") # the first command is the message that determins the state of the button. 
						if button_on_message is not None: 
							if button_on_message == msg_payload: 
					 			self.settings_buttons[x].state="down"
							elif "STATE" in msg_payload:
								button_on_message_parts = button_on_message.split('/')
								if len(button_on_message_parts)==3: 
									button_on_message_state = button_on_message_parts[0] + "/" + button_on_message_parts[1] + "_STATE/" + button_on_message_parts[2]
	                        		                	if button_on_message_state == msg_payload:
								 		self.settings_buttons[x].state="down"

						button_off_message = self.db.get_message("button" + str(x) + "off-0") # the first command is the message that determins the state of the button. 	
						if button_off_message is not None: 
							if button_off_message == msg_payload: 
						 		self.settings_buttons[x].state="normal"
							elif "STATE" in msg_payload:
								button_off_message_parts = button_off_message.split('/')
	
								if len(button_off_message_parts)==3: 
									button_off_message_state = button_off_message_parts[0] + "/" + button_off_message_parts[1] + "_STATE/" + button_off_message_parts[2]
	                        		            		if button_off_message_state == msg_payload:
								 		self.settings_buttons[x].state="normal"

	        except Exception as e:
        	        app_log.exception('Exception: %s', e)

	def is_data_current(self, index): 
		try:
			return time.time() - self.display_update[index] <= self.STALE_DATA_SECONDS
        	except Exception as e:
                	app_log.exception('Exception: %s', e)


	def popup_callback(self, instance):
		app_log.info('Popup', instance, 'is being dismissed')
	
		if self.last_event is not None:
			self.send_message_set(last_event.name + "off")
			self.last_event = None

	def automation1(self, dt):
		try:
			#check if the database has changed, if so, re-read it. 
			filemodifiedtime = time.ctime(os.path.getmtime(self.db.get_file_path()))	
			if(filemodifiedtime <> self.file_modified_time_at_last_read):
				self.read_settings()

			for x in range(1, 13):
				self.set_display(x, self.db.get_value("display" + str(x)))

			#Do we need to triger an event
			if (self.last_mins <> utils.get_mins()): #check once a minute 
				self.last_mins = utils.get_mins() 

			        event_list = Event.EventList()
				next_event = event_list.get_next_event(self.db)	

				if next_event.get_mins_until_event()==0: #then the event is now.
					app_log.info("time for event")
					app_log.info(next_event.name + "on")
					self.send_message_set(next_event.name + "on")
					self.last_event = next_event

	        except Exception as e:
        	        app_log.exception('Exception: %s', e)


	def set_display(self, digit, selection):

		try:
			#Time
			if selection == "@@time":
				if self.db.get_value("timestyle")=="12":
					self.display_text[digit]=utils.get_time_h_12() + " " + utils.get_time_hhmm()[2:4] 
 					self.display_update[digit]=time.time()
				else:
					self.display_text[digit]=utils.get_time_hhmm()[0:2] + " " + utils.get_time_hhmm()[2:4]
					self.display_update[digit]=time.time()

			#Seconds
			elif selection == "@@secs":
				self.display_text[digit]=utils.get_secs()
				self.display_update[digit]=time.time()

			#Date
			elif selection == "@@date":
				self.display_text[digit]= utils.short_day() + " " + str(datetime.datetime.today().day) + " " + utils.full_month()
				self.display_update[digit]=time.time()

			#Next Event
			elif selection == "@@nextevent":
			        event_list = Event.EventList()
				next_event = event_list.get_next_event(self.db)	
				if next_event is None:
					self.display_text[digit]= "No event set"
				else:
					self.display_text[digit]= next_event.day + " " + next_event.get_time(self.db.get_value("timestyle")=="24") + " " + next_event.description  
			
				self.display_update[digit]=time.time()

			#Mins until next Event
			elif selection == "@@minsuntilnextevent":
			        event_list = Event.EventList()
				next_event = event_list.get_next_event(self.db)	

				if next_event is None:
					self.display_text[digit]= "No event set"
				else:
					self.display_text[digit]= "Next in " + str(next_event.get_mins_until_event()) + " mins" 
			
				self.display_update[digit]=time.time()

			#Hours, Mins until next Event
			elif selection == "@@hoursminsuntilnextevent":
			        event_list = Event.EventList()
				next_event = event_list.get_next_event(self.db)	

				if next_event is None:
					self.display_text[digit]= "No event set"
				else:
					self.display_text[digit]= "Next in " + str(next_event.get_hours_mins_until_event())
			
				self.display_update[digit]=time.time()
	
			elif selection == "@@away":
				if away:
					self.display_text[digit] = "Away"
				else:
					self.display_text[digit] = ""

				self.display_update[digit]=time.time()

			elif selection == "@@off":
				self.display_text[digit]= ""

			if not self.is_data_current(digit):		
				self.display_text[digit]=""

	        except Exception as e:
        	        app_log.exception('Exception: %s', e)


	def send_message_set(self, set_name):
		Thread(target=self.send_messages,args=(set_name,)).start()

	def send_messages(self, set_name):
		app_log.info("set_name is .... " + set_name)

		for cmd_loop in range(0, 9):
			set_step = set_name + "-" + str(cmd_loop)
			message_id = self.db.get_value(set_step)

			#break because end of the steps. 
			if message_id == "-": 
				break

			message = self.db.get_message(set_step)
			app_log.info(message)
			app_log.info(set_step)
		
			if "If Away" in message:
				host, name, value = message.split("/")			
				if value=="if" and not away:
					break
				elif value=="not" and away:
					break
			elif "Pause" in message:
				host, name, value = message.split("/")			
				time.sleep(int(value))
			elif "Set Away" in message:
				host, name, value = message.split("/")			
				away = (value=="on")
			else:
			        result, mid = self.mos_client.publish(self.db.get_value("mostopic"), message)
	
			app_log.info("actioned message")

	def send_motion_email(self):
		try:
			myemail.send_email(self.db.get_value("gmailaddress"), self.db.get_value("motionaddress"), "motion", "motion detected", self.db.get_value("emailpassword"))	
	        except Exception as e:
        	        app_log.exception('Exception: %s', e)

	def send_event_non_dismiss_email(self):
		try:
			myemail.send_email(self.db.get_value("gmailaddress"), self.db.get_value("nondismissaddress"), "event", "event not dismissed within 2  minutes", self.db.get_value("emailpassword"))
	        except Exception as e:
        	        app_log.exception('Exception: %s', e)


	def trigger_action_on_motion(self):

		try:
			if (time.time()-self.last_pir_time <=8): #only fire this once per high
				return; 
 
			self.last_pir_time = time.time()

			self.send_message_set("motionon")

			if self.away:
				Thread(target=send_motion_email,args=()).start()

	        except Exception as e:
        	        app_log.exception('Exception: %s', e)


	def set_screen(self,desired_state):
	        f = open("/sys/class/backlight/rpi_backlight/bl_power","w")
        	if desired_state:
                	f.write("0")
	        else:
        	        f.write("1")
	        f.close()

	def get_screen(self):
        	f = open("/sys/class/backlight/rpi_backlight/bl_power","r")
	        ch  = f.read(1)
        	f.close()
	
	        return (ch == "0")

def run_program(main_app_log):
	global main_application
	global app_log

	if main_app_log is None:
        	log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

                logFile = 'logs/TouchScreen.log'

                my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024, backupCount=1, encoding=None, delay=0)
                my_handler.setFormatter(log_formatter)
                my_handler.setLevel(logging.INFO)

                app_log = logging.getLogger('root')
                app_log.setLevel(logging.INFO)

                app_log.addHandler(my_handler)
	else:
        	app_log = main_app_log

	try:
		main_application = MyApp()
		main_application.run()
        except Exception as e:
                app_log.exception('Exception: %s', e)

if __name__ == '__main__':
        run_program(None)

