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

dbname = 'dq.db'		# Name of the DQ database, sensibly
semi = threading.Semaphore()		# Start us up, with (we hope) a global semaphore

def open_listener_db():

	# We want to open the database of listened-to stuffs
	# We need to use the semaphore to make sure we really can do that
	#print('Acquiring semaphore...')
	semi.acquire()
	#print('Acquired semaphore')

	try:
		testy = os.stat('db' + os.sep + dbname)
	except OSError:		# No directory, apparently
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
		connector = sqlite3.connect('db' + os.sep + dbname)
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