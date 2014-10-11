from modules import util

def irc_public (client, hostmask, channel, message):
    nick, user, host = util.ircmask_split(hostmask)
    if client.access_list.check(hostmask, client.access_list.LEVEL_OWNER):
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
    
    if message.startswith('!alias'):
        args = message.split(' ')[1:]
        cmd, target = args[0:2]
        
        print args

        if client.access_list.check(hostmask, client.access_list.LEVEL_OWNER) or \
           nick.lower() in client.alias_map.get_aliases(target.lower()):
            if cmd == 'add':
                alias = args[2]
                success = client.alias_map.add(target, alias)

                if success:
                    client.say(channel, 'Alias ({0} -> {1} successfully added!'.format(target, alias))
           
                print client.alias_map.aliases

            if cmd == 'remove':
                client.alias_map.remove(target)
