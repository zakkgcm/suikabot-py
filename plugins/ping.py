import random
responses = ["pong", "butts", "bing", "bong", "dong", "wong", "gong", "ding", "wing", "ring", "that's gnu PLUS ping to you", "kentucky fried pingen", "burger ping", "ping of the hill"]

def irc_public (client, user, channel, message):
    if message.strip() == "ping":
        client.say(channel, random.choice(responses))

