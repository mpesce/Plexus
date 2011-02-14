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


dbfname = 'plex.db'		# Name of the Plexus social graph database, sensibly
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

class Plex:
	# The Plex instances itself on connection
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

		# Try to connect to the Plex.  
		# If we can't, we need to create it.
		# We return a connection object thingy
		try:
			#print('Trying to connect')
			self.connector = sqlite3.connect(getDBName())
			#print('Successful connection')
			# Do we know if we have the correct table in this database?
			# Or any tables at all?
			self.connector.execute('''create table if not exists graph (firstname text, lastname text, uid text, pluid text primary key)''')
			self.connector.execute('''create table if not exists connections (pluid text, type text, service text, info text)''')
			return self.connector
		except:
			print('Some sort of exception connecting to plex')
			self.connector = None
			return self.connector
		
	def is_in_plex(self, firstname='', lastname='', uid=''):
		# We do two checks
		# First, is the public UID in the Plexbase
		# If it is, then it's already in here
		# If not, then check the first name, last name
		# If that's not in there either, return False
		if (uid != ''):
			curs = self.connector.cursor()
			matches = curs.execute('select * from graph where uid=?', (uid,))
			# Theoretically this will return some sort of interesting iterator
			if (len(curs.fetchall()) > 0):
				return True
		
		# OK, check the first and last name for uniqueness
		if ((firstname != '') and (lastname != '')):
			curs = self.connector.cursor()
			matches = curs.execute('select * from graph where firstname=? and lastname=?', (firstname, lastname))
			# Theoretically this will return some sort of interesting iterator
			if (len(curs.fetchall()) > 0):
				return True		
		
		print('is_in_plex no matches found')
		return False

	def name_to_pluid(self, cursor, firstname='', lastname=''):
		if len(firstname) > 1:
			matches = cursor.execute('select * from graph where firstname=? and lastname=?', (firstname, lastname))
		else:
		  print 'lastname %s' % lastname  
		  matches = cursor.execute('select * from graph where lastname=?', (lastname,))
		resultant = cursor.fetchone()
		if (resultant != None):
			return resultant[3]			# This should be the pluid
		else:
			return None
	
	def add_from_jcard(self, jcards):
		# We've got a JSON-like object which is our jCard
		# Ideally it's been somewhat validated
		# Now we need to add it to the plexbase
		for jcard in jcards['vcard']:
			name = jcard['fn']
			plexus_type = jcard['plexus-type']
			# break the name into firstname and lastname components
			fullname = name.split()
			# is there a uid?
			try:
				publicUid = jcard['uid']
				#print ('\"' + publicUid + '\"')
			except KeyError:
				publicUid = ""
			
			# If there is already an entry that matches
			# We do not create a new one.
			insert = True
			if len(fullname) > 1:
				if self.is_in_plex(fullname[0], fullname[1], publicUid) == True:
					# Eventually we should use this point to update information in the Plexbase
					print('Matches something in Plex, not inserting')
					insert = False
			elif self.is_in_plex(lastname=fullname[0], uid=publicUid) == True:  # Only one name
				print 'Matches something in Plex, not inserting'
				insert = False

			curs = self.connector.cursor()
			try:
				# Add the entry to the Plex, creating a plex uuid for it along the way...
				if (insert == True):
					pluid = str(uuid.uuid4())  # Create Plexus UID
					#curs = self.connector.cursor()
					if len(fullname) > 1:
						curs.execute('insert into graph values (?, ?, ?, ?)', (fullname[0], fullname[1], publicUid, pluid))				#self.connector.execute("insert into graph values (\'" + fullname[0] + "\', \'" + fullname[1] + "\', \'" + publicUid + "\', \' \')")
					else:
						curs.execute('insert into graph values (?, ?, ?, ?)', ("", fullname[0], publicUid, pluid))

				# Grab the correct pluid for this entry in the graph, if we haven't generated one
				if (insert == False):
					if len(fullname) > 1:
						pluid = self.name_to_pluid(curs, fullname[0], fullname[1])
						print 'inserting existing match into connections'
					else:
						pluid = self.name_to_pluid(cursor=curs, lastname=fullname[0])
						print 'inserting existing match into connections'
						
				# Iterate through the connections, adding them to the connections table		
				conlist = jcard['connections']
				for connection in conlist:
					print connection
					curs.execute('insert into connections values (?, ?, ?, ?)', (pluid, plexus_type, connection.items()[0][0], json.dumps(connection.items())))
				print('New entry added to Plexbase.')
			except KeyboardInterrupt:
				print('Something did not work with that')

	def get_listeners(self):
		curs = self.connector.cursor()
		matches = curs.execute('select * from connections order by service asc')
		return matches

	def close(self):
		self.connector.commit()		# Commit all the changes to the plexbase
		self.connector.close()

# Given a pluid, returns (firstname, lastname)
def pluid_to_name(id):
	base = Plex()
	curs = base.connector.cursor()
	matches = curs.execute('select * from graph where pluid=?', (id,))
	resultant = curs.fetchone()
	base.close()
	if (resultant != None):
		return((resultant[0],resultant[1]))
	else:
		return None


# Sample jCard for testing
tcs = '''{ "vcard" : [ { 
			"fn": "Mark Pesce", 
			"uid": "6fa459ea-ee8a-3ca4-894e-db77e160355e", 
			"nickname": "mpesce",
			"photo": "http://upload.wikimedia.org/wikipedia/en/3/3d/Mark-cafelife.jpg",
			"connections": [
				{ "twitter": "mpesce", "id": "Twitter" },
				{ "feed": "http://blog.futurestreetconsulting.com/?feed=rss2", "id": "The Human Network" },
				{ "flickr": "hyperpeople", "id": "Flickr" },
				{ "delicious": "mpesce", "id": "del.icio.us" } ],
			"rev": "2010-07-11T11:39:00" } ] }'''

if __name__ == "__main__":
	# let's see if we can stuff a card into the Plexbase...
	testcard = json.loads(tcs)
	#print(testcard)
	
	whee = Plex()
	whee.add_from_jcard(testcard)
	whee.close()