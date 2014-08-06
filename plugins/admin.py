def irc_public (client, user, channel, message):
    if client.access_list.check(user, client.access_list.LEVEL_OWNER):
        if message.startswith('!'):
            args = message.split(' ')
            cmd = args.pop(0)
           
            if cmd == '!access':
                client.access_list.add(args[0],  int(args[1]))
                client.say(channel, 'Added mask {0} with level {1}'.format(args[0], args[1]))

            if cmd == '!join':
                client.join(args[0])
            
            if cmd == '!leave':
                client.leave(channel)
            
            if cmd == '!reload':
                client.plugins.reload()
                client.say(channel, 'Plugins Reloaded!')
