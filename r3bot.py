#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twx.botapi import TelegramBot
import r3door
import r3temp
import json


class r3bot():

    def __init__(self, apitoken):
        self.log('initializing r3bot ...')
        self.setupBot(apitoken)
        self.__loadBotState()

    def log(self, text):
        print text

    def setupBot(self, apitoken):
        """
        Setup the bot
        """
        self.bot = TelegramBot(apitoken)
        self.bot.update_bot_info().wait()

    def initHook(self, hook):
        self.bot.set_webhook(url=hook)

    def processHookRequest(self, request):
        print request

    def __saveBotState(self):
        """
        Saves the bot's state to state.json file.
        """
        with open('state.json', 'w') as fp:
            json.dump(self.state, fp)

    def __loadBotState(self):
        """
        Loads the bot's state from state.json file.
        """
        try:
            with open('state.json', 'r') as fp:
                self.state = json.load(fp)
        except:
            self.state = dict()
            self.state['offset'] = 0
