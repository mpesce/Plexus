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
# This moudule prints out the database as a series of vcards
# A debugging utility, but has practical uses for export
#
import sys, os
import plex
import json

def makevcard(first, last, uid, connections):
  #print connections
  con_list = []
  for con in connections:
    mbr = { "type": con[0], "service": con[1], con[2][0][0]: con[2][0][1] }
    con_list.append(mbr)
  conpart = { "connections": con_list }
  if (len(first) > 0):
    fn = "%s %s" % (first, last)
  else:
    fn = last
  if (len(uid) > 0):
    inside = { "fn": fn, "uid": uid, "connections": con_list }
  else:
    inside = { "fn": fn, "connections": con_list }
  outside = { "vcard" : [ inside, ] }
  #print outside
  return json.dumps(outside)


# Just call this function to return the whole plex as a series of JSON-style vcards
def plex2vcards():

  plx = plex.Plex()		# Open the Plex, would be bad if we can't.
  
  # Now, um, go and get the entire Plex.  More or less.
  curs = plx.connector.cursor()
  matches = curs.execute('select * from graph order by lastname')  # This seems to work, will it assplode memory?
  
  # OK, now iterate through the list
  social_graph = curs.fetchall()
  #print 'The social graph has %d entries.' % (len(social_graph))
  retval = ""
  for friend in social_graph:
    friend_firstname = friend[0]
    friend_lastname = friend[1]
    friend_uid = friend[2]
    friend_pluid = friend[3]
    #print friend_pluid		# Should be the pluid
    
    funstr = 'select * from connections where pluid=\"%s\"' % friend_pluid
    match2 = curs.execute(funstr)
    cons = []
    friend_connections = curs.fetchall()
    for each_connection in friend_connections:
    	#print '     %s  %s %s' % (each_connection[1], each_connection[2], each_connection[3])
    	cons.append([each_connection[1], each_connection[2], json.loads(each_connection[3])])
    vcard = makevcard(friend_firstname, friend_lastname, friend_uid, cons)
    #print vcard
    if (len(retval) == 0):
      retval = vcard
    else:
      retval = retval + "\n" + vcard
  plx.close()
  return retval


if __name__ == "__main__":
  vcards = plex2vcards()
  print vcards