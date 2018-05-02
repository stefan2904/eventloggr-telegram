#!/usr/bin/env python

import os

PORT = os.environ['BOT_PORT']
APITOKEN = os.environ['BOT_APITOKEN']
HOOKURL = os.environ['BOT_HOOKURL']

OWNER = os.environ['BOT_OWNER']
SECRET = os.environ['BOT_SECRET']  # shared eventloggr secret

DEBUG = os.getenv('BOT_DEBUG', False)
