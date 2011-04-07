import twitter, imaplib
import os, sys
import re, bitly
import ConfigParser

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
	config.read('config.ini')
	
	# Connect to IMAP server
	imap_server = config.get('imap', 'server')
	if verbose: print 'Connecting to', imap_server
	imap_connection = imaplib.IMAP4_SSL(imap_server)
	
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




M, T, B = open_connections()

if (M is not None) and (T is not None) and (B is not None):
	try:
		M.select('Chumby')
		typ, data = M.search(None, 'UNSEEN')
	except:
		print 'Could not access IMAP data'
	else:
		if len(data[0].split()) > 0:
			for num in data[0].split():
				typ, msg_data = M.fetch(num, '(BODY[TEXT])')
				content = msg_data[0][1].replace('\r', '').replace('\n','').split('Please do not')[0]
				msg = bitify_urls(api = B, text = content, verbose = True)
				if len(msg) <= 140:
					try:
						status = T.PostUpdate(msg)
					except TwitterError as e:
						print 'Twitter error:', e
				else:
					print 'Post too long, this needs a way to be handled!'
					
	M.close()
	M.logout()
	sys.exit