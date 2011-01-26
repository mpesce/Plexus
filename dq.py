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
# This is DQ, the de-queueing module
# This module receives all of the things the listeners listen to
# And keeps them in its own database
# So that when front end clients ask for them
# Well, here they are!
#
# All the listeners call the send_listened() function
# And the rest of the work happens internally here

import os
import threading
import sqlite3

dbfname = 'dq.db'		# Name of the DQ database, sensibly
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
				print 'Directory db already exists, will not create it'
		else:
			try:
				os.mkdir('db')
				print('Created db directory')
			except OSError:
				print('Directory db already exists, will not create it')

	# Try to connect to the plexbase.  
	# If we can't, we need to create it.
	# We return a connection object thingy
	try:
		#print('Trying to connect')
		connector = sqlite3.connect(getDBName())
		#print('Successful connection')
		# Do we know if we have the correct table in this database?
		# Or any tables at all?
		connector.execute('''create table if not exists dequeue (msgid text, type text, timestamp text, data text)''')
	except:
		print('Some sort of exception connecting to listenbase')
		connector = None
	return connector

def close_listener_db(connector):
	connector.commit()
	connector.close()
	semi.release()
	#print('Semaphore released')

def send_listened(msgid, type, timestamp, data):
	print("We've listened to something!")
	print msgid, type, timestamp, data
	connector = open_listener_db()
	if (connector != None):
		connector.execute('insert into dequeue values (?,?,?,?)', (msgid, type, timestamp, data))
		close_listener_db(connector)

def get_listened(index):
	#print("We are getting index " + str(index))
	#the_index = int(index)
	connector = open_listener_db()
	if (connector != None):
		curs = connector.cursor()
		curs.execute('select * from heard where ROWID=?',(index,))
		result = curs.fetchone()
		retobj = plobject.Plobject(result[0], result[1], result[2], result[3], result[4], result[5])
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
		curs.execute('select * from heard where ROWID=?',(the_index,))
		result = curs.fetchone()
		retsize = len(result[0]) + len(result[1]) + 20 + len(result[3]) + len(result[4]) + len(result[5])
		close_listener_db(connector)
		return retsize
	else:
		return 0
		
def count_listened():
	#print("count_listened")
	connector = open_listener_db()
	if (connector != None):
		curs = connector.cursor()
		curs.execute('select ROWID from heard')		# Cheap and fast
		count = len(curs.fetchall())
		#print("count_listened is " + str(count))
		close_listener_db(connector)
		return count