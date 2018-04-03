#!/usr/bin/env python
#
# Helper module providing email support
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
# Import smtplib for the actual email sending function
import smtplib

# Import the email modules 
from email.mime.text import MIMEText

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

