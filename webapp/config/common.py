import os

# Common configuration variables not dependent on environment
# FIXME: Make it compatible with docker setup
DEBUG = False
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DATABASE_NAME = "RunningTracker"