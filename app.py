#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request
app = Flask(__name__)


@app.route('/hook/', methods=['POST'])
def hook():
    print request
    return "OK"


@app.route("/")
def index():
    return "Yay! realraum Telegram Hook working!"

if __name__ == "__main__":
    app.run()
