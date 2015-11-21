import sys
import re

# parsing dictionaries
command_verbs = [
    'give',
    'bullying',
]

command_tverb = [
    'is'
]

command_prep = [
    'to'
]

command_desc = [
    'glass',
    'cup'
]

command_nouns = [
    'sake',
    'tea'
]


def match_command (line):
    '''Return if a line is a command and the line without the command identifier.'''
    match_kw = 'suika|suika_ibuki|suikaibuki|suika1buki|suika_1buki'
    match_punct = ',.?!'
    match_re = '^({0}[{1}]*)|({0}[{1}]*)$'.format(match_kw, match_punct)

    return (re.match(match_re, line) != None,
            re.sub(match_re, '', line))

def parse_command (line):
    '''Parse a natural language line into a command dictionary'''
    words = re.split('[,\s]+', line)

    command = {}

    # ""language"" processing
    pword = ''
    for word in words:
        if word in command_verbs:
            command['verb'] = word
        elif word in command_nouns:
            command['dobject'] = word
            if pword not in (command_verbs + command_desc):
                command['iobject'] = pword
        elif pword in command_prep:
            command['iobject'] = word
        elif word in command_tverb:
            command['iobject'] = pword

        pword = word
    
    return command

def irc_public (client, user, channel, message):
    if client.access_list.check(user, 0):
        is_command, line = match_command(message)

        if is_command:
            command = parse_command(line)
           
            # run the sub-command
            mod = sys.modules[__name__]
            cmd_func = 'cmd_{0}'.format(command['verb'])
            if (hasattr(mod, cmd_func)):
                getattr(mod, cmd_func)(client, user, channel, command)

# sub-commands
def cmd_give (client, user, channel, command):
    if command['iobject'] == 'me': command['iobject'], _ = user.split('!')
    client.describe(channel, 'gives {0} a nice warm cup of {1}'.format(command['iobject'], command['dobject']))

def cmd_bullying (client, user, channel,  command):
    client.say(channel, '{0}: I feel offended by your recent action(s). Please read http://stop-irc-bullying.eu/stop'.format(command['iobject']))
