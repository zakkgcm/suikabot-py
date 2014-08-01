#!/usr/bin/env python2

import os
import sys
import imp

import re
import json
import errno

import threading
import pickle

import appdirs
import ssl
import logging

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, ssl
from twisted.internet.endpoints import TCP4ClientEndpoint, SSL4ClientEndpoint, connectProtocol
from Queue import Queue

def ircmask_match (pattern, mask):
    '''Match an irc-style mask against a wildcard pattern.'''
    pattern = re.escape(pattern).replace('\\*', '.+')
    return re.match(pattern, mask) != None

def mkdir(dirname):
    try:
        os.makedirs(dirname)
    except OSError as e:
        if e.errno != errno.EEXIST and not os.path.isdir(e.filename):
            raise

class DataWriter():
    '''Threaded pickle data writing subsystem. Assumes small, infrequent writes'''
    def __init__ (self, data_dir='.'):
        self.data_dir = data_dir
        self.thread = threading.Thread(target=self.run)
        self.queue = Queue()

        self.thread.daemon = True
        self.thread.start()

    def add (self, fname, data):
        '''Queue the given data to be written to a file'''
        self.queue.put((fname, data))

    def get(self, fname):
        '''Get the data from the given file'''
        try:
            with open(os.path.join(self.data_dir, fname), 'rb') as f:
                data = pickle.load(f)
                return data
        except IOError:
            logging.warning("Tried to load nonexistant data file {0}", fname)

        return []

    def run (self):
        while True:
            mkdir(self.data_dir)

            fname, data = self.queue.get()
            with open(os.path.join(self.data_dir, fname), 'wb') as f:
                pickle.dump(data, f) 

class AccessList:
    LEVEL_OWNER = 100
    LEVEL_OP = 10

    def __init__ (self):
        self.access_map = {}

    def add (self, mask, level):
        self.access_map[mask] = level

    def delete (self, mask):
        if mask in self.access_map:
            del self.access_map[mask]

    def check (self, mask, level):
        '''Return if a given mask has at least the specified permissions.'''

        for p, l in self.access_map.viewitems():
            if ircmask_match(p, mask):
                return l >= level

        return True

class SuikaBot(irc.IRCClient):
    '''
        main bot class
        sends ALL events to loaded plugins (as raw_*)
        also sends Twisted's convenience events (as irc_*)
    '''

    def __init__ (self):
        self.plugins = {}
        self.plugin_dir = '.'
        self.access_list = AccessList()
        self.data_writer = DataWriter(appdirs.user_data_dir('suikabot'))
        
    def load_plugins (self):
        plugin_files = os.listdir(self.plugin_dir)
        #suffixes = [x[0] for x in imp.get_suffixes()]
        suffixes = ['.py']

        for plugin_file in plugin_files:
            name, suffix = os.path.splitext(plugin_file)
            if suffix not in suffixes:
                continue
            try:
                mod = imp.load_source('suikabot.plugin.{0}'.format(name), os.path.join(self.plugin_dir, plugin_file))
                self.plugins[name] = mod

                mod.init(self)               
 
                logging.info("Loaded module {0} from {1}".format(name, self.plugin_dir))
            except ImportError as e:
                logging.error("Couldn't load module {0}! {1}".format(plugin_file, e))
            except AttributeError:
                logging.warning("No init defined for module {0}".format(name)) # FIXME: handle just the init error

        print self.plugins

    def reload_plugins (self):
        self.plugins = {}
        self.load_plugins()

    def dispatch_to_plugins (self, handler, *args):
        for plugin in self.plugins.viewvalues():
            # call the handler
            if hasattr(plugin, handler):
                getattr(plugin, handler)(self, *args)

    def handleCommand (self, command, prefix, params):
        handler = 'raw_{0}'.format(command.lower())
        self.dispatch_to_plugins(handler, prefix, params)

        print "{0}: {1} ({2})".format(command, prefix, params)

        irc.IRCClient.handleCommand(self, command, prefix, params)

    # the rest of these are convenience methods inherited from Twisted
    # each is forwarded to plugins
    # some may have internal tracking logic
    # yes this is very silly

    # TODO: implement all of them
    def privmsg (self, *args):
        self.dispatch_to_plugins('irc_public', *args)

    def noticed (self, *args):
        self.dispatch_to_plugins('irc_notice', *args)
  
    def action (self, *args):
        self.dispatch_to_plugins('irc_action', *args)
    
    def modeChanged (self, *args):
        self.dispatch_to_plugins('irc_mode', *args)

    def topicUpdated (self, *args):
        self.dispatch_to_plugins('irc_topic', *args)

    def userRenamed (self, *args):
        self.dispatch_to_plugins('irc_nick', *args)

    def nickChanged (self, *args):
        self.dispatch_to_plugins('irc_nickchange', *args)

    def joined (self, *args):
        self.dispatch_to_plugins('irc_joined', *args)

    def userJoined (self, *args):
        self.dispatch_to_plugins('irc_join', *args)

    def left (self, *args):
        self.dispatch_to_plugins('irc_left', *args)
    
    def userLeft (self, *args):
        self.dispatch_to_plugins('irc_leave', *args)
  
    def kickedFrom (self, *args):
        self.dispatch_to_plugins('irc_kicked', *args)
    
    def userKicked (self, *args):
        self.dispatch_to_plugins('irc_kick', *args)

    def userQuit (self, *args):
        self.dispatch_to_plugins('irc_quit', *args)

def main ():
    # config directories
    config_dir = appdirs.user_config_dir('suikabot')
    access_file = os.path.join(config_dir, 'accesslist.json.conf')

    mkdir(config_dir)

    # set up the client
    servaddr, servport = sys.argv[2].split(':')

    client = SuikaBot()
    client.nickname = sys.argv[1] 
    client.password = sys.argv[3]

    with open(access_file, 'r') as f:
        client.access_list.access_map = json.load(f)

    client.plugin_dir = 'plugins'
    client.load_plugins()

    connectProtocol(SSL4ClientEndpoint(reactor, servaddr, int(servport), ssl.ClientContextFactory()), client)
   
    # main loop
    reactor.run()

    # save access list to file
    with open(access_file, 'w+') as f:
        json.dump(client.access_list.access_map, f)

if __name__ == "__main__":
    main()
