def irc_public (client, user, channel, message):
    # log messages to stdout
    print "<{0}:{1}> {2}".format(user, channel, message)

    # send a message to the server
    if message.startswith("you're a big guy"):
        client.say(channel, "for you")
