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
        print(text)

    def setupBot(self, apitoken):
        """
        Setup the bot
        """
        self.bot = TelegramBot(apitoken)
        # self.bot.update_bot_info().wait()

    def initHook(self, hook):
        self.log('initializing callback hook %s ...' % hook)
        self.bot.set_webhook(url=hook)
        self.hook = hook
        self.log('initialized callback hook!')

    def processHookRequest(self, request):
        # need to reaload every time since there are multiple workers ...
        self.__loadBotState()
        if not self.isMessageNew(request['update_id']):
            print('Message is not new. Skipping ...')
            # return
        self.log('received request on HOOK:')
        print(request)
        # update = Update.from_result(request)
        # print update.message
        print(' parsing message ...')
        # print type(request)
        response = self.getReplyForUpdate(request)
        print(' parsing message done!')
        self.sendMessageToUser(response, request['message']['from']['id'])
        self.log('END prosessing message on hook')
        self.updateOffset(request['update_id'])

    def updateOffset(self, update_id):
        self.state['offset'] = update_id + 1
        self.__saveBotState()

    def isMessageNew(self, update_id):
        return update_id >= self.state['offset']

    def sendMessageToUser(self, text, user_id):
        self.bot.send_message(
            user_id,
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

    def getReplyForMessage(self, msg, sender, sender_id):
        """
        Does the magic. Returns a string.
        """
        msgLower = msg.lower()
        if self.match(msgLower, self.strings_door):
            return self.getDoorstatusString()
        elif self.match(msgLower, self.strings_temp):
            return self.getTemperatureString()
        elif 'unsubscribe' in msgLower:
            return self.unsubscribeUser(msg, sender_id)
        elif 'subscribe' in msgLower:
            return self.subscribeUser(msg, sender_id)
        elif 'hook' in msgLower:
            return self.hook
        else:
            print('unknown message: %s' % msg)
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
            update['message']['from']['first_name'],
            update['message']['from']['id'])

    def __getSubscriptionLists(self):
        if 'subscriptions' not in self.state:
            return None
        return ', '.join(self.state['subscriptions'])

    def __parseSubscriptionStr(self, msg):
        words = msg.split()
        if len(words) != 2:
            sublists = self.__getSubscriptionLists()
            return 'Available lists: %s' % sublists, None
        return None, words[1]

    def processBroadcast(self, request):
        if 'list' not in request or 'text' not in request:
            print request
            return None, 'ERROR: Invalid request.'
        # need to reaload every time since there are multiple workers ...
        self.__loadBotState()
        return self.broadcastToList(request['list'], request['text'])

    def broadcastToList(self, sublist, text):
        if 'subscriptions' not in self.state:
            return None, 'ERROR: no subscription lists!'
        if sublist not in self.state['subscriptions']:
            return None, 'ERROR: subscription list %s not found!' % sublist
        i = 0
        for user_id in self.state['subscriptions'][sublist]:
            self.sendMessageToUser(text, user_id)
            i += 1
        return 'successfully send to %d users' % i, None

    def subscribeUser(self, msg, sender_id):
        if 'subscriptions' not in self.state:
            self.state['subscriptions'] = dict()
        error, sublist = self.__parseSubscriptionStr(msg)
        if error is not None:
            return error
        print('subscribing to %s ...' % sublist)
        if sublist not in self.state['subscriptions']:
            # return 'list %s does not exist!' % sublist
            self.state['subscriptions'][sublist] = []
        if sender_id in self.state['subscriptions'][sublist]:
            return 'already subscribed to %s list ...' % sublist
        self.state['subscriptions'][sublist].append(sender_id)
        self.__saveBotState()
        return 'successfully subscribed to %s list!' % sublist

    def unsubscribeUser(self, msg, sender_id):
        if 'subscriptions' not in self.state:
            return 'nothing to do: no subscription lists!'
        error, sublist = self.__parseSubscriptionStr(msg)
        if error is not None:
            return error
        if sublist not in self.state['subscriptions']:
            return 'nothing to do: subscription list %s not found!' % sublist
        print('unsubscribing from %s ...' % sublist)
        if sender_id not in self.state['subscriptions'][sublist]:
            return 'not subscribed to %s list ...' % sublist
        self.state['subscriptions'][sublist].remove(sender_id)
        self.__saveBotState()
        return 'successfully unsubscribed from %s list!' % sublist

    def logUpdate(self, update):
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
