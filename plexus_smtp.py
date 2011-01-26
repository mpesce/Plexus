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
import twitter
import os, sys, time, uuid
#import yaml
#from yaml import Loader, Dumper
import json
import smtpd, asyncore
#import rsa
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.parser import Parser, HeaderParser
import email
import socket
import dq
import plxaddr

mypod_ip = "74.207.224.149"
kuanyin_ip ="192.168.0.37"
android_ip = "192.168.0.148"
set_ip = "localhost"

# Returns True if we are running on Android - use absolute paths
def isAndroid():
	try:
		import android
		#print "Android!"
		return True
	except:
		return False

class PlexusSMTPServer(smtpd.SMTPServer):

	def process_message(self, peer, mailfrom, rcpttos, data):
		print "===SMTP==="
		print "Receiving message from: ", peer
		print "Message addressed to: ", mailfrom
		print "Message addressed to: ", rcpttos
		print "Message length: ", len(data)
		#print "---------"
		#print data
		#print '---------'
		#print
		#print "About to parse..."
		parse_plexus_2822_data(data)

# The Plexus message is a message-within-a-message
# That is to say, there is another RFC2822 message inside the message
# This makes the inner message transport independent.  Theoretically.
# Here, we peel off the outer envelope and reveal the inner message
def parse_plexus_2822_data(data):
	#print "PlexusSMTPServer::parse_plexus_2822_data"
	msg = Parser().parsestr(data)
	#msg = email.message_from_string(data)
	#ymsg = yaml.dump(msg)
	#print ymsg
	inner_data = msg.get_payload()
	print inner_data
	inner_msg = Parser().parsestr(inner_data)
	#ymsg = yaml.dump(inner_msg)
	#print ymsg
	process_message(inner_msg)


# Format for From: is username@instanceID.plexus.relationalspace.org
# Where username is the account name / handle of the user account
# And the instanceID is the uuid for the process sending the message
def unpack_sender(adr):
	parts = adr.split("@")
	moreparts = parts[1].split(".")
	return { "type": parts[0], "destid": moreparts[0] }


# Format for To: is type@destID.plexus.relationalspace.org
# Where type is the type of message (update, command, post, etc...)
# And the destID is the ID of the destination Plexus process.  Which should be us.  Hopefully.
def unpack_to(to):
	parts = to.split("@")
	moreparts = parts[1].split(".")
	return { "user": parts[0], "listenerid": moreparts[0] }


# Get your own IP address.  This is the IPV4 address, so when we go to IPV6, that'll need fixing...
# Also, if this is a multi-homed machine, this could return, erm, "indeterminate" (read: wrong) results.
def get_my_ipv4():
	return socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)[0][4][0]


# All of the built-in types are validated here.  
# There's only a few of them at the moment
# def validate_type(the_type):
# 	if (the_type.find(u'plexus-update') == 0):
# 		return True
# 	if (the_type.find(u'plexus-message') == 0):
# 		return True
# 	if (the_type.find(u'pleuxs-post') == 0):
# 		return True
# 	if (the_type.find(u'plexus-command') == 0):
# 		return True
# 	else:
# 		return False

# The payload should be a JSON object
# One would hope, anyway.  If it parses, then good.
# If not, then ick.
def validate_payload(the_payload):
	try:
		result = json.loads(the_payload)
	except TypeError:
		return False
	return True

# Eventually this function will be moving to another, more central module
# All incoming messages from whatever transport make their way to this function
# They're read in, parsed, and checked for validity
# If they're valid, they should end up on the DQ
def process_message(msg):
	print "process_message"	

	ph = plxaddr.parse_headers(msg)		# This should render lots of useful information.  No, seriously.
	#print ph
	if (ph == None):
		print "Garbled headers, rejecting"
		return

# 	msgid = msg['Subject']		# Should have a UUID therein - some way to validate this?
# 	
# 	mfrom = msg['From']		# Get the addressee information
# 	f = unpack_sender(mfrom)
# 	print f
# 
# 	mto = msg['To']
# 	to = unpack_to(mto)
# 	print to

# 	if validate_type(f['type']):
# 		print "Type valid"
# 	else:
# 		print "Type invalid"
# 		return

# 	if validate_type(ph['plexus-identifier']):
# 		print "Plexus Identifier valid"
# 	else:
# 		print "Plexus Identifier invalid"
# 		return

	contents = msg.get_payload()
	if validate_payload(contents):
		print "Contents valid"
	else:
		print "Contents invalid"
		return
	content_object = json.loads(contents)	# Now we have a lovely object with stuff in it

	# Is there anything more fun than a state machine?  I thought not.
#	state = f['type']
	if (ph['listened']):
		print "We are listening, so we DQ this"
		state = ph['plexus-identifier']
		if (state.find(u'plexus-update') == 0):			# Twitter updates, etc.
			print "UPDATE"
			print "Sending it to the DQ"
			dq.send_listened(ph['tracking_id'], state, content_object['when'], contents)	# Pop it onto the DQ
		elif (state.find(u'plexus-message') == 0):			# Twitter DMs, emails, FB messages, etc.
			print "MESSAGE"
			dq.send_listened(ph['tracking_id'], state, content_object['when'], contents)	# Pop it onto the DQ
		elif (state.find(u'plexus-post') == 0):			# RSS, for example
			print "POST"
		elif (state.find(u'plexus-command') == 0):			# Plexus commands <- very important
			print "COMMAND"
	else:
		print "We are sharing, so we NQ this"

if __name__ == "__main__":

	# We'll use the Facade UI to ask the user for the server IP addreess, if Android.
	if isAndroid():
		import android
		droid = android.Android()
		an_ip = droid.dialogGetInput('IP', 'Server IP address?', '127.0.0.1').result
		if (an_ip != None):		# Cancel pressed?
			if (len(an_ip) > 7):	# Malformed IP address?  (should be validated)
				set_ip = an_ip
	else:
		if (len(sys.argv) > 1):
			set_ip = sys.argv[1]
		else:
			set_ip = get_my_ipv4()
	
	print "Starting Plexus SMTP interface on", set_ip,  "port 4180"
	server = PlexusSMTPServer((set_ip, 4180), None)
	asyncore.loop()