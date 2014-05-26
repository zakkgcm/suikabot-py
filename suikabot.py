#!/usr/bin/env python2

import os
import sys
import imp
import ssl
import logging

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, ssl
from twisted.internet.endpoints import TCP4ClientEndpoint, SSL4ClientEndpoint, connectProtocol

# global plugin list TODO: move this into the bot class
plugins = {}

def load_plugins (plugin_dir):
    plugin_files = os.listdir(plugin_dir)
    suffixes = [x[0] for x in imp.get_suffixes()]

    for plugin_file in plugin_files:
        name, suffix = os.path.splitext(plugin_file)
        if suffix not in suffixes:
            continue

        try:
            mod = imp.load_source('suikabot.plugin.{0}'.format(name), os.path.join(plugin_dir, plugin_file))
            plugins[plugin_file] = mod
        except Exception as e:
            logging.error("Couldn't load module {0}! {1}".format(plugin_file, e))

class SuikaBot(irc.IRCClient):
    '''
        main bot class
        sends ALL events to loaded plugins (as raw_*)
        also sends Twisted's convenience events (as irc_*)
    '''

    def dispatch_to_plugins (self, handler, *args):
        for plugin in plugins.viewvalues():
            # call the handler
            if hasattr(plugin, handler):
                getattr(plugin, handler)(self, *args)

    def handleCommand (self, command, prefix, params):
        handler = 'raw_{0}'.format(command)
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
    load_plugins('plugins')
   
    servaddr, servport = sys.argv[2].split(':')

    client = SuikaBot()
    client.nickname = sys.argv[1] 
    client.password = sys.argv[3]

    connectProtocol(SSL4ClientEndpoint(reactor, servaddr, int(servport), ssl.ClientContextFactory()), client)
    
    reactor.run()

if __name__ == "__main__":
    main()
