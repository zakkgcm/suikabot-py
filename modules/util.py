def ircmask_match (pattern, mask):
    '''Match an irc-style mask against a wildcard pattern.'''
    pattern = re.escape(pattern).replace('\\*', '.+')
    return re.match(pattern, mask) != None

def split_user (hostmask):
    nick, userhost = hostmask.split('!', 1)
    user, host = userhost.split('@', 1)

    return (nick, user, host)
