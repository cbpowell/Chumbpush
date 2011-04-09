import imaplib2, time
from threading import *
import os, sys
import twitter, bitly
import ConfigParser, re

def bitify_urls(api, text, verbose=False):
	pat_url = re.compile(  r'''http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+''')
	for url in re.findall(pat_url, text):
		if verbose: print 'Long url', url
		try:
			short_url = api.shorten(url)
		except:
			print 'Bitly Error!'
			return text
		else:
			text = text.replace(url, short_url)
			return text

def open_connections(verbose=False):
	# Read from config file
	config = ConfigParser.ConfigParser()
	#config.read('config.ini')
	config.read([os.path.expanduser('~/.chumbpush')])
	
	# Connect to IMAP server
	imap_server = config.get('imap', 'server')
	if verbose: print 'Connecting to', imap_server
	imap_connection = imaplib2.IMAP4_SSL(imap_server)
	
	# Login to our account
	imap_username = config.get('imap', 'username')
	imap_password = config.get('imap', 'password')
	if verbose: print 'Logging in as', imap_username
	imap_connection.login(imap_username, imap_password)
	
	# Set up Twitter API
	twitter_consumer_key = config.get('twitter', 'consumer_key')
	twitter_consumer_secret = config.get('twitter', 'consumer_secret')
	twitter_access_token_key = config.get('twitter', 'access_token_key')
	twitter_access_token_secret = config.get('twitter', 'access_token_secret')
	twitter_api = twitter.Api(consumer_key = twitter_consumer_key, consumer_secret = twitter_consumer_secret, access_token_key = twitter_access_token_key, access_token_secret = twitter_access_token_secret)
	
	# Set up Bitify API
	bitly_login = config.get('bitly', 'login')
	bitly_apikey = config.get('bitly', 'apikey')
	bitify = bitly.Api(login = bitly_login, apikey = bitly_apikey)
	
	return imap_connection, twitter_api, bitify

# from http://blog.timstoop.nl/2009/03/11/python-imap-idle-with-imaplib2/
class Idler(object):
	def __init__(self, email, twitter, bitly):
		self.thread = Thread(target=self.idle)
		self.M = email
		self.T = twitter
		self.B = bitly
		self.event = Event()
	
	def start(self):
		self.thread.start()
    
	def stop(self):
		print 'Stopping idler thread'
		self.event.set()
	
	def join(self):
		self.thread.join()
	
	def idle(self):
		while True:
			if self.event.isSet():
				return
			self.needsync = False
			def callback(args):
				if not self.event.isSet():
					self.needsync = True
					self.event.set()
			
			self.M.idle(callback=callback)
			
			self.event.wait()
			
			if self.needsync:
				self.event.clear()
				self.dosync()
	
	def dosync(self):
		print "Got an event!"
		typ, data = M.search(None, 'UNSEEN')
		if len(data[0].split()) > 0:
			for num in data[0].split():
				# retrieve data for email, marking as read in the process (could use (BODY.PEEK[TEXT]) to avoid marking as read)
				typ, msg_data = M.fetch(num, '(BODY[TEXT])')
				
				# strip newlines and carriage retunrs, and split at 'Please do not reply' to chop off 'Please do not reply to this email...' parts
				content = msg_data[0][1].replace('\r', '').replace('\n','').split('Please do not reply')[0]
				
				# replace URLs with short URLs
				msg = bitify_urls(api = B, text = content, verbose = True)
				
				# post message if it's shorter than 140
				if len(msg) <= 140:
					try:
						status = T.PostUpdate(msg)
					except TwitterError as e:
						print 'Twitter error:', e
				else:
					# shorten otherwise (coming soon)
					print 'Post too long, this needs a way to be handled!'

try:
	M, T, B = open_connections()
	M.select('Chumby')
	idler = Idler(M, T, B)
	idler.start()
	time.sleep(4*60)
finally:
	idler.stop()
	idler.join()
	M.close()
	M.logout()
	sys.exit()
