import random
import datetime
import pytz

responses = ["pong", "butts", "bing", "bong", "dong", "wong", "gong", "ding", "wing", "ring", "that's gnu PLUS ping to you", "kentucky fried pingen", "burger ping", "ping of the hill", "xi jinping"]

bongzone = pytz.timezone('Europe/London')

def irc_public (client, user, channel, message):
    if message.strip('!#?.~') == "ping":
        client.say(channel, random.choice(responses))

    if message.strip('!#?.~') == 'bing':
        # i hate timezones
        bongs = bongzone.normalize(pytz.utc.localize(datetime.datetime.utcnow()).astimezone(bongzone)).hour
        #bongs = datetime.datetime.utcnow().hour
        if bongs > 12:
            bongs = bongs - 12

        client.say(channel, ' '.join(['bong' for x in range(0, bongs)])) 
