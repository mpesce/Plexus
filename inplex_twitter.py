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
# Read in the contacts list from Twitter, add it to the Plex
# 
import sys, os
#import getopt
#import getpass
import yaml, json
import plex
import twitter

class TwitterContacts(object):
  """TwitterContacts object imports Twitter Contacts into the Plex."""

    
  def __init__(self):
    """Constructor for the TwitterContacts object.
    
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
    # Check to see if we have login credentials
    self.credentials = getLogin() 
    #print credentials
    if self.credentials == -1:
	  print "You don't have Twitter authorization, let's do that now..."
	  twitter_authorize()
	  self.credentials = getLogin()
	  
    self.api = api = twitter.Api(consumer_key="4a4AK5ZUpJu3fxNfaXb5A", consumer_secret="IRvMihJ6vVLIMcWDDIe945zoqMHiwfVY3FCbnasMAMk", access_token_key=self.credentials['oauth_token'], access_token_secret=self.credentials['oauth_token_secret'])
    if (self.api == None):
      raise BaseException()
    else:
      print 'Successful login to Twitter'

	# Now get our screen name, which we'll be needing later on
    #self.screen_name = self.get_my_screen_name()
    #print 'My screen name is %s' % self.screen_name
    
    # Now that we have the screen name, get my user info
    #self.user = self.api.GetUser(self.screen_name)
    #print self.user
    return

  def get_my_screen_name(self):
    statuses = self.api.GetUserTimeline(count=2)
    for status in statuses:
      screen_name = status.user.screen_name
      return screen_name	

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
				  db_entry = { "name": entry_name, "email": entry_email }  # This could potentially contain many things
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
    """Returns a vCard for a given Twitter Contact entry"""
    
    # Create connections based on entry
    connections = []
    for an_email in entry["twitter"]:			# Gosh, does this work?
    	thingy = { "twitter": an_email }
    	connections.append(thingy)
    	
    vcard = { "vcard": [ { "fn": entry["name"], "connections": connections } ] }
    return vcard
    
  def SendToPlex(self, entry):
	"""Sends the Twitter Contact entry to the Plex to be added to the social graph"""
	
	vcard = self.CreateVCard(entry)
	print vcard
	plx = plex.Plex()
	plx.add_from_jcard(vcard)
	plx.close()
	return

  # This function was taken from the Python-twitter implementation
  # But um, I've fixed it so that it actually works.
  # Hasn't anyone else needed this?
  # It now returns a tuple of (friends[], next_cursor)
  def GetFriends(self, user=None, cursor=-1):

    if not user and not self.api._oauth_consumer:
      raise twitter.TwitterError("twitter.Api instance must be authenticated")
    if user:
      url = '%s/statuses/friends/%s.json' % (self.api.base_url, user)
    else:
      url = '%s/statuses/friends.json' % self.api.base_url
    parameters = {}
    parameters['cursor'] = cursor
    jsondata = self.api._FetchUrl(url, parameters=parameters)
    data = json.loads(jsondata)
    #print data['next_cursor_str']
    self.api._CheckForTwitterError(data)
    return ([twitter.User.NewFromJsonDict(x) for x in data['users']], int(data['next_cursor_str']))

  def Run(self):
    """Retrieves the exhaustive list of contacts and displays name and primary email."""
    done = False
    curs = -1  # Get the whole lot
    while curs != 0:
      (friends, next_curs) = self.GetFriends(cursor=curs)
      #contact_list = ret["users"]
      #curs = ret["next_cursor"]
      for friend in friends:
        print "\"%s\"     %s" % (friend.name, friend.screen_name)
        #feed = self.gd_client.GetContactsFeed()
        #self.AddContacts(a_contact)
      curs = next_curs
      print 'Getting next list of friends...'

# Returns True if we are running on Android - use absolute paths
def isAndroid():
	try:
		import android
		#print "Android!"
		return True
	except:
		return False

def getAndroidPath():
	if isAndroid():
		return "/sdcard/sl4a/scripts/v2/"
	else:
		return ""

def getLogin():
    if (os.path.isfile(getAndroidPath() + ".twittercredentials")):
        fp = open(getAndroidPath() + ".twittercredentials", "r")
        a = yaml.load(fp)
        fp.close()
        return a
    else:
        return -1

def twitter_authorize():
	result = get_access_token()
	fp = open(getAndroidPath() + ".twittercredentials", "wb")  # This is not secure and must be fixed
	fp.writelines(yaml.dump(result))
	fp.close()


def get_access_token():
	
	# parse_qsl moved to urlparse module in v2.6
	try:
	  from urlparse import parse_qsl
	except:
	  from cgi import parse_qsl
	
	import oauth2 as oauth
	
	REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
	ACCESS_TOKEN_URL  = 'https://api.twitter.com/oauth/access_token'
	AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
	SIGNIN_URL        = 'https://api.twitter.com/oauth/authenticate'
	
	consumer_key    = "4a4AK5ZUpJu3fxNfaXb5A"
	consumer_secret = "IRvMihJ6vVLIMcWDDIe945zoqMHiwfVY3FCbnasMAMk"
	
	if consumer_key is None or consumer_secret is None:
	  print 'You need to edit this script and provide values for the'
	  print 'consumer_key and also consumer_secret.'
	  print ''
	  print 'The values you need come from Twitter - you need to register'
	  print 'as a developer your "application".  This is needed only until'
	  print 'Twitter finishes the idea they have of a way to allow open-source'
	  print 'based libraries to have a token that can be used to generate a'
	  print 'one-time use key that will allow the library to make the request'
	  print 'on your behalf.'
	  print ''
	  sys.exit(1)
	
	signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()
	oauth_consumer             = oauth.Consumer(key=consumer_key, secret=consumer_secret)
	oauth_client               = oauth.Client(oauth_consumer)
	
	print 'Requesting temp token from Twitter'
	
	resp, content = oauth_client.request(REQUEST_TOKEN_URL, 'GET')
	
	if resp['status'] != '200':
	  print 'Invalid respond from Twitter requesting temp token: %s' % resp['status']
	else:
	  request_token = dict(parse_qsl(content))
	  if isAndroid():  # We can launch a browser if it's Android
	  	theURL = '%s?oauth_token=%s' % (AUTHORIZATION_URL, request_token['oauth_token'])
	  	import android
	  	droid = android.Android()
	  	droid.startActivity('android.intent.action.VIEW', theURL)
	  else:		
		  print ''
		  print 'Please visit this Twitter page and retrieve the pincode to be used'
		  print 'in the next step to obtaining an Authentication Token:'
		  print ''
		  print '%s?oauth_token=%s' % (AUTHORIZATION_URL, request_token['oauth_token'])
		  print ''
	
	  pincode = raw_input('Pincode? ')
	
	  token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
	  token.set_verifier(pincode)
	
	  print ''
	  print 'Generating and signing request for an access token'
	  print ''
	
	  oauth_client  = oauth.Client(oauth_consumer, token)
	  resp, content = oauth_client.request(ACCESS_TOKEN_URL, method='POST', body='oauth_verifier=%s' % pincode)
	  access_token  = dict(parse_qsl(content))
	
	  if resp['status'] != '200':
		print 'The request for a Token did not succeed: %s' % resp['status']
		print access_token
	  else:
		print 'Your Twitter Access Token key: %s' % access_token['oauth_token']
		print '          Access Token secret: %s' % access_token['oauth_token_secret']
		print ''
		return access_token
    
def main():
  """Import Twitter contacts using the TwitterContacts object."""
  
  try:
    sample = TwitterContacts()
  except:
    print 'Could not log into Twitter.'
    return

  print 'It looks like we logged in successfully.  W00t!'
  sample.Run()


if __name__ == '__main__':
  main()