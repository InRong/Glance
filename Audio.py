#!/usr/bin/env python
#
# Module containing some Audio features
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

import pygame
from pygame.locals import *
import utils
import os
import inflect
import math
import numpy
import random

class Audio(object):

	def __init__(self):
		self._stop = False

		#create the beep
	        size = (1366, 720)
        	bits = 16
        	pygame.mixer.pre_init(44100, -bits, 2)
        	pygame.init()


	        duration = 0.05          # in seconds
        	#freqency for the left speaker
        	frequency_l = 2200
        	#frequency for the right speaker
        	frequency_r = 1800

	        #this sounds totally different coming out of a laptop versus coming out of headphones

        	sample_rate = 44100

        	n_samples = int(round(duration*sample_rate))

        	#setup our numpy array to handle 16 bit ints, which is what we set our mixer to expect with "bits" up above
        	buf = numpy.zeros((n_samples, 2), dtype = numpy.int16)
        	max_sample = 2**(bits - 1) - 1

        	for s in range(n_samples):
                	t = float(s)/sample_rate    # time in seconds

                	#grab the x-coordinate of the sine wave at a given time, while constraining the sample to what our m$
                	buf[s][0] = int(round(max_sample*math.sin(2*math.pi*frequency_l*t)))        # left
                	buf[s][1] = int(round(max_sample*0.5*math.sin(2*math.pi*frequency_r*t)))    # right

        	self._sound = pygame.sndarray.make_sound(buf)



	def play_beep(self):
        	self._sound.play(1)

        	x = 0
        	while x < 1000000: #bit rough.....
                	x = x + 1

	def to_string_for_speech(self, myint):
        	p = inflect.engine()
        	return p.number_to_words(myint)

	def speak(self, vol, words):

        	if vol == "soft":
                	os.system ("amixer cset numid=1 -- 80%")
        	elif vol == "med":
                	os.system ("amixer cset numid=1 -- 90%")
        	elif vol == "loud":
                	os.system ("amixer cset numid=1 -- 100%")
        	else:
                	os.system ("amixer cset numid=1 -- 80%")


       		os.system('flite -voice slt -t "' + words + ' " ')


	def play_file(self, path):
		self._stop = False
		pygame.mixer.init()
		pygame.mixer.music.load(path)
		pygame.mixer.music.play()
		while pygame.mixer.music.get_busy() == True:
   			if not self._stop:
				continue

	def stop(self):
                self._stop = True

	def play_multi(self, *args):

		self._stop = False
		pygame.mixer.init()

		for x in args:
			pygame.mixer.music.load(x)
			pygame.mixer.music.play()
			while pygame.mixer.music.get_busy() == True:
   				if not self._stop:
					continue

	def say_good_greeting(self):
		greeting = ""
		
		if utils.get_hours() < 12:
			greeting = "goodmorning"
		elif utils.get_hours() < 18:
			greeting = "goodafternoon"
		else:
			greeting = "goodevening"

		self.play_file('Clock//' + greeting + '.wav')

	def say_time(self, style):
	
		if style == "12":
			if (utils.get_mins()==0):
       		 		self.play_multi('Clock//thetimeis.wav','Clock//' + utils.get_time_h_12() + '.wav','Clock//oclock.wav','Clock//exactly.wav')
			elif (utils.get_mins()<10):
        			self.play_multi('Clock//thetimeis.wav','Clock//' + utils.get_time_h_12() + '.wav','Clock//oh.wav','Clock//' + utils.get_time_m() + '.wav')
			else:
        			self.play_multi('Clock//thetimeis.wav','Clock//' + utils.get_time_h_12() + '.wav','Clock//' + utils.get_time_m() + '.wav')
		else:	
			if (utils.get_mins()==0):
       		 		self.play_multi('Clock//thetimeis.wav','Clock//' + utils.get_time_h() + '.wav','Clock//hundred.wav','Clock//hours.wav')
			elif (utils.get_mins()<10):
        			self.play_multi('Clock//thetimeis.wav','Clock//' + utils.get_time_h() + '.wav','Clock//oh.wav','Clock//' + utils.get_time_m() + '.wav')
			else:
        			self.play_multi('Clock//thetimeis.wav','Clock//' + utils.get_time_h() + '.wav','Clock//' + utils.get_time_m() + '.wav')


	def say_inspiration(self):
		path = "Inspiration//"
		inspiration = random.choice(os.listdir(path)) 
		print (path + inspiration)
		self.play_file(path + inspiration)

	
	def end(self):
		self.stop()
        	pygame.quit()


if __name__ == "__main__":
	audio = Audio()
	audio.say_inspiration()
