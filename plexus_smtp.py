#!/usr/bin/python
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

mypod_ip = "74.207.224.149"
kuanyin_ip ="192.168.0.37"
android_ip = "192.168.0.148"

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
		self.parse_plexus_2822_data(data)

	# The Plexus message is a message-within-a-message
	# That is to say, there is another RFC2822 message inside the message
	# This makes the inner message transport independent.  Theoretically.
	# Here, we peel off the outer envelope and reveal the inner message
	def parse_plexus_2822_data(self, data):
		print "PlexusSMTPServer::parse_plexus_2822_data"
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
def validate_type(the_type):
	if (the_type.find(u'update') == 0):
		return True
	if (the_type.find(u'message') == 0):
		return True
	if (the_type.find(u'post') == 0):
		return True
	if (the_type.find(u'command') == 0):
		return True
	else:
		return False

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

	msgid = msg['Subject']		# Should have a UUID therein - some way to validate this?
	
	mfrom = msg['From']		# Get the addressee information
	f = unpack_sender(mfrom)
	print f

	mto = msg['To']
	to = unpack_to(mto)
	print to

	if validate_type(f['type']):
		print "Type valid"
	else:
		print "Type invalid"
		return

	contents = msg.get_payload()
	if validate_payload(contents):
		print "Contents valid"
	else:
		print "Contents invalid"
		return
	content_object = json.loads(contents)	# Now we have a lovely object with stuff in it

	# Is there anything more fun than a state machine?  I thought not.
	state = f['type']
	if (state.find(u'update') == 0):			# Twitter updates, etc.
		print "UPDATE"
		print "Sending it to the DQ"
		dq.send_listened(msgid, f['type'], content_object['when'], contents)	# Pop it onto the DQ
	elif (state.find(u'message') == 0):			# Twitter DMs, emails, FB messages, etc.
		print "MESSAGE"
		dq.send_listened(msgid, f['type'], content_object['when'], contents)	# Pop it onto the DQ
	elif (state.find(u'post') == 0):			# RSS, for example
		print "POST"
	elif (state.find(u'command') == 0):			# Plexus commands <- very important
		print "COMMAND"

if __name__ == "__main__":
	print "Starting Plexus SMTP interface on", get_my_ipv4(),  "port 4180"
	server = PlexusSMTPServer((get_my_ipv4(), 4180), None)
	asyncore.loop()