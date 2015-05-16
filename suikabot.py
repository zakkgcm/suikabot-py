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

from modules import util

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.internet.ssl import ClientContextFactory as SSLClientContextFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.endpoints import TCP4ClientEndpoint, SSL4ClientEndpoint, connectProtocol
from Queue import Queue

class DataWriter:
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
            util.logger.warning("Tried to load nonexistant data file {0}", fname)

        return []

    def run (self):
        while True:
            util.mkdir(self.data_dir)

            fname, data = self.queue.get()
            with open(os.path.join(self.data_dir, fname), 'wb') as f:
                pickle.dump(data, f) 

class AliasMap:
    def __init__ (self):
        self.aliases = []

    def find_alias_indices (self, alias_in, alias):
        in_idx = None
        needle_idx = None

        for idx, group in enumerate(self.aliases):
            if alias_in.lower() in group:
                in_idx = idx
            if alias.lower() in group:
                needle_idx = idx

            # got what we came here for
            if in_idx != None and needle_idx != None:
                return (in_idx, needle_idx)

        return (in_idx, needle_idx)
    
    def is_alias_of (self, alias_in, alias):
        in_idx, needle_idx = self.find_alias_indices(alias_in, alias)
        return in_idx != None and needle_idx != None and in_idx == needle_idx

    def get_aliases (self, alias):
        in_idx, needle_idx = self.find_alias_indices('', alias)
        if needle_idx != None:
            return self.aliases[needle_idx]

        return [alias]

    def add (self, alias_in, alias):
        if alias_in.strip() == '' or alias.strip() == '':
	        return False

        in_idx, needle_idx = self.find_alias_indices(alias_in, alias)
        
        # new alias already exists
        if needle_idx != None:
            return False

        # the parent alias isn't there, make a new group
        if in_idx == None:
            self.aliases.append([alias_in.lower()])
            in_idx = len(self.aliases) - 1

        self.aliases[in_idx].append(alias.lower())
        return True

    def remove (self, alias):
        # can optimize this by just calling remove() on every group
        in_idx, needle_idx = self.find_alias_indices('', alias)
        if needle_idx != None:
            self.aliases[needle_idx].remove(alias)
            return True

        return False

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
            if util.ircmask_match(p, mask):
                return l >= level

        return False

# FIXME: wtf is this shit
class Scheduler:
    def schedule (self, delay, callback, *args):
        reactor.callLater(delay, callback, *args)

class PluginLoader:
    def __init__ (self, plugin_dir='.'):
        self.plugins = {}
        self.plugin_dir = plugin_dir
        self.data_writer = None
        self.services = {}

    def load (self):
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

                mod.data_writer = self.data_writer # FIXME: magic global variable is ugly
                mod.services = self.services
                mod.init()
 
                util.logger.info("Loaded module {0} from {1}".format(name, self.plugin_dir))
            except ImportError as e:
                util.logger.error("Couldn't load module {0}! {1}".format(plugin_file, e))
            except AttributeError:
                util.logger.warning("No init defined for module {0}".format(name)) # FIXME: handle just the init error

    def reload (self):
        self.plugins = {}
        self.load()

    def get (self):
        return self.plugins

class SuikaClient(irc.IRCClient):
    '''
        main bot class
        sends ALL events to loaded plugins (as raw_*)
        also sends Twisted's convenience events (as irc_*)
    '''

    def __init__ (self, server):
        self.server = server
        self.access_list = None
        self.alias_map = None
        self.plugins = None

        self.lineRate = 1

    def dispatch_to_plugins (self, handler, *args):
        for plugin in self.plugins.get().viewvalues():
            # call the handler
            if hasattr(plugin, handler):
                getattr(plugin, handler)(self, *args)

    def handleCommand (self, command, prefix, params):
        handler = 'raw_{0}'.format(command.lower())
        self.dispatch_to_plugins(handler, prefix, params)

        util.logger.debug("{0}: {1} ({2})".format(command, prefix, params))

        irc.IRCClient.handleCommand(self, command, prefix, params)

    def schedule (self, delay, callback, *args):
        reactor.callLater(delay, callback, *args)

    def connectionMade(self):
        util.logger.info("Connected to server {0}.".format(self.server))

        self.services['clients'][self.server] = self
        self.dispatch_to_plugins("client_connected")

        irc.IRCClient.connectionMade(self)

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

class SuikaClientFactory(ReconnectingClientFactory):
    def set_info(self, server, nickname='dumb_bot', username='', realname='', server_password=''):
        self.server = server
        self.userinfo = (nickname, username, realname)
        self.server_password = server_password

    def buildProtocol (self, addr):
        client = SuikaClient(self.server)
        client.nickname = self.userinfo[0]
        client.username = self.userinfo[1]
        client.realname = self.userinfo[2]
        client.password = self.server_password

        # FIXME: refactor this as a "service" kind of design
        client.access_list = self.access_list
        client.alias_map = self.alias_map
        client.plugins = self.plugins

        client.services = self.services

        # required(?) by the api
        client.factory = self
        
        return client

    def clientConnectionLost (self, connector, reason):
        util.logger.warning("Lost connection.  ({0})".format(reason.getErrorMessage()))
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed (self, connector, reason):
        util.logger.warning("Connection failed.  ({0})".format(reason.getErrorMessage()))
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

def connect_client (server, address, port=6667, password=None, nickname='', username=None, realname=None, ssl=False, **kwargs):
    ''' Constructs and returns factory instance for a server after connecting it. '''
    factory = SuikaClientFactory()
    factory.set_info(server, nickname, username, realname, password)

    if ssl:
        reactor.connectSSL(address, port, factory, SSLClientContextFactory())
    else:
        reactor.connectTCP(address, port, factory)

    return factory

def main ():
    # client list (actually clientfactories)
    clients = {}

    # configuration files
    configuration = util.Config('suikabot')
    userinfo = configuration.load('userinfo')
    serverlist = configuration.load('servers')

    # services
    access_list = AccessList()
    access_list.access_map = configuration.load('accesslist')

    data_writer = DataWriter(appdirs.user_data_dir('suikabot'))

    alias_map = AliasMap()
    alias_map.aliases = data_writer.get('aliases.db')

    services = {}
    services['clients'] = {}
    services['scheduler'] = Scheduler()

    plugins = PluginLoader('plugins')
    plugins.data_writer = data_writer
    plugins.services = services
    plugins.load()

    # connection logic
    for server, opts in serverlist.viewitems():
        # clump the options together and let connect unpack w/ defaults
        opts.update(userinfo)
        factory = connect_client(server, **opts)

        # dependency inject
        factory.access_list = access_list
        factory.alias_map = alias_map
        factory.plugins = plugins
        factory.services = services

        clients[server] = factory

    # cleanup callback
    def shutdown ():
        util.logger.info("Shutting down...")
        
        # save config files
        configuration.save('accesslist', access_list.access_map)
        data_writer.add('aliases.db', alias_map.aliases)
        
    reactor.addSystemEventTrigger('before', 'shutdown', shutdown)

    # main loop
    reactor.run()

if __name__ == "__main__":
    main()
