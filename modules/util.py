import os
import re

import appdirs
import errno
import json
import logging

def mkdir(dirname):
    try:
        os.makedirs(dirname)
    except OSError as e:
        if e.errno != errno.EEXIST and not os.path.isdir(e.filename):
            raise

def ircmask_match (pattern, mask):
    '''Match an irc-style mask against a wildcard pattern.'''
    pattern = re.escape(pattern).replace('\\*', '.+')
    return re.match(pattern, mask) != None

def split_user (hostmask):
    nick, userhost = hostmask.split('!', 1)
    user, host = userhost.split('@', 1)

    return (nick, user, host)

class Config:
    def __init__ (self, config_dir):
        self.config_dir = appdirs.user_config_dir(config_dir)
        mkdir(config_dir)

    def format_config_name (self, config):
        return os.path.join(self.config_dir, '{0}.json.conf'.format(config))
        

    def load (self, config):
        fname = self.format_config_name(config)
    
        try:
            with open(fname, 'r') as f:
                return json.load(f)
        except IOError as e:
            logging.error("Couldn't read config file {0}! {1}".format(fname, e))
        
        return {}

    def save (self, config, data):
        fname = self.format_config_name(config)
    
        try:
            with open(fname, 'w+') as f:
                return json.dump(data, f)
        except IOError as e:
            logging.error("Couldn't write config file {0}! {1}".format(fname, e))
