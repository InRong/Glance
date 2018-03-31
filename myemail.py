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

