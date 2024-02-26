#!/usr/bin/python

# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-

# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
# Copyright 2015 Palo Alto Research Center, Inc. (PARC), a Xerox company.  All Rights Reserved.
# The content of this file, whole or in part, is subject to licensing terms.
# If distributing this software, include this License Header Notice in each
# file and provide the accompanying LICENSE file.

# @author Alan Walendowski, System Sciences Laboratory, PARC
# @copyright 2015 Palo Alto Research Center, Inc. (PARC), A Xerox Company. All Rights Reserved.

"""
    A very simple chat client using CCNx Interests and ContentObjects to send
    and receive chat messages. Please see the README for info on the names
    used and some example payloads.
"""

import npyscreen
import sys, tempfile, time, json, random, getopt, re
from sortedcontainers import SortedList

from CCNx import *
from CCNxChatClient import CCNxChatClient

class ActionControllerChat(object):
    def __init__(self, parent=None):
        try:
            self.parent = weakref.proxy(parent)
        except:
            self.parent = parent
        self._action_list = []
        self.create()

    def create(self):
        pass

    def add_action(self, ident, function, live):
        ident = re.compile(ident)
        self._action_list.append({'identifier': ident,
                                  'function': function,
                                  'live': live
                                  })

    def process_command_live(self, command_line, control_widget_proxy):
        for a in self._action_list:
            if a['live'] and a['identifier'].match(command_line) ==True:
                a['function'](command_line, control_widget_proxy, live=True)

    def process_command_complete(self, command_line, control_widget_proxy):
        for a in self._action_list:
            if a['identifier'].match(command_line):
                a['function'](command_line, control_widget_proxy, live=False)

class ChatForm(npyscreen.FormMuttActiveTraditional):
    ACTION_CONTROLLER = ActionControllerChat
    MAIN_WIDGET_CLASS = npyscreen.BufferPager
    COMMAND_WIDGET_CLASS = npyscreen.TextCommandBox

    def __init__(self, ccnx, userName, lciPrefix):
        super(ChatForm, self).__init__(self)
        self.userName = userName
        self.lciPrefix = lciPrefix
        self.ccnxChatClient = ccnx
        self.ccnxChatClient.set_callback_for_incoming_messages(self.on_text_received)

        self.wStatus1.value = "CCNx 1.0 Chat: [%s @ %s]  " % (self.userName, self.lciPrefix)

    def on_text_received(self, seq, timestamp, userName, text):
        # Called when incoming texts have been updated
        # We are called with the latest on received - but they COULD come out
        # of order. The self.ccnxChatClient has a sorted list that is in the
        # correct order, so use that to update the screen.
        msgs = self.ccnxChatClient.get_messages()
        self.wMain.values.clear()
        for (seq, timestamp, userName, text) in msgs:
            self.wMain.values.append("%s: %s" % (userName, text))
        # TODO: could use the last 50 or whatever
        self.wMain.display()


    def create(self, *args, **kwargs):
        super(ChatForm, self).create(*args, **kwargs)
        self.wStatus1.value = "CCNx 1.0 Chat"
        self.wStatus2.value = "Enter text to send:"
        self.wMain.editable  = False
        self.wMain.autowrap = True
        self.wMain.maxlen = 10

        # Add entered command/text handlers
        self.action_controller.add_action("", self.on_text_entered, False)

    def on_text_entered(self, v1, widget, live=None):
        text = widget.value

        # One could add some slash commands here... Like /quit.
        if text == "/sync":
            self.ccnxChatClient.send_seq_request()
        elif text == "/who":
            self.ccnxChatClient.send_who_request()
        else:
            self.wCommand.clear()
            self.wCommand.display()

            # Send the text to the server
            self.ccnxChatClient.send_text_message(text)

    def appendDisplayedText(self, timestamp, userName, text):
        self.wMain.values.append("%s: %s" % (userName, text))
        self.wMain.display()

class ChatApp(npyscreen.NPSApp):
    def __init__(self, lciPrefix, userName):
        super(npyscreen.NPSApp, self).__init__()
        self.ccnxChatClient = CCNxChatClient(lciPrefix, userName)
        self.userName = userName
        self.lciPrefix = lciPrefix

    def main(self):
        self.ccnxChatClient = CCNxChatClient(lciPrefix, userName)
        self.lastSeqNumSeen = 0
        self.chatForm = ChatForm(self.ccnxChatClient, self.userName, "%s" % (self.lciPrefix))

        self.ccnxChatClient.enable_periodic_sync(2)
        self.chatForm.edit()

def usage(argv):
    print "Usage: %s [-h ] [-l | -lci] lci:/name/of/chat/room -u userName" % argv[0]
    print "  e.g. ./%s -l lci:/ccnx/game/chat/gossip -u MrFizzy" % argv[0]

def parse_args(argv):
    lciPrefix = None
    userName = None
    try:
        opts, args = getopt.getopt(argv[1:], "l:u:hd", ["lci=", "help"])
    except getopt.GetoptError:
        usage(argv)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(argv)
            sys.exit()
        elif opt == '-d':
            global _debug
            _debug = 1
        elif opt == '-u':
            userName = arg
        elif opt in ("-l", "--lci"):
            lciPrefix = arg
            print "Will chat with [ %s ]" % lciPrefix

    return (userName, lciPrefix)

if __name__ == "__main__":

    userName, lciPrefix = parse_args(sys.argv)
    if not lciPrefix or not userName:
        usage(sys.argv)
        sys.exit(2)

    App = ChatApp(lciPrefix, userName)
    App.run()
