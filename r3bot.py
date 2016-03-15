#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twx.botapi import TelegramBot, Update
import r3door
import r3temp
import json


class r3bot():

    def __init__(self, apitoken):
        self.log('initializing r3bot ...')
        self.setupBot(apitoken)
        self.__loadBotState()
        self.log('initializing r3bot done!')

    def log(self, text):
        print text

    def setupBot(self, apitoken):
        """
        Setup the bot
        """
        self.bot = TelegramBot(apitoken)
        # self.bot.update_bot_info().wait()

    def initHook(self, hook):
        self.log('initializing callback hook %s ...' % hook)
        self.bot.set_webhook(url=hook)
        self.log('initialized callback hook!')

    def processHookRequest(self, request):
        self.log('received request on HOOK:')
        print request
        #update = Update.from_result(request)
        #print update.message
	print ' parsing message ...'
	print type(request)
        response = self.getReplyForUpdate(request)
        print ' parsing message done!'
	self.sendMessageToUser(response, request['message']['from']['id'])
        self.log('END prosessing message on hook')
        self.state['offset'] = update.update_id + 1

    def sendMessageToUser(self, text, user_id):
        self.bot.send_message(
            sender,
            text).wait()

    def getTemperatureString(self):
        """
        Retrieve temperature data
        using the r3 Space-API.
        """
        api = r3temp.r3temp()
        return '''
        Temperatures in r3:
        Temp Outside:           %s°C
        Temp in LoTHR:          %s°C
        Temp in CX:             %s°C
        Temp in OLGA Room:      %s°C
        Temp in OLGA freezer:   %s°C
        Temp in UPS Battery:    %s°C
        ''' % (
               api.getTempByName('Temp@Outside'),
               api.getTempByName('Temp@LoTHR'),
               api.getTempByName('Temp@CX'),
               api.getTempByName('Temp@OLGA Room'),
               api.getTempByName('Temp@OLGA freezer'),
               api.getTempByName('Temp@UPS Yellow Battery')
        )

    def getDoorstatusString(self):
        """
        Retrieve door status data
        using the r3 Space-API.
        """
        api = r3door.r3door()
        status = api.getDoorstatus()
        return '''
        Doorstatus of r3 frontdoor:
        locked: %s
        kontakted: %s
        ''' % (
            status[0], status[1]
        )

    def match(self, text, words):
        """
        Returns True if any of 'words' is contained
        in 'text', otherwise returns False.
        """
        return any(x in text for x in words)

    strings_door = ['door', 'tuer', u'tür', 'status']
    strings_temp = ['temp', 'temperature', 'temperatur', 'status']

    def getReplyForMessage(self, msg, sender):
        """
        Does the magic. Returns a string.
        """
        msgLower = msg.lower()
        if self.match(msgLower, self.strings_door):
            return self.getDoorstatusString()
        elif self.match(msgLower, self.strings_temp):
            return self.getTemperatureString()
        else:
            return '''
            Sorry, %s. I don\'t understand that (so far?) ...''' % (
                sender)

    def getReplyForUpdate(self, update):
        """
        Hands the given update to getReplyForMessage()
        and logs it using logupdate().
        Returns the returned string.
        """
        self.logUpdate(update)
        return self.getReplyForMessage(
            update['message']['text'],
            update['message']['from']['first_name'])

    def logUpdate(update):
        """
        Does a quick log of the received message
        to stdout.
        """
        self.log('%s: %s' % (
            update['message']['text'],
            update['message']['from']['first_name']))

    def __saveBotState(self):
        """
        Saves the bot's state to state.json file.
        """
        self.log('saving bot state ...')
        with open('state.json', 'w') as fp:
            json.dump(self.state, fp)

    def __loadBotState(self):
        """
        Loads the bot's state from state.json file.
        """
        self.log('loading bot state ...')
        try:
            with open('state.json', 'r') as fp:
                self.state = json.load(fp)
        except:
            self.state = dict()
            self.state['offset'] = 0
