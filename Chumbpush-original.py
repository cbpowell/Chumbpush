import twitter
import imaplib
import os
import sys
import re
import bitly

def bitify_urls(text):
	pat_url = re.compile(  r'''http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+''')
	bitify = bitly.Api(login='bitly_login', apikey='bitley_apikey')
	for url in re.findall(pat_url, text):
		short_url = bitify.shorten(url)
		text = text.replace(url, short_url)
	
	return text

server = 'your_imap_server'
username = 'your_imap_login'
password = 'your_imap_password'

M = imaplib.IMAP4_SSL(server)
M.login(username, password)
try:
	M.select('Chumby')
	typ, data = M.search(None, 'UNSEEN')
	if len(data[0].split()) > 0:
		api = twitter.Api(consumer_key='consumer_key', consumer_secret='consumer_secret', access_token_key='access_token_key', access_token_secret='access_token_secret')
		for num in data[0].split():
			typ, msg_data = M.fetch(num, '(BODY[TEXT])')
			msg = bitify_urls(msg_data[0][1].replace('\r', '').replace('\n',''))
			if len(msg) < 140:
				status = api.PostUpdate(msg)
			#else:
				#too long! handle it
	
finally:
	M.close()
	M.logout()
	sys.exit