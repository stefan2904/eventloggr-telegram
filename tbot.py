#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from twx.botapi import TelegramBot
from itsdangerous import JSONWebSignatureSerializer, BadSignature

class tbot():

    def __init__(self, apitoken, secret, owner_user_id):
        self.log('initializing r3bot ...')
        self.secret = secret
        self.owner_user_id = owner_user_id
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


    def match(self, text, words):
        """
        Returns True if any of 'words' is contained
        in 'text', otherwise returns False.
        """
        return any(x in text for x in words)

    def getReplyForMessage(self, msg, sender, sender_id):
        """
        Does the magic. Returns a string.
        """
        msgLower = msg.lower()
        if 'unsubscribe' in msgLower:
            return self.unsubscribeUser(msg, sender_id)
        elif 'subscribe' in msgLower:
            return self.subscribeUser(msg, sender_id)
        elif 'hook' in msgLower:
            return self.hook
        elif 'whoami' in msgLower:
            return str(sender_id)
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


    def processEventloggrMessage(self, input):

        if self.owner_user_id is None:
            return None, 'No owner set yet.'
        if 'data' not in input:
            return None, 'ERROR: no data found in request.'
        serializer = JSONWebSignatureSerializer(self.secret)
        try:
            data = serializer.loads(input['data'])
        except BadSignature:
            return None, 'ERROR: bad signature.'

        text = 'News from {service}: {source} wrote\n{text}'.format(service=data['service'], source=data['source'], text=data['text'])

        self.sendMessageToUser(text, self.owner_user_id)
        return 'OK', None

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
