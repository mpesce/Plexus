#!/usr/bin/python
import twitter
import os, sys, time, yaml, uuid
import json
import smtpd, asyncore
#import rsa
from yaml import Loader, Dumper
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.parser import Parser
import email
import plxaddr

# Every module has a UUID associated with it, which becomes the item encoded in the signature
# Thus uniquely identifing both the module and the sender
sharer_uuid = 'fdad1fd4-0d1f-547c-bca4-e9dece750532'  # uuid.uuid5(uuid.NAMESPACE_DNS, 'twitter.plexus.relationalspace.org')
dest_id = "dfd51f44-c44f-5d75-973f-2eef4854a4e5" # uuid.uuid5(uuid.NAMESPACE_DNS, 'twitter.mpesce.plexus.relationalspace.org')
mypod_ip = "74.207.224.149"
kuanyin_ip ="192.168.0.37"

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

def writeFile(content, file):
    fp = open(file, "wb")
    fp.writelines(yaml.dump(content))
    fp.close()


# The instance ID is a UUID specific to this instance, uniquely identifies this listener
def getInstance():
	#print "getInstance()"
	if (os.path.isfile(getAndroidPath() + ".twitter_listener")):
		fp = open(getAndroidPath() + ".twitter_listener", "r")
		a = yaml.load(fp)
		fp.close()
		return a
	else:
		return -1


#Create an instance ID if one does not yet exist
def genInstance():
	print "Generating instance UUID..."
	instance_id = str(uuid.uuid4())
	writeFile(instance_id, getAndroidPath() + ".twitter_listener")
	print "Done!"


# Generate an RSA keypair
def genKey():
    print "Generating your keypair, THIS WILL TAKE A LONG TIME.  At least ten minutes.  Make a nice cuppa..."
    keypair = rsa.newkeys(512)  # Should be secure until 2030.  Well, that's what they say, anyway...
    writeFile(keypair[0], getAndroidPath() + ".plexus_public_key")  # This is so not secure
    writeFile(keypair[1], getAndroidPath() + ".plexus_private_key") # THis is especially not secure
    print "Done!"
 

# Retrieve the RSA keypair
def getPubPriv():
    if (os.path.isfile(getAndroidPath() + ".plexus_public_key") and os.path.isfile(getAndroidPath() + ".plexus_private_key")):
        fp = open(getAndroidPath() + ".plexus_public_key", "rb")
        pubkey = yaml.load(fp)
        fp = open(getAndroidPath() + ".plexus_private_key", "rb")
        privkey = yaml.load(fp)
        fp.close()
        return {'priv': privkey, 'pub': pubkey}
    else:
        return -1


def getLogin():
    if (os.path.isfile(getAndroidPath() + ".twittercredentials")):
        fp = open(getAndroidPath() + ".twittercredentials", "r")
        a = yaml.load(fp)
        fp.close()
        return a
    else:
        return -1


def authorize():
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
		inner_data = msg.get_payload()
		print inner_data
		inner_msg = Parser().parsestr(inner_data)
		process_message(inner_msg)


# Format for From: is username@instanceID.plexus.relationalspace.org
# Where username is the account name / handle of the user account
# And the instanceID is the uuid for the process sending the message
def unpack_sender(adr):
	parts = adr.split("@")
	moreparts = parts[1].split(".")
	return { "user": parts[0], "listenerid": moreparts[0] }


# Format for To: is type@destID.plexus.relationalspace.org
# Where type is the type of message (update, command, post, etc...)
# And the destID is the ID of the destination Plexus process.  Which should be us.  Hopefully.
def unpack_to(to):
	parts = to.split("@")
	moreparts = parts[1].split(".")
	return { "type": parts[0], "destid": moreparts[0] }


# All of the built-in types are validated here.  
# There's only two of them at the moment
def validate_type(the_type):
	if (the_type.find(u'plexus-update') == 0):
		return True
	if (the_type.find(u'plexus-message') == 0):
		return True
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


