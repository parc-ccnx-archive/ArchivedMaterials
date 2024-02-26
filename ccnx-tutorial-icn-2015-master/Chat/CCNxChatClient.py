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

A collection of helper functions for the simple chat_client.py example.

"""

import tempfile
import time
import thread
import json
from sortedcontainers import SortedList

from CCNx import *

class CCNxChatClient(object):
    def __init__(self, lciPrefix, userName):
        self.MAX_MESSAGES_TO_BUFFER = 50

        self.identity = self.setup_identity()
        factory = PortalFactory(self.identity)
        self.portal = factory.create_portal()

        self.messages = SortedList()

        self.lciPrefix = lciPrefix  # includes room name
        self.userName = userName

        # Get the latest message from the chat server
        thread.start_new_thread(self.background_receiver, ("BGReceiver",))
        self.send_seq_request()

        self.callbackIncoming = None

    def set_callback_for_incoming_messages(self, callback):
        self.callbackIncoming = callback

    def setup_identity(self):
        global IDENTITY_FILE
        IDENTITY_FILE = tempfile.NamedTemporaryFile(suffix=".p12")
        identity = create_pkcs12_keystore(IDENTITY_FILE.name, "foobar", "bletch", 1024, 10)
        return identity

    def open_portal(self):
        identity = setup_identity()
        factory = PortalFactory(identity)
        portal = factory.create_portal()
        return portal

    def get_last_seen_seq(self):
        try:
            (lastSeenSeq, timestamp, userName, text) = self.messages[-1]
            return lastSeenSeq
        except:
            return 0


    def _find_message(self, sortedList, seq):
        """ Binary search for the sorted list we keep the messages in """
        if len(sortedList) == 0:
            return False
        else:
            midpoint = len(sortedList) // 2
            if sortedList[midpoint][0] == seq:
                return True
            else:
                if seq < sortedList[midpoint][0]:
                    return self._find_message(sortedList[:midpoint], seq)
                else:
                    return self._find_message(sortedList[midpoint+1:], seq)


    def is_seq_in_messages(self, seq):
        return self._find_message(self.messages, seq)

    def background_receiver(self, threadName):
        keepRunning = True
        while keepRunning:
            message = self.portal.receive()
            if isinstance(message, ContentObject):
                nameComponents = str(message.name).replace(self.lciPrefix, "").split('/')
                del nameComponents[0] # Remove the ''

                j = json.loads(message.getPayload())
                if j['status'] == 0:

                    if nameComponents[0] == 'seq':
                        seq = j['seq']
                        ## This is a sequence request response
                        if seq > self.get_last_seen_seq():
                            self.request_missing_texts(seq)

                    elif nameComponents[0] == 'who':
                        timestamp = j['timestamp']
                        members = j['members'] 
                        s = "Users in room: "
                        for member in members:
                            s += member + ", "
                        if s[-2:] == ", ":
                            s = s[:-2]
                        userName = "ChatServer"
                        self.messages.add((seq, timestamp, userName, s))

                        if self.callbackIncoming:
                            self.callbackIncoming(seq, timestamp, userName, s)

                    elif nameComponents[0] == 'text':
                        # This could be an ACK for a submitted text, or it could be
                        # a text utterance. If it has a sequence number after /text,
                        # then it's a new utterance.
                        if len(nameComponents) == 1:
                            seq = j['seq']
                            if seq > self.get_last_seen_seq():
                                self.request_missing_texts(seq)

                        elif nameComponents[1].isdigit():
                            # this is a text utterance
                            seq = j['seq']
                            timestamp = j['timestamp']
                            userName = j['userName']
                            text = j['text']

                            # Don't add duplicates
                            if not self.is_seq_in_messages(seq):
                                self.messages.add((seq, timestamp, userName, text))

                            # Remove the oldest messages, if necessary
                            if len(self.messages) > self.MAX_MESSAGES_TO_BUFFER:
                                del self.messages[0]

                            if self.callbackIncoming:
                                self.callbackIncoming(seq, timestamp, userName, text)


    def sync_in_background(self, threadName, periodInSeconds):
        while self.bgSyncKeepRunning == True:
            self.send_seq_request()
            time.sleep(periodInSeconds)

    def enable_periodic_sync(self, numSeconds):
        self.bgSyncKeepRunning = True
        thread.start_new_thread(self.sync_in_background, ("BGSync", numSeconds))

    def send_seq_request(self):
        # This will not work if cacheing is enabled on the forwarder (via the ContentStore)
        interest = Interest(Name("%s/seq" % (self.lciPrefix)))
        m = {'user': self.userName}
        interest.setPayload(json.dumps(m))
        self.portal.send(interest)

    def send_who_request(self):
        # This will not work if cacheing is enabled on the forwarder (via the ContentStore)
        interest = Interest(Name("%s/who" % (self.lciPrefix)))
        m = {'user': self.userName}
        interest.setPayload(json.dumps(m))
        self.portal.send(interest)

    #@Remove
    def request_missing_texts(self, seq):
        lastSeen = self.get_last_seen_seq()
        startSeq = lastSeen
        seq += 1
        if seq - lastSeen > self.MAX_MESSAGES_TO_BUFFER:
           startSeq = seq - self.MAX_MESSAGES_TO_BUFFER

        for missingSeq in xrange(startSeq, seq):
            interest = Interest(Name("%s/text/%d" % (self.lciPrefix, missingSeq)))
            self.portal.send(interest)

    def send_text_message(self, text):
        interest = Interest(Name("%s/text" % (self.lciPrefix)))
        m = {'user': self.userName, 'text': text}
        #@REMOVE (need to call AndId() to work with content store)
        #interest.setPayloadAndId(json.dumps(m)) 
        interest.setPayload(json.dumps(m))
        self.portal.send(interest)

    def get_messages(self):
        return self.messages

def on_incoming(seq, timestamp, userName, text):
    print "Notified that incoming messages have been updated"

if __name__ == "__main__":
    ccnx = CCNxChatClient("lci:/ccnx/game/chat/room", "walendo")
    ccnx.set_callback_for_incoming_messages(on_incoming)

    ccnx.enable_periodic_sync(5)
    n = 0
    while n < 3:
        ccnx.send_text_message("hey: %d" % n)
        n += 1
        time.sleep(1)
        for seq, ts, userName, text in ccnx.get_messages():
            print seq, ts, userName, text
