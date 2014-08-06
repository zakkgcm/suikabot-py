import time
import datetime
import humanize
import parsedatetime

from modules import util

reminders = []
pdt = parsedatetime.Calendar()

def init (client):
    for r in client.data_writer.get("reminders.db"):
        schedule_reminder(client, r)

    save(client)

def save (client):
    client.data_writer.add("reminders.db", reminders)

def schedule_reminder (client, reminder):
    nick, t, channel, remindtime, remindmsg = reminder
    reminddelta = remindtime - time.time()

    if reminddelta > 0:
        reminders.append(reminder)
        client.schedule(reminddelta, client.say, channel, "{0}: <{1}> {2}".format(t, nick, remindmsg))

def irc_public (client, hostmask, channel, message):
    nick, user, host = util.ircmask_split(hostmask)
    
    if message.startswith('!remind'):
        _, target, msg = message.split(' ', 2)
        dmsg, remindmsg = msg.split(':', 1)

        remindmsg = remindmsg.strip()
        t = target.lower()
       
        if t == "me":
            t = nick.lower()

        dtime, _, _, _, _ = pdt.nlp(dmsg)[0] # first matched date-like object
        remindtime = time.mktime(dtime.timetuple())
        #remindmsg = (msg[:spos] + msg[epos:]).strip()

        reminddelta = remindtime - time.time()
        if reminddelta < 0:
            client.say(channel, "I'm not a time traveler!")
        else:
            schedule_reminder(client, (nick, t, channel, remindtime, remindmsg))
            save(client)

            client.say(channel, "Okay, I'll remind {0} then!".format(t))
