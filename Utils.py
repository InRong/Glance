#!/usr/bin/env python
#
# Utils.py file for providing helper functions
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
import datetime
import os
import time
import urllib2
import socket
import fcntl
import struct
import smtplib

# Import the email modules
from email.mime.text import MIMEText

MON = 0
TUE = 1
WED = 2
THU = 3
FRI = 4
SAT = 5
SUN = 6

def get_hours():
        return int(time.strftime("%H"))

def get_mins():
        return int(time.strftime("%M"))

def get_days():
        return int(time.strftime("%d"))

def get_months():
        return int(time.strftime("%m"))

def get_secs():
        return time.strftime("%S")

def is_odd_seconds():
        secs = int(time.strftime("%S"))
        remainder = secs % 2
        if (remainder == 1):
                return True
        else:
                return False


def to_string_with_leading_zero(x):
        if(x<10):
                return '0' + str(x)
        else:
                return str(x)

def get_time():
        return to_string_with_leading_zero(get_hours())+ ":" + to_string_with_leading_zero(get_mins())

def get_time_2():
        if (is_odd_seconds()==1):
                divider=":"
        else:
                divider=" "

        return to_string_with_leading_zero(get_hours())+ divider + to_string_with_leading_zero(get_mins())

def get_time_3():
        if (is_odd_seconds()==1):
                divider="."
        else:
                divider=" "

        return to_string_with_leading_zero(get_hours())+ ":" + to_string_with_leading_zero(get_mins()) + divider

def get_time_hhmm():
        return time.strftime("%H%M")

def get_time_h_12():
        return str(int(time.strftime("%I")))

def get_time_12():
        return str(int(time.strftime("%I"))) + to_string_with_leading_zero(get_mins())

def get_time_h():
        return str(get_hours())

def get_time_m():
        return str(get_mins())

def get_date_mmdd():
        return time.strftime("%m%d")

def get_date_ddmm():
        return time.strftime("%d%m")


def get_current_time():
        return to_string_with_leading_zero(get_hours())+ to_string_with_leading_zero(get_mins())

def get_current_date():
        return to_string_with_leading_zero(get_months())+ to_string_with_leading_zero(get_days())





def get_ip_address(ifname):
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915, #SIOCGIFADDR
                struct.pack('256s', ifname[:15])
        )[20:24])

def get_ip():
        try:
                return get_ip_address('eth0')
        except IOError:
 		return get_ip_address('wlan0')

def dp_helper(temp):

	i = temp.find('.')

	s = temp.replace(".","")

	return {'pos':i,'tempstr':s}	

def get_tens_of(what):
        return what / 10

def get_units_of(what):
        return what % 10

def centigrade_to_fahrenheit(temp):
        return round((float(temp) * 1.8) + 32,1)

def restart():
        os.system("shutdown -r now")

def is_weekend():
        d = datetime.datetime.now();
        return (d.weekday() ==  5 or d.weekday() == 6)

def is_saturday():
        d = datetime.datetime.now();
        return (d.weekday() ==  5)

def is_friday():
        d = datetime.datetime.now();
        return (d.weekday() ==  4)

def day_number():
        d = datetime.datetime.now();
        return d.weekday()

def is_tomorrow_weekend():
        d = datetime.datetime.now();
        return (d.weekday() ==  4 or d.weekday() == 5)


def convert_hours_to_12_hours(in_hours):
	if in_hours>12:
		return in_hours - 12

	if inhours==0:
		return  12
		
	return inhours

def convert_time_to_12hrs(in_time):
	hours =  int(in_time[:2])
	mins = in_time[-2:]
	if hours > 12: 
		hours = hours - 12

	return str(hours) + mins

def convert_mins_to_hours_mins(in_mins):
	hours = str(in_mins / 60)
	mins = str(in_mins % 60)
	return hours + "h " + mins + "m "

def abbreviated_day():
	weekdays = 'MON TUE WED THU FRI SAT SUN'.split()
        d = datetime.datetime.now();
	return weekdays[d.weekday()]

def full_day():
	weekdays = 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()
        d = datetime.datetime.now();
	return weekdays[d.weekday()]

def short_day():
	weekdays = 'Mon Tue Wed Thu Fri Sat Sun'.split()
        d = datetime.datetime.now();
	return weekdays[d.weekday()]


def full_month():
	months = 'January February March April May June July August September October November December'.split()
        d = datetime.datetime.now();
	return months[d.month-1]


def check_internet():
	try:
        	urllib2.urlopen("http://www.google.com").close()
	except urllib2.URLError:
        	return False
	else:
        	return True


def send_email(fromemail,toemail,subject, body, passwd):
        password = passwd

        msg = MIMEText(body)

        msg['Subject'] = subject
        msg['From'] = fromemail
        msg['To'] = toemail

        s = smtplib.SMTP('smtp.gmail.com',587)
        s.starttls()
        s.login(fromemail,password)
        s.sendmail(fromemail, toemail, msg.as_string())
        s.quit()

#print dphelper("27c")

if __name__ == "__main__":
#	intime = "1747"
#	print converttimeto12hrs(intime)

#	print abbreviatedday()

	print (get_hours())

	if check_internet():
		print "connected"
	else:
		print "not connected"
