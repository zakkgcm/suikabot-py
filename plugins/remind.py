import time
import datetime
import humanize
import parsedatetime
import random

from modules import util
from collections import defaultdict

reminders = defaultdict(list)
pdt = parsedatetime.Calendar()

def init ():
    global reminders # FIXME: PUKE
    reminders = data_writer.get("reminders.db")

def client_connected (client):
    # this runs on every connect, but it's okay since we get a new client object every time 
    global reminders # FIXME: PUKE

    # purge reminders that have passed
    # FIXME: be more intelligent about this
    reminders[client.server] = [ r for r in reminders[client.server] if schedule_reminder(client, r) ]
    save(client)

def save (client):
    data_writer.add("reminders.db", dict(reminders))

def schedule_reminder (client, reminder):
    nick, t, channel, remindtime, remindmsg = reminder
    dtime = datetime.datetime.fromtimestamp(remindtime) + datetime.timedelta(microseconds=999999)
    reminddelta = remindtime - time.time()
    
    if reminddelta > 0: # only in the future
        client.schedule(reminddelta, client.msg, channel, "{0}: Sent {1}: <{2}> {3}".format(
            t, humanize.naturaltime(dtime - datetime.datetime.now()), nick, remindmsg
        ))

        return True

    return False

def irc_public (client, hostmask, channel, message):
    nick, user, host = util.ircmask_split(hostmask)
    
    if message.startswith('!remind'):
        _, target, msg = message.split(' ', 2)
        dmsg = msg.strip()
        #dmsg, remindmsg = msg.split(':', 1)

        t = target.lower()
       
        if t == "me":
            t = nick.lower()

        matches = pdt.nlp(dmsg)
        if matches != None:
                dtime, flags, spos, epos, mtext = matches[0] # first matched date-like object

                # convert into unix timestamp FIXME: probably blows up when timezone/DST
                remindtime = time.mktime(dtime.timetuple())
                remindmsg = (msg[:spos] + msg[epos:]).strip()

                if remindmsg in ['oven', 'stove', 'microwave']:
                    remindmsg = "BEEP" * random.randint(5, 8)

                reminder = (nick, t, channel, remindtime, remindmsg)
                if schedule_reminder(client, reminder):
                    reminders[client.server].append(reminder)
                    save(client)
                    client.msg(channel, "Okay, I'll remind {0} {1}!".format(t, humanize.naturaltime(dtime + datetime.timedelta(microseconds=999999))))
                else:
                    client.msg(channel, "I'm not a time traveler!")
        else:
                client.msg(channel, "Sorry, I didn't catch that....")
