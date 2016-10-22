#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request
try:
    import config
except:
    import envconfig as config
from tbot import tbot

app = Flask(__name__)
bot = tbot(config.APITOKEN)
bot.initHook(config.HOOKURL)


@app.route('/hook/', methods=['POST'])
def hook():
    bot.processHookRequest(request.get_json())
    return "OK"


@app.route('/broadcast/', methods=['POST'])
def broadcast():
    msg, error = bot.processBroadcast(request.form)
    if msg:
        return msg
    elif error:
        return error
    else:
        return 'Something went wrong :('


@app.route("/")
def index():
    return "Yay! Telegram Hook working!"

if __name__ == "__main__":
    app.run(debug=True, port=PORT)
