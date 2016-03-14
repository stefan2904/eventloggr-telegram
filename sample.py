#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twx.botapi import TelegramBot
import r3door
import r3temp
import config


def setupBot(apitoken):
    """
    Setup the bot
    """
    bot = TelegramBot(apitoken)
    bot.update_bot_info().wait()
    return bot


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
        status[0], status[1])


def match(text, words):
    """
    Returns True if any of 'words' is contained
    in 'text', otherwise returns False.
    """
    return any(x in text for x in words)


strings_door = ['door', 'tuer', u'tür', 'status']
strings_temp = ['temp', 'temperature', 'temperatur', 'status']


def getReplyForMessage(msg, sender):
    msgLower = msg.lower()
    if match(msgLower, strings_door):
        return getDoorstatusString()
    elif match(msgLower, strings_temp):
        return getTemperatureString()
    else:
        return 'Sorry, %s. I don\'t understand that (so far?) ...' % (sender)


def getReplyForUpdate(update):
    logUpdate(update)
    return getReplyForMessage(
        update.message.text,
        update.message.sender.first_name)


def logUpdate(update):
    print '%s: %s' % (
        update.message.sender.first_name, update.message.text)


def updateLoop(bot):
    offset = 0
    running = True
    while running:
        updates = bot.get_updates(offset=offset).wait()
        for update in updates:
            offset = update.update_id + 1
            reply = getReplyForUpdate(update)
            bot.send_message(
                update.message.sender.id,
                reply).wait()


if __name__ == '__main__':
    bot = setupBot(config.APITOKEN)
    print '> %s ready to rock!' % bot.username
    if unsetWebhook(bot):
        print '> successfully unset webhook.'
    updateLoop(bot)
