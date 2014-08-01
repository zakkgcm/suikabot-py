import random
responses = ["pong", "butts", "bing", "bong", "dong", "wong", "gong"]

def irc_public (client, user, channel, message):
    if message.strip() == "ping":
        client.say(channel, random.choice(responses))

