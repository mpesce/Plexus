#!/usr/bin/python
#
# Copyright (c) 2010, 2011 Mark D. Pesce
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
# This is the main database module for Plexus
# Which handles storage and retrieval of entries in the social graph

import sqlite3		# Requires 2.5
import os
import json			# Requires 2.6
import uuid			# Requires 2.5
import smtplib
from email.mime.text import MIMEText

instance_id = 'e309f818-f870-40ff-ba7a-8ff69a4bbe28'		# This should be provided programatically, but whatevs...

dbfname = 'sharer.db'		# Name of the Plexus sharer map database, sensibly
# Returns True if we are running on Android - use absolute paths
def isAndroid():
	try:
		import android
		return True
	except:
		return False

def getDBName():	
	if isAndroid():
		return "/sdcard/sl4a/scripts/v2/db/" + dbfname
	else:
		return 'db' + os.sep + dbfname

class Sharer:
	# The Sharer instances itself on connection
	def __init__(self):
		connector = self.connect()
		if (connector == None):
			print('This ain\'t gonna work right.')
			# Probably should throw an exception
			raise OSError
		return
		
	def connect(self):
		try:
			testy = os.stat(getDBName())
		except OSError:		# No directory, apparently
			try:
				if isAndroid():
					os.mkdir('/sdcard/sl4a/scripts/v2/db')
					print 'Created Android db directory'
				else:
					os.mkdir('db') # Relative location
					print 'Created db directory'
			except OSError:
				print('Directory db already exists, will not create it')

		# Try to connect to the Sharer.  
		# If we can't, we need to create it.
		# We return a connection object thingy
		try:
			#print('Trying to connect')
			self.connector = sqlite3.connect(getDBName())
			#print('Successful connection')
			# Do we know if we have the correct table in this database?
			# Or any tables at all?
			self.connector.execute('''create table if not exists share_map (type text, service text, host text, port text, dest_id text, pluid text)''')
			return self.connector
		except:
			print('Some sort of exception connecting to share_map')
			self.connector = None
			return self.connector

	def close(self):
		self.connector.commit()		# Commit all the changes to the plexbase
		self.connector.close()

def beam(msgid, type, pluid, timestamp, data, host, port, dest_id):
  print 'We are BEAMING to %s on port %s' % (host, port)

  # Eventually a function will handle this reasonably.
  # For the moment, a constant
  my_name = 'mpesce'

  # Now build the RFC2822/5822 message
  msg = MIMEText(data)
  msg.set_charset('utf-8') 
  msg['From'] = my_name + "." + instance_id + "@plexus.relationalspace.org"  # That should be unique and global across Plexus
  msg['To'] = type + "." + dest_id + "@plexus.relationalspace.org"  # Routing information for message type
  msg['Subject'] = msgid # unique ID for tracking messages

  # To transport by SMTP, we wrap our RFC2822-compliant message in another header. 
  # This allows us to have our way with the sender and receiver fields.  Muahahah.
  print "Sending mail..."
  smtp_msg = MIMEText(msg.as_string())
  smtp_msg.set_charset('utf-8') 
  smtp_msg['Subject'] = "sharer.py"
  
  try:
    s = smtplib.SMTP(host, int(port))  # of course, this could be running anywhere, really
    s.sendmail("mark@markpesce.com", "mpesce@gmail.com", smtp_msg.as_string())
    s.quit()
    print 'Message sent!'
  except:
    print 'We threw an exception trying to send that.  Probably the host is not there or refused.  Sorry.'

def share_map_from_type(type):

  # Let's find the mapping(s) for this type.
  # What do we do if we have multiple mappings?  Probably we use them all.  For now.
  # Returns a tuple of host, port, dest_id
  base = Sharer()
  curs = base.connector.cursor()
  matches = curs.execute('select * from share_map where type=?', (type,))
  resultant = curs.fetchone()
  base.close()
  if (len(resultant) == 0):
    return (None, None, None)
  else:
    return (resultant[2], resultant[3], resultant[4])

# This is the entry point for anything that wants to share something
def share(msgid, type, pluid, timestamp, data):
  #print 'We should be sharing right now...'

  if (type.find('plexus-update') == 0):
    
    print 'We should be sharing an update...'
    # Let's find the mapping(s) for this type.
    # What do we do if we have multiple mappings?  Probably we use them all.  For now.
    (host, port, dest_id) = share_map_from_type(type)
    if (host == None):
      print 'No matching type for UPDATE, which is weird and PROBABLY VERY WRONG, aborting...'
      return
    else:
      for method in resultant:
        beam(msgid, type, pluid, timestamp, data, host, port, dest_id)  # Should send things right along.  Probably.
        return
        
  if (type.find('plexus-message') == 0):
  
    print 'We should be sharing a message...'
    
    # Translate the pluid and type into all matching access methods to send the message
    # If there are no messages, we can't send the message and we make a sad.
    import plex			# No need to do this unless we really need to, we can move it later
    plx = plex.Plex()
    curs = plx.connector.cursor()
    matches = curs.execute('select * from connections where pluid=? and type=?', (pluid, type))
    resultant = curs.fetchall()
    plx.close()
    if (len(resultant) > 0):		# We has some matches, yay!
    
      for connection in resultant:
        method = connection[2]
        credential = json.loads(connection[3])
        print 'method: %s       credential: %s' % (method, credential)
        
        # For the moment, we'll focus on Twitter.  This should be modular, blah blah blah
        if (method.find('twitter') == 0):
          print 'Packing something off to Twitter'
          old_data = json.loads(data)  # Grab the old data
          print old_data
          print credential[0]
          print credential[0][1]
          plexus_data = { "service": "plexus", "plexus-message": old_data['plexus-message'], "destination": [credential[0][1],], "when": old_data['when'] }
          new_plexus_data = json.dumps(plexus_data)
          (host, port, dest_id) = share_map_from_type(type)
          if (host == None):
            print 'No matching type for MESSAGE, which is weird and probably wrong, aborting...'
          else:
            beam(msgid, type, pluid, timestamp, new_plexus_data, host, port, dest_id)
    else:
      print 'No matches in connections database for %s and %s, abandonding message.' % (pluid, type)
      
  return

# Given a pluid and plexus type, returns (service, pointer) if one exists
# This is necessary if there are specific share_map entries for specific social graph entries
def match_service(pluid, type):
	base = Sharer()
	curs = base.connector.cursor()
	matches = curs.execute('select * from share_map where pluid=? and type=?', (pluid, type))
	resultant = curs.fetchone()
	base.close()
	if (resultant != None):
		return((resultant[1],resultant[2]))
	else:
		return None

# Create a new share map, should run this before having a play, fills with data -- used during development ONLY		
def init_share_map():
	base = Sharer()
	curs = base.connector.cursor()
	curs.execute('''insert into share_map values ("plexus-message", "twitter", "192.168.0.57", "4181", "5d686217-fbe8-4d72-9440-db2da08b45a6", "")''')
	curs.execute('''insert into share_map values ("plexus-message", "smtp", "localhost", "4180", "bbb3af78-7e94-4dd1-b15a-c1ee3527a018", "")''')
	curs.execute('''insert into share_map values ("plexus-update", "twitter", "192.168.0.57", "4181", "5d686217-fbe8-4d72-9440-db2da08b45a6", "")''')
	base.close()
	print 'New share_map database created.'

if __name__ == "__main__":
  init_share_map()