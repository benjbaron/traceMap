import os
from urlparse import urlsplit
from pymongo import Connection


def authenticate_in_mongodb():
	url = os.getenv('MONGO_URI', 'mongodb://localhost:27017/tracemap')
	parsed = urlsplit(url)
	db_name = parsed.path[1:]

	# Get your DB
	db = Connection(url)[db_name]

	# Authenticate
	if '@' in url:
	    user, password = parsed.netloc.split('@')[0].split(':')
	    db.authenticate(user, password)

	return db

