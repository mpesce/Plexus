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
# This is NQ, the enqueueing module
# This module receives all of the things to be shared
# And keeps them in its own database
# So that when front end clients ask for them
# Well, here they are!
#
# Always call the send_shared() function
# And the rest of the work happens internally here

import os
import threading
import sqlite3
import sharer			# module that actually dispatches the thingy to be shared

dbfname = 'nq.db'					# Name of the NQ database, sensibly
semi = threading.Semaphore()		# Start us up, with (we hope) a global semaphore

# Returns True if we are running on Android - use absolute paths
def isAndroid():
	try:
		import android
		#print "Android!"
		return True
	except:
		return False

def getDBName():	
	if isAndroid():
		return "/sdcard/sl4a/scripts/db/v2/" + dbfname
	else:
		return 'db' + os.sep + dbfname

def open_listener_db():

	# We want to open the database of listened-to stuffs
	# We need to use the semaphore to make sure we really can do that
	#print('Acquiring semaphore...')
	semi.acquire()
	#print('Acquired semaphore')

	try:
		testy = os.stat(getDBName())
	except OSError:		# No directory, apparently
		if (isAndroid()):
			try:
				os.mkdir('/sdcard/sl4a/scripts/db')
				print 'Created Android db directory'
			except OSError:
				#print 'Directory db already exists, will not create it'
				x = 1 # placeholder
		else:
			try:
				os.mkdir('db')
				print('Created db directory')
			except OSError:
				#print('Directory db already exists, will not create it')
				x = 2 # placeholder

	# Try to connect to the plexbase.  
	# If we can't, we need to create it.
	# We return a connection object thingy
	try:
		#print('Trying to connect')
		connector = sqlite3.connect(getDBName())
		#print('Successful connection')
		# Do we know if we have the correct table in this database?
		# Or any tables at all?
		connector.execute('''create table if not exists shared (msgid text, type text, pluid text, timestamp text, data text)''')
	except:
		print('Some sort of exception connecting to listenbase')
		connector = None
	return connector

def close_listener_db(connector):
	connector.commit()
	connector.close()
	semi.release()
	#print('Semaphore released')

def send_shared(msgid, type, pluid, timestamp, data):
	print("We want to share to something!")
	print msgid, type, timestamp, data
	connector = open_listener_db()
	if (connector != None):
		connector.execute('insert into shared values (?,?,?,?,?)', (msgid, type, pluid, timestamp, data))
		close_listener_db(connector)
	
	# Our work has just barely begun
	# This is where we actually map a message type to a particular sharer.
	# We should be prepared to send it off to the appropriate sharer, once we reckon which sharer that is.
	# Now when this gets all fancy-like, it will handle failure recovery, etc.
	sharer.share(msgid, type, pluid, timestamp, data)

def get_shared(index):
	#print("We are getting index " + str(index))
	#the_index = int(index)
	connector = open_listener_db()
	if (connector != None):
		curs = connector.cursor()
		curs.execute('select * from shared where ROWID=?',(index,))
		result = curs.fetchone()
		# Here we would take the row data and put it into retobj
		retobj = None
		close_listener_db(connector)
		return retobj
	else:
		return None

def size_listened(index):
	#print("We are getting the size")
	the_index = int(index)
	connector = open_listener_db()
	if (connector != None):
		curs = connector.cursor()
		curs.execute('select * from shared where ROWID=?',(the_index,))
		result = curs.fetchone()
		# Need a size calcualtion right here
		close_listener_db(connector)
		return retsize
	else:
		return 0
		
def count_listened():
	#print("count_listened")
	connector = open_listener_db()
	if (connector != None):
		curs = connector.cursor()
		curs.execute('select ROWID from shared')		# Cheap and fast
		count = len(curs.fetchall())
		close_listener_db(connector)
		return count