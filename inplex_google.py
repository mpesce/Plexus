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
# Stolen^H^H^H^H^H^HBorrowed very freely from the Google sample code for GData for Python
#
import sys
import getopt
import getpass
import atom
import gdata.contacts
import gdata.contacts.service
import plex

class GoogleContacts(object):
  """GoogleCotacts object demonstrates imports Google Contacts into the Plex."""

  def __init__(self, email, password):
    """Constructor for the GoogleContacts object.
    
    Takes an email and password corresponding to a gmail account to
    demonstrate the functionality of the Contacts feed.
    
    Args:
      email: [string] The e-mail address of the account to use for the sample.
      password: [string] The password corresponding to the account specified by
          the email parameter.
    
    Yields:
      A GoogleContacts object used to run the sample demonstrating the
      functionality of the Contacts feed.
    """
    self.gd_client = gdata.contacts.service.ContactsService()
    self.gd_client.email = email
    self.gd_client.password = password
    self.gd_client.source = 'Plexus-InputContacts'
    self.gd_client.ProgrammaticLogin()

  def PrintPaginatedFeed(self, feed, print_method):
    """ Print all pages of a paginated feed.
    
    This will iterate through a paginated feed, requesting each page and
    printing the entries contained therein.
    
    Args:
      feed: A gdata.contacts.ContactsFeed instance.
      print_method: The method which will be used to print each page of the
          feed. Must accept these two named arguments:
              feed: A gdata.contacts.ContactsFeed instance.
              ctr: [int] The number of entries in this feed previously
                  printed. This allows continuous entry numbers when paging
                  through a feed.
    """
    ctr = 0
    while feed:
      # Print contents of current feed
      ctr = print_method(feed=feed, ctr=ctr)
      # Prepare for next feed iteration
      next = feed.GetNextLink()
      feed = None
      if next:
        #if self.PromptOperationShouldContinue():
        if False:
          # Another feed is available, and the user has given us permission
          # to fetch it
          feed = self.gd_client.GetContactsFeed(next.href)
        else:
          # User has asked us to terminate
          feed = None

  def PrintFeed(self, feed, ctr=0):
    """Prints out the contents of a feed to the console.
   
    Args:
      feed: A gdata.contacts.ContactsFeed instance.
      ctr: [int] The number of entries in this feed previously printed. This
          allows continuous entry numbers when paging through a feed.
    
    Returns:
      The number of entries printed, including those previously printed as
      specified in ctr. This is for passing as an argument to ctr on
      successive calls to this method.
    
    """
    if not feed.entry:
      print '\nNo entries in feed.\n'
      return 0
    for i, entry in enumerate(feed.entry):
      print entry
      print '\n%s %s' % (ctr+i+1, entry.title.text)
      if entry.content:
        print '    %s' % (entry.content.text)
      for email in entry.email:
        if email.primary and email.primary == 'true':
          print '    %s' % (email.address)
      # Show the contact groups that this contact is a member of.
      for group in entry.group_membership_info:
        print '    Member of group: %s' % (group.href)
      # Display extended properties.
      for extended_property in entry.extended_property:
        if extended_property.value:
          value = extended_property.value
        else:
          value = extended_property.GetXmlBlobString()
        print '    Extended Property %s: %s' % (extended_property.name, value)
    return len(feed.entry) + ctr

#   def PrintGroupsFeed(self, feed, ctr):
#     if not feed.entry:
#       print '\nNo groups in feed.\n'
#       return 0
#     for i, entry in enumerate(feed.entry):
#       print '\n%s %s' % (ctr+i+1, entry.title.text)
#       if entry.content:
#         print '    %s' % (entry.content.text)
#       # Display the group id which can be used to query the contacts feed.
#       #print '    Group ID: %s' % entry.id.text
#       # Display extended properties.
#       for extended_property in entry.extended_property:
#         if extended_property.value:
#           value = extended_property.value
#         else:
#           value = extended_property.GetXmlBlobString()
#         print '    Extended Property %s: %s' % (extended_property.name, value)
#     return len(feed.entry) + ctr

  def AddContacts(self, feed):
    ctr = 0
    print "Reading contacts.",
    while feed:
      # Print contents of current feed
      if not feed.entry:
        print '\nNo entries in feed.\n'
        return
      for i, entry in enumerate(feed.entry):
        #print entry
        if entry.content:
        	entry_name = entry.title.text
          	#print '    %s' % (entry.title.text),
          	if (len(entry.email) > 0):
          		entry_email = []
          		for email in entry.email:
				  entry_email.append(email.address)
				  #print '    %s' % (email.address),
				  db_entry = { "name": entry_name, "smtp": entry_email }  # This could potentially contain many things
				  self.SendToPlex(db_entry)
				  #print
				  #print db_entry
          	#else:
          		#print '   NO EMAIL'

      #feed = False
      # Prepare for next feed iteration
      next = feed.GetNextLink()
      if (next == None):
      	print
      	return
      feed = feed = self.gd_client.GetContactsFeed(next.href)
      print ".",
      sys.stdout.flush()

  def CreateVCard(self, entry):
    """Returns a vCard for a given Google Contacts entry"""
    
    # Create connections based on entry
    connections = []
    for an_email in entry["smtp"]:			# Gosh, does this work?
    	thingy = { "type": "plexus-message", "service": "smtp", "credential": an_email }  # New connection format
    	connections.append(thingy)
    	
    vcard = { "vcard": [ { "fn": entry["name"], "connections": connections } ] }
    return vcard
    
  def SendToPlex(self, entry):
	"""Sends the Google Contact entry to the Plex to be added to the social graph"""
	
	vcard = self.CreateVCard(entry)
	print vcard
	plx = plex.Plex()
	plx.add_from_jcard(vcard)
	plx.close()
	return

  def Run(self):
    """Retrieves the exhaustive list of contacts and displays name and primary email."""
    feed = self.gd_client.GetContactsFeed()
    self.AddContacts(feed)
    #self.PrintPaginatedFeed(feed, self.PrintFeed)  
    
def main():
  """Import Google Contacts extension using the GoogleContacts object."""
  # Parse command line options
  try:
    opts, args = getopt.getopt(sys.argv[1:], '', ['user=', 'pw='])
  except getopt.error, msg:
    print 'python contacts_example.py --user [username] --pw [password]'
    sys.exit(2)

  user = ''
  pw = ''
  # Process options
  for option, arg in opts:
    if option == '--user':
      user = arg
    elif option == '--pw':
      pw = arg

  # If running on Android, use Facade to get this information.  Possibly.
  try:
  	import android
	droid = android.Android()
	user = droid.dialogGetInput('Username', 'Google username', 'yourname@gmail.com').result
	if (user == None):
		return
	pw = droid.dialogGetPassword().result
	if (pw == None):
		return
  except:
	  while not user:
		print 'NOTE: Please run these tests only with a test account.'
		user = raw_input('Please enter your username: ')
	  while not pw:
		pw = getpass.getpass()
		if not pw:
		  print 'Password cannot be blank.'


  try:
    sample = GoogleContacts(user, pw)
  except gdata.service.BadAuthentication:
    print 'Invalid user credentials given.'
    return

  print 'It looks like we logged in successfully.  W00t!'
  sample.Run()


if __name__ == '__main__':
  main()