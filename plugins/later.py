import time
import humanize
from collections import defaultdict

class Laters (defaultdict):
    def add (self, target, user, msg):
        self.get(target).append((user, msg, time.time()))
   
    def has (self, target):
        return target.lower() in self
     
    def get (self, target):
        return self[target.lower()]

    def remove (self, target):
        del self[target.lower()]

    def limitcheck (self, target, user):
        return len([l for l in self.get(target) if l[0].lower() == user.lower()]) < 3

    def load (self, client):
        self.clear()
        self.update(client.data_writer.get('laters.db'))

    def commit (self, client):
        client.data_writer.add('laters.db', dict(self))
        
laters = Laters(list)

def init (client):
    laters.load(client)

def irc_public (client, user, channel, message):
    user, _ = user.split('!', 1)

    # check for saved laters first
    if laters.has(user):
        lats = laters.get(user)
        for l in lats:
            sender, msg, t = l
       
            t = time.time() - t

            client.say(channel, "{0}: Sent {1}: <{2}> {3}".format(
                user, humanize.naturaltime(t), sender, msg
            ))

        laters.remove(user)
        laters.commit(client)
    
    # process commands
    if message.startswith('!later'):
        _, cmd, target, msg = message.split(' ', 3)
        
        if cmd in ['tell', 'remind']:
            t = target.lower()
            if t in ['xpc', 'xpcybic', 'xpcynic', 'xpcyphone', 'xpcdroid']:
                client.say(channel, "Shhh!!! You know xpc doesn't like that!")
            else:
                if laters.limitcheck(target, user):
                    laters.add(target, user, msg)
                    client.say(channel, "Okay, I'll remind {0} later!".format(target))
                    laters.commit(client)
                else:
                    client.say(channel, "You already left {0} too many reminders!".format(target))
