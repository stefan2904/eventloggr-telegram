#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from twx.botapi import TelegramBot
from itsdangerous import JSONWebSignatureSerializer, BadSignature


class tbot():

    def __init__(self, apitoken, secret, owner_user_id):
        self.log('initializing bot ...')
        self.secret = secret
        self.owner_user_id = owner_user_id
        self.setupBot(apitoken)
        self.__loadBotState()
        self.log('initializing bot done!')

    def log(self, text):
        print(text)

    def setupBot(self, apitoken):
        """
        Setup the bot
        """
        self.bot = TelegramBot(apitoken)

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
            return

        self.log('received request on HOOK:')
        print(request)

        print(' parsing message ...')
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

    def getReplyForMessage(self, msg, sender, sender_id):
        """
        Does the magic. Returns a string.
        """
        msgLower = msg.lower()

        if 'hook' in msgLower:
            return self.hook
        elif 'whoami' in msgLower:
            return '''
            name: {}
            id: {}
            '''.format(sender, str(sender_id))
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

    def logUpdate(self, update):
        """
        Does a quick log of the received message
        to stdout.
        """
        self.log('%s: %s' % (
            update['message']['text'],
            update['message']['from']['first_name']))

    def processEventloggrMessage(self, input):
        """
        Process a (signed) message from an eventloggr instance
        and sends it to the bot owner.
        """
        if self.owner_user_id is None:
            return None, 'No owner set yet.'
        if 'data' not in input:
            return None, 'ERROR: no data found in request.'
        serializer = JSONWebSignatureSerializer(self.secret)
        try:
            data = serializer.loads(input['data'])
        except BadSignature:
            return None, 'ERROR: bad signature.'

        text = 'News from {service}: {source} wrote\n{text}'.format(
            service=data['service'], source=data['source'], text=data['text'])

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