# All incoming messages from whatever transport make their way to this function
# They're read in, parsed, and checked for validity
# If they're valid, they should end up on the DQ
def process_message(msg):
	print "process_message"	

	ph = plxaddr.parse_headers(msg)		# This should render lots of useful information.  No, seriously.
	#print ph
	if (ph == None):
		print "Garbled headers, rejecting"
		return

# 	msgid = msg['Subject']		# Should have a UUID therein - some way to validate this?
# 	
# 	mfrom = msg['From']		# Get the addressee information
# 	f = unpack_sender(mfrom)
# 	print f
# 
# 	mto = msg['To']
# 	to = unpack_to(mto)
# 	print to
# 
# 	if validate_type(to['type']):
# 		print "Type valid"
# 	else:
# 		print "Type invalid"
# 		return

	contents = msg.get_payload()
	if validate_payload(contents):
		print "Contents valid"
	else:
		print "Contents invalid"
		return
	content_object = json.loads(contents)	# Now we have a lovely object with stuff in it
	
	# If this is an update, we should send an update out 
	# If this is a message, we should send a DM
# 	if (to['type'].find(u'plexus-update') == 0):
# 		stat = do_sendUpdate(content_object)
# 	elif (to['type'].find(u'plexus-message') == 0):
# 		do_sendDM(content_object)

	if (ph['plexus-identifier'].find(u'plexus-update') == 0):
		stat = do_sendUpdate(content_object)
	elif (ph['plexus-identifier'].find(u'plexus-message') == 0):
		do_sendDM(content_object)

# We do everything here that we need to so we can post an update to Twitter.
def do_sendUpdate(stuff):

	credentials = getLogin()		# If this fails, well, we're screwed.  So it better not fail.
	if (credentials == -1):
		return

	# Ok, open access to the Twitter API, using our credentials
	api = twitter.Api(consumer_key="4a4AK5ZUpJu3fxNfaXb5A", consumer_secret="IRvMihJ6vVLIMcWDDIe945zoqMHiwfVY3FCbnasMAMk",
		access_token_key=credentials['oauth_token'], access_token_secret=credentials['oauth_token_secret'])
	stat = None
	stat = api.PostUpdate(status=stuff['plexus-update'])  # And post the update
	return stat

def do_sendDM(stuff):
	credentials = getLogin()		# If this fails, well, we're screwed.  So it better not fail.
	if (credentials == -1):
		return

	# Ok, open access to the Twitter API, using our credentials
	api = twitter.Api(consumer_key="4a4AK5ZUpJu3fxNfaXb5A", consumer_secret="IRvMihJ6vVLIMcWDDIe945zoqMHiwfVY3FCbnasMAMk",
		access_token_key=credentials['oauth_token'], access_token_secret=credentials['oauth_token_secret'])
	thedm = api.PostDirectMessage(user=stuff['destination'][0], text=stuff['plexus-message'])
	return
		

if __name__ == "__main__":

	# Check to see if we have a keypair
#	keys = getPubPriv()
#	if keys == -1:
#		print "No RSA keypair, we've got to generate them!"
#		genKey()
#		keys = getPubPriv()

	# Check to see if we have login credentials
	credentials = getLogin() 
	#print credentials
	if credentials == -1:
		print "You don't have Twitter authorization, let's do that now..."
		authorize()
		credentials = getLogin()
#	else:
#		print "We already have authorization, so let's grab some statuses..."

	# Get the Instance ID
	instance_id = getInstance()
	if instance_id == -1:
		print "We don't have an instance ID yet, must create it"
		genInstance()
		instance_id = getInstance()

	if (len(sys.argv) > 1):
		set_ip = sys.argv[1]
	else:
		set_ip = "localhost"
		
	print "Starting Plexus SMTP interface on", set_ip, "port 4180"
	server = PlexusSMTPServer((set_ip, 4180), None)
	asyncore.loop()

