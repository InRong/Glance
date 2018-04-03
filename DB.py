#!/usr/bin/env python
#
# Database Helper class 
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

import sqlite3

SETTING = 0
VALUE = 1
MESSAGE = 2

class DB (object):

	def __init__(self):
		self._file_path = '//var//www//html//GlanceWeb//clp.db'
		self._field_dict = {}
		self._message_dict = {}

	def db_load(self):
		self._field_dict.clear()
		self.load_settings()		

	def get_file_path(self):
		return self._file_path

	def load_settings(self):
		self._conn = sqlite3.connect(self._file_path)
		curs=self._conn.cursor()
		self._field_dict.clear()

		for row in curs.execute("SELECT setting,value FROM settings"):
			if not self._field_dict.has_key(row[SETTING]):
                		self._field_dict[row[SETTING]]= row[VALUE].strip()

		self._message_dict.clear()

		for row in curs.execute("select s.setting, s.value, (m.host || '/' || m.name || '/' || m.value) as message from settings s, messages m where s.value = m.id"):
			if not self._message_dict.has_key(row[SETTING]):
                		self._message_dict[row[SETTING]]= row[MESSAGE].strip()

	def get_value(self, setting):
		if self._field_dict.has_key(setting):
                	return self._field_dict[setting]

	def get_int_value(self, setting):
		if self._field_dict.has_key(setting):
                	return int(self._field_dict[setting])

	def get_message(self, setting):
		if self._message_dict.has_key(setting):
                	return self._message_dict[setting]

	def save_setting(self, setting, newvalue):
		result = False

		print "saving setting - " + setting + " " + newvalue
		self._conn = sqlite3.connect(self._file_path)

		curs=self._conn.cursor()
		curs.execute("UPDATE settings SET value = '" + newvalue + "' WHERE setting = '" + setting + "'")
		self._conn.commit()
		if curs.rowcount==1:
			self._field_dict[setting] = newvalue
			result = True	

		return result

if __name__ == "__main__":
	db = DB()
	db.load_settings()
	print db.get_message('display12')
