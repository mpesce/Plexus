#!/usr/bin/python
#
# Copyright (c) 2011 Mark D. Pesce
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
import os, sys, time, uuid, smtplib, json
import yaml
#import rsa
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from optparse import OptionParser		# Will eventually move to argparse, but requires 2.7

instance_id = None  # uuid.uuid4() - eventually this should auto-generate per instance
dest_id = "e2eb0d8b-b82c-5c2f-b6f1-dee1038fd9ae" # uuid.uuid5(uuid.NAMESPACE_DNS, 'mpesce.plexus.relationalspace.org')
my_name = u"mpesce"
dest_ip = None

def writeFile(content, file):
    fp = open(file, "wb")
    fp.writelines(yaml.dump(content))
    fp.close()

# The instance ID is a UUID specific to this instance, uniquely identifies this listener
def getInstance():
	#print "getInstance()"
	if (os.path.isfile(".plxcli-instance")):
		fp = open(".twitter_listener", "r")
		a = yaml.load(fp)
		fp.close()
		return a
	else:
		return -1

#Create an instance ID if one does not yet exist
def genInstance():
	print "Generating instance UUID..."
	instance_id = str(uuid.uuid4())
	writeFile(instance_id, ".plxcli-instance")
	print "Done!"

def set_dest(addr):
	global dest_ip
	dest_ip = addr
	return

def mail_msg_plexus(txt):

	# To transport by SMTP, we wrap our RFC2822-compliant message in another header. 
	# This allows us to have our way with the sender and receiver fields.  Muahahah.
	print "Sending mail..."
	import smtplib
	msg = MIMEText(txt)
	msg.set_charset('utf-8') 
	msg['Subject'] = "plxcli.py"
	
	# Check to see if dest_ip is valid, if not, um, use localhost?
	global dest_ip
	if (dest_ip == None):
		dest_ip = "localhost"
	
	s = smtplib.SMTP(dest_ip, 4180)  # of course, this could be running anywhere, really
	s.sendmail("mark@markpesce.com", "mpesce@gmail.com", msg.as_string())
	s.quit()
	
def send_update(data):
	#print "The data is: ", data

	name_list = [ my_name, ]
	plexus_data = { "service": "plxcli", "plexus-update": data.encode('utf-8'), "source": name_list, "when": str(int(time.time())) }
	msg = MIMEText(json.dumps(plexus_data))
	msg.set_charset('utf-8') 
		
	# Create the 'From' field by signing the UUID of the module with the private key
	#signature = rsa.sign(listener_uuid, keys['priv'])
	#print signature
	# Get the user to put into 'From' field
	msg['From'] = my_name + "." + instance_id + "@plexus.relationalspace.org"  # That should be unique and global across Plexus
	msg['To'] = "plexus-update." + dest_id + "@plexus.relationalspace.org"  # Routing information for message type
	msg['Subject'] = str(uuid.uuid4())  # unique ID for tracking messages
	
	print msg.as_string()
	#mail_msg(msg.as_string())
	mail_msg_plexus(msg.as_string())

	return

def send_message(msg, to):
	print msg
	print to

	name_list = [ to.encode('utf-8'), ]
	plexus_data = { "service": "plxcli", "plexus-message": msg.encode('utf-8'), "destination": name_list, "when": str(int(time.time())) }
	msg = MIMEText(json.dumps(plexus_data))
	msg.set_charset('utf-8') 
	msg['From'] = my_name + "." + instance_id + "@plexus.relationalspace.org"  # That should be unique and global across Plexus
	msg['To'] = "plexus-message." + dest_id + "@plexus.relationalspace.org"  # Routing information for message type
	msg['Subject'] = str(uuid.uuid4())  # unique ID for tracking messages
	
	print msg.as_string()
	#mail_msg(msg.as_string())
	mail_msg_plexus(msg.as_string())

	return

if __name__ == "__main__":

	# Get the Instance ID
	instance_id = getInstance()
	if instance_id == -1:
		print "We don't have an instance ID yet, must create it"
		genInstance()
		instance_id = getInstance()

	#print "Plexus Command Line Tool v0.1"
	parser = OptionParser(usage="%prog [-d] [-u] [-m -r]", version="%prog - 0.1")
	parser.add_option("-d", "--destination", action="store", type="string", dest="dest_addr", help="IP address/name for destination Plexus process")
	parser.add_option("-u", "--update", action="store", type="string", dest="update_data", help="sends UPDATE_DATA as update")
	parser.add_option("-m", "--message", action="store", type="string", dest="message_data", help="sends MESSAGE_DATA as message to RECIPIENT")
	parser.add_option("-r", "--recipient", action="store", type="string", dest="recipient_name", help="RECIPIENT for MESSAGE")
	(option, args) = parser.parse_args()
	if option.dest_addr:
		set_dest(option.dest_addr)
	if option.update_data:
		send_update(option.update_data)
	elif option.message_data:
		if option.recipient_name:
			send_message(option.message_data, option.recipient_name)
		else:
			parser.error("You must specify a recipient for a message.")
	else:
		parser.print_help()


