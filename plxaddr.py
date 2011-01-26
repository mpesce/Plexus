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
# Module for parsing of RFC2822 addresses for Plexus

# Here's how things look as of 24 January 2011

# Sender 
# username.instance_id@plexus.relationalspace.org
# where the username is some unique username connected to the process sending the message
# Where the instance_id is a uuid.uuid4()-generated UUID, specific to the process instance sending the message
# Everything after the @ is ignored at the moment.  It may eventually mean something.

# Addressee
# plexus-identifier.dest_id@plexus.relationalspace.org
# where the plexus-idenifier is one of a specific set of possibilities:
#	plexus-update - update (Twitter update, Facebook status update, etc)
#	plexus-message - message content (email, Twitter DM, Facebook message, etc)
#	plexus-post - HTML content (RSS, ATOM, etc.)
#	plexus-command - in-band signalling between Plexus processes
#   There will undoubtedly be more of these, and this format will probably change
# Where the dest_id is a is a uuid.uuid4()-generated UUID, specific to the process instance receiving the message
# Everything after the @ is ignored at the moment.  It may eventually mean something.

import email

# All of the built-in types are validated here.  
# There's only a few of them at the moment
def validate_type(the_type):
	if (the_type.find(u'plexus-update') == 0):
		return True
	if (the_type.find(u'plexus-message') == 0):
		return True
	if (the_type.find(u'pleuxs-post') == 0):
		return True
	if (the_type.find(u'plexus-command') == 0):
		return True
	else:
		return False

# We get the RFC2822 message, we hand back a dictionary with all the relevant info in it.
# Including whether this is incoming or outgoingn (listener or shared)
def parse_headers(msg):

	# First, let's figure out which way this thing is pointing.
	# Either direction, the To and From headers have thingy.id
	# So let's extract those first
	senders = msg['From'].split('@')
	sender = senders[0].split('.')
	#print "sender: ", sender
	receivers = msg['To'].split('@')
	receiver = receivers[0].split('.')
	#print "receiver: ", receiver
	
	# So is this listened or shared?
	# If it's listened, then From will have the plexus-identifier
	# If it's shared, then To will have the plexus-identifier
	if (sender[0].find('plexus-') == 0):
		listened = True
		if (validate_type(sender[0]) == False):
			return None						# Invalid plexus-identifier, we bail
	elif (receiver[0].find('plexus-') == 0):
		listened = False
		if (validate_type(receiver[0]) == False):
			return None						# Invalid plexus-identifier, we bail so hard
	else:
		return None			# Failed, we ain't returning nothing, baby
	
	if listened:
		retval = { "listened": True, "user": receiver[0], "plexus-identifier": sender[0], "instance_id": sender[0], "dest_id": receiver[1], "tracking_id": msg['Subject']}
	else:
		retval = { "listened": False, "user": sender[0], "plexus-identifier": receiver[0], "instance_id": sender[0], "dest_id": receiver[1], "tracking_id": msg['Subject']}
		
	return retval


