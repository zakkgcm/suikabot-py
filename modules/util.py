import os
import re
import sys

import appdirs
import errno
import yaml
import logging

logger = logging.getLogger("suikabot")
logger.setLevel(logging.INFO)

shandle = logging.StreamHandler(sys.stdout)
logger.addHandler(shandle)
 
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

def ircmask_split (hostmask):
    nick, userhost = hostmask.split('!', 1)
    user, host = userhost.split('@', 1)

    return (nick, user, host)

class Config:
    def __init__ (self, config_dir):
        self.config_dir = appdirs.user_config_dir(config_dir)
        mkdir(config_dir)

    def format_config_name (self, config):
        return os.path.join(self.config_dir, '{0}.conf'.format(config))
        

    def load (self, config):
        fname = self.format_config_name(config)
    
        try:
            with open(fname, 'r') as f:
                return yaml.load(f)
        except IOError as e:
            logger.error("Couldn't read config file {0}! {1}".format(fname, e))
        
        return {}

    def save (self, config, data):
        fname = self.format_config_name(config)
    
        try:
            with open(fname, 'w+') as f:
                return yaml.dump(data, f)
        except IOError as e:
            logger.error("Couldn't write config file {0}! {1}".format(fname, e))
