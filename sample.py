#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twx.botapi import TelegramBot
import r3door
import r3temp
import config
import json


def setupBot(apitoken):
    """
    Setup the bot
    """
    bot = TelegramBot(apitoken)
    bot.update_bot_info().wait()
    return bot


def saveBotState(state):
    with open('state.json', 'w') as fp:
        json.dump(state, fp)


def loadBotState():
    try:
        with open('state.json', 'r') as fp:
            state = json.load(fp)
    except:
        state = dict()
        state['offset'] = 0
    return state


def unsetWebhook(bot):
    """
    Since we will not be able to receive updates
    using getUpdates for as long as an outgoing
    webhook is set up, we need to unset it here.
    """
    return bot.set_webhook(url=None)


def getTemperatureString():
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


def getDoorstatusString():
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


def match(text, words):
    """
    Returns True if any of 'words' is contained
    in 'text', otherwise returns False.
    """
    return any(x in text for x in words)


strings_door = ['door', 'tuer', u'tür', 'status']
strings_temp = ['temp', 'temperature', 'temperatur', 'status']


def getReplyForMessage(msg, sender):
    """
    Does the magic. Returns a string.
    """
    msgLower = msg.lower()
    if match(msgLower, strings_door):
        return getDoorstatusString()
    elif match(msgLower, strings_temp):
        return getTemperatureString()
    else:
        return 'Sorry, %s. I don\'t understand that (so far?) ...' % (sender)


def getReplyForUpdate(update):
    """
    Hands the given update to getReplyForMessage()
    and logs it using logupdate().
    Returns the returned string.
    """
    logUpdate(update)
    return getReplyForMessage(
        update.message.text,
        update.message.sender.first_name)


def logUpdate(update):
    """
    Does a quick log of the received message
    to stdout.
    """
    print '%s: %s' % (
        update.message.sender.first_name, update.message.text)


def updateLoop(bot, state):
    """
    Retrieves updates in an infinite loop.
    Hands received update to getReplyForUpdate()
    and sends the returned string to the user
    via Telegram.
    """
    running = True
    while running:
        updates = bot.get_updates(offset=state['offset']).wait()
        for update in updates:
            state['offset'] = update.update_id + 1
            reply = getReplyForUpdate(update)
            bot.send_message(
                update.message.sender.id,
                reply).wait()


if __name__ == '__main__':
    """
    main code.
    runs this script in an (infinite) loop,
    until a KeyboardInterrupt is caught.
    """
    bot = setupBot(config.APITOKEN)
    state = loadBotState()
    print '> %s ready to rock! offset = %d' % (
        bot.username, state['offset'])
    if unsetWebhook(bot):
        print '> successfully unset webhook.'
    try:
        updateLoop(bot, state)
    except KeyboardInterrupt:
        pass
    print 'shutting down bot ... ',
    saveBotState(state)
    print 'done!'
