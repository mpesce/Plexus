#!/usr/bin/python
import twitter
import os, sys, time, yaml, uuid, socket
import json
#import rsa
from yaml import Loader, Dumper
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Every module has a UUID associated with it, which becomes the item encoded in the signature
# Thus uniquely identifing both the module and the sender
listener_uuid = 'e2726948-68dd-5272-a437-0265f76f53a9'  # uuid.uuid5(uuid.NAMESPACE_DNS, 'plexus.relationalspace.org')
dest_id = "e2eb0d8b-b82c-5c2f-b6f1-dee1038fd9ae" # uuid.uuid5(uuid.NAMESPACE_DNS, 'mpesce.plexus.relationalspace.org')
mypod_ip = "74.207.224.149"
kuanyin_ip ="192.168.0.37"
android_ip = "192.168.0.148"

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

# Get your own IP address.  This is the IPV4 address, so when we go to IPV6, that'll need fixing...
# Also, if this is a multi-homed machine, this could return, erm, "indeterminate" (read: wrong) results.
def get_my_ipv4():
	return socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)[0][4][0]

def writeFile(content, file):
    fp = open(file, "wb")
    fp.writelines(yaml.dump(content))
    fp.close()


# The instance ID is a UUID specific to this instance, uniquely identifies this listener
def getInstance():
	#print "getInstance()"
	if (os.path.isfile(getAndroidPath() + ".twitter_listener")):
		fp = open(getAndroidPath()+ ".twitter_listener", "r")
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


def get_statuses(token):

	return statuses


def make_msg():

	msg = MIMEMultipart()
	msg['Subject'] = "Twitter status updates"
	msg['From'] = "mpesce@gmail.com"
	msg['To'] = "mark@markpesce.com"
	
	#print msg.as_string()
	return msg


def mail_msg(txt):

	# To transport by SMTP, we wrap our RFC2822-compliant message in another header. 
	# This allows us to have our way with the sender and receiver fields.  Muahahah.
	print "Sending mail..."
	import smtplib
	msg = MIMEText(txt)
	msg.set_charset('utf-8') 
	msg['Subject'] = "twitter_listener.py"
	s = smtplib.SMTP()
	s.set_debuglevel(False)
	s.connect("smtp.gmail.com", 587)
	s.ehlo()
	s.starttls()
	s.ehlo()
	s.login("mpesce@gmail.com", "********")
	s.sendmail("mark@markpesce.com", "mpesce@gmail.com", msg.as_string())
	s.close()


def mail_msg_plexus(txt):

	# To transport by SMTP, we wrap our RFC2822-compliant message in another header. 
	# This allows us to have our way with the sender and receiver fields.  Muahahah.
	print "Sending mail..."
	import smtplib
	msg = MIMEText(txt)
	msg.set_charset('utf-8') 
	msg['Subject'] = "twitter_listener.py"

	if (len(sys.argv) > 1):
		set_ip = sys.argv[1]
	else:
		set_ip = "localhost"
	s = smtplib.SMTP(set_ip, 4180)  # of course, this could be running anywhere, really
	s.sendmail("mark@markpesce.com", "mpesce@gmail.com", msg.as_string())
	s.quit()


def get_my_screen_name(api):
	statuses = api.GetUserTimeline(count=2)
	for status in statuses:
		screen_name = status.user.screen_name
		return screen_name	
	

# def make_msg(api, screen_name, update):
# 	plexus_data = { "service": "twitter", "update": update }
# 	#mime_header ="MIME-Version 1.0\nContent-Transfer-Encoding: 7bit\nContent-Type: plexus/update; charset=\"utf-8\"\n\n"
# 	msg = MIMEText(json.dumps(plexus_data))
# 	msg.set_charset('utf-8') 
# 	msg['Subject'] = str(uuid.uuid4())
# 		
# 	# Create the 'From' field by signing the UUID of the module with the private key
# 	#signature = rsa.sign(listener_uuid, keys['priv'])
# 	#print signature
# 	# Get the user to put into 'From' field
# 	msg['From'] = screen_name.encode('utf-8')
# 	msg['To'] = "TO BE COMPLETED"
# 
# 	return msg		

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

	start_id = None
	starting_timestamp = time.time()  # Current time
	dm_since = None
	count_num = 2 # a maximum of 50 statuses
	while True:

		api = twitter.Api(consumer_key="4a4AK5ZUpJu3fxNfaXb5A", consumer_secret="IRvMihJ6vVLIMcWDDIe945zoqMHiwfVY3FCbnasMAMk",
			access_token_key=credentials['oauth_token'], access_token_secret=credentials['oauth_token_secret'])
		screen_name = get_my_screen_name(api)  # odd way to do it, but whatevs
		
		# Check for DMs before we move along to the statuses (because they're more important, aren't they?)
		if (dm_since == None):
			print "Starting timestamp: ", starting_timestamp
			directs = api.GetDirectMessages()
		else:
			directs = api.GetDirectMessages(since_id=dm_since)
		for direct in directs:
			if dm_since < direct.id:
				dm_since = direct.id	# Keep things current

			if (direct.created_at_in_seconds > starting_timestamp):	 # Since we started up?
				name_list = [ direct.sender_screen_name.encode('utf-8'), ]
				plexus_data = { "service": "twitter", "plexus-message": direct.text.encode('utf-8'), "source": name_list, "when": str(direct.created_at_in_seconds) }
				msg = MIMEText(json.dumps(plexus_data))
				msg.set_charset('utf-8') 
				msg['To'] = screen_name.encode('utf-8') + "." + dest_id + "@plexus.relationalspace.org"  # That should be unique and global across Plexus
				msg['From'] = "plexus-message." + instance_id + "@plexus.relationalspace.org"  # Routing information for message type
				msg['Subject'] = str(uuid.uuid4())  # unique ID for tracking messages
				
				print msg.as_string()
				#mail_msg(msg.as_string())
				mail_msg_plexus(msg.as_string())
			
		statuses = api.GetFriendsTimeline(count=count_num, since_id=start_id)	
		for status in statuses:
		
			if start_id < status.id:
				start_id = status.id		# Keep latest status
			#txt = yaml.dump(status)
			#txt = status.user.screen_name.encode('utf-8') + ": " + status.text.encode('utf-8')
			#msg = make_msg(api, screen_name, status.text.encode('utf-8'))
			name_list = [ status.user.screen_name.encode('utf-8'), ]
			plexus_data = { "service": "twitter", "plexus-update": status.text.encode('utf-8'), "source": name_list, "when": str(status.created_at_in_seconds) }
			#mime_header ="MIME-Version 1.0\nContent-Transfer-Encoding: 7bit\nContent-Type: plexus/update; charset=\"utf-8\"\n\n"
			msg = MIMEText(json.dumps(plexus_data))
			msg.set_charset('utf-8') 
				
			# Create the 'From' field by signing the UUID of the module with the private key
			#signature = rsa.sign(listener_uuid, keys['priv'])
			#print signature
			# Get the user to put into 'From' field
			msg['To'] = screen_name.encode('utf-8') + "." + dest_id + "@plexus.relationalspace.org"  # That should be unique and global across Plexus
			msg['From'] = "plexus-update." + instance_id + "@plexus.relationalspace.org"  # Routing information for message type
			msg['Subject'] = str(uuid.uuid4())  # unique ID for tracking messages
			
			print msg.as_string()
			#mail_msg(msg.as_string())
			mail_msg_plexus(msg.as_string())
		print "Sleeping..."
		time.sleep(30)			# wait 30 seconds, and do it all again
