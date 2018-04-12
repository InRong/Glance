#!/usr/bin/env python
#
# Module for Managing Events
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
import Utils
import DB

NUMBER_OF_EVENTS = 8

class Event(object):
	def __init__(self, event_index, event_hours, event_mins, week_mins, event_day, event_description):
        	self._index = event_index
		self._mins = event_mins
		self._hours = event_hours
		self._day = event_day
		self._week_mins = week_mins
		self._description = event_description

	def __cmp__(self,other):
		return cmp(self._week_mins,other._week_mins)

	def get_mins_until_event(self):
	        now_week_mins = (Utils.day_number()* 24 * 60) + (Utils.get_hours()*60) + Utils.get_mins()
		return self._week_mins - now_week_mins

	def get_hours_mins_until_event(self):
		return Utils.convert_mins_to_hours_mins(self.get_mins_until_event())

	@property
	def name(self):
		return "event" + str(self._index) 

	@property
	def friendly_name(self):
		return "event" + str(self._index + 1) 

	@property
	def description(self):
		return self._description

	@property
	def day(self):
		return self._day

	@property
	def mins(self):
		return self._mins

	@property
	def hours(self):
		return self._hours

	@property
	def week_mins(self):
		return self._week_mins

	def time_12(self):
		if self._hours > 13:
			return str(self._hours-12) + ":" + Utils.to_string_with_leading_zero(self._mins) + "pm"
		else:
			return str(self._hours) + ":" + Utils.to_string_with_leading_zero(self._mins) + "am"
	
	def time_24(self):
		return str(self._hours) + ":" + Utils.to_string_with_leading_zero(self._mins)

	def get_time(self, is_24):
		if is_24:
			return self.time_24()
		else:
			return self.time_12()

class EventList(object):

	def __init__(self):
		self._event_list = []

	@property
	def event_list(self):
		return self._event_list

	def get_next_event(self, db):

	        #Events are switched off
        	if db.get_value("eventson")=="off":
                	return None

	        now_mins = (Utils.day_number()* 24 * 60) + (Utils.get_hours()*60) + Utils.get_mins()

        	x = 0
	        while (x < NUMBER_OF_EVENTS):
                	event_time = db.get_value("event" + str(x) + "time")

	                if len(event_time)>2:

		                event = db.get_value("event" + str(x) + "days").lower()
		                event_description = db.get_value("event" + str(x) + "description")

	        	        if len(event)>2:

			                event_hours = int(event_time[:2]) #hours
        			        event_mins =  int(event_time[-2:]) #mins

		                	if "mon" in event or "weekday" in event or "everyday" in event:
                		        	week_mins = (0 * 24 * 60) + (event_hours*60) + event_mins
			                        my_event  = Event(x,event_hours,event_mins, week_mins, "Mon", event_description)
        			                self.event_list.append(my_event)

		                	if "tue" in event or "weekday" in event or "everyday" in event:
                		        	week_mins = (1 * 24 * 60) + (event_hours*60) + event_mins
	                        		my_event  = Event(x,event_hours,event_mins, week_mins, "Tue", event_description)
		        	                self.event_list.append(my_event)

                			if "wed" in event or "weekday" in event or "everyday" in event:
		                        	week_mins = (2 * 24 * 60) + (event_hours*60) + event_mins
	        		                my_event  = Event(x,event_hours,event_mins, week_mins, "Wed", event_description)
        	                		self.event_list.append(my_event)

		                	if "thu" in event or "weekday" in event or "everyday" in event:
                		        	week_mins = (3 * 24 * 60) + (event_hours*60) + event_mins
	                        		my_event  = Event(x,event_hours,event_mins, week_mins, "Thu", event_description)
		        	                self.event_list.append(my_event)

		                	if "fri" in event or "weekday" in event or "everyday" in event:
                		        	week_mins = (4 * 24 * 60) + (event_hours*60) + event_mins
	                        		my_event  = Event(x,event_hours,event_mins, week_mins, "Fri", event_description)
		        	                self.event_list.append(my_event)

		        	        if "sat" in event or "weekend" in event or "everyday" in event:
                		        	week_mins = (5 * 24 * 60) + (event_hours*60) + event_mins
			                        my_event  = Event(x,event_hours,event_mins, week_mins, "Sat", event_description)
		        	                self.event_list.append(my_event)

		        	        if "sun" in event or "weekend" in event or "everyday" in event:
                		        	week_mins = (6 * 24 * 60) + (event_hours*60) + event_mins
			                        my_event  = Event(x,event_hours,event_mins, week_mins, "Sun", event_description)
		        	                self.event_list.append(my_event)

	                x = x + 1

	        #No events set
        	if len(self.event_list)==0:
                	return None

	        self.event_list.sort(key = lambda a: a.week_mins)

        	next_event = self.event_list[0]
	        for a in self.event_list:
        	        if a._week_mins >= now_mins:
                	        next_event = a
                        	break

        	return next_event


if __name__ == "__main__":
	db = DB.DB()
	db.load_settings()
        event_list = EventList()
        next_event = event_list.get_next_event(db)
	if next_event == None:
		print ("No events")
	else:
	        print "Next Event: " + next_event.day + " " + next_event.get_time(db.get_value("timestyle")=="24") + " " + next_event.description


