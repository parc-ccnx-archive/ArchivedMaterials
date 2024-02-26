#!/usr/bin/python

# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-

# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
# Copyright 2015 Palo Alto Research Center, Inc. (PARC), a Xerox company.  All Rights Reserved.
# The content of this file, whole or in part, is subject to licensing terms.
# If distributing this software, include this License Header Notice in each
# file and provide the accompanying LICENSE file.

# @copyright 2015 Palo Alto Research Center, Inc. (PARC), A Xerox Company. All Rights Reserved.

import sys
import os, time, tempfile, json, getopt
from CCNx import *

def usage(argv):
    print "Usage: %s [-hd] [-l | --lci] lci:/collector/prefix [-n count] value" % argv[0]
    print "\t-h = help"
    print "\t-d = enable debug mode"
    print "\t-n = number of times to send"

def parse_args(argv):
    namePrefix = None
    count = None
    try:
        opts, args = getopt.getopt(argv[1:], "l:hn:d", ["lci=", "help"])
    except getopt.GetoptError:
        usage(argv)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(argv)
            sys.exit()
        elif opt == '-n':
            count = arg
        elif opt == '-d':
            global _debug
            _debug = 1
        elif opt in ("-l", "--lci"):
            namePrefix = arg

    return (namePrefix, count, " ".join(args))

def setup_identity():
    global IDENTITY_FILE
    IDENTITY_FILE = tempfile.NamedTemporaryFile(suffix=".p12")
    identity = create_pkcs12_keystore(IDENTITY_FILE.name, "foobar", "bletch", 1024, 10)
    return identity

def open_portal():
    identity = setup_identity()
    factory = PortalFactory(identity)
    portal = factory.create_portal()
    return portal

if __name__ == "__main__":
    namePrefix, count, value = parse_args(sys.argv)

    if not namePrefix or not value:
        usage(sys.argv)
        sys.exit(2)

    if not count:
        count = 1 
        
    
    portal = open_portal()

    for i in range(int(count)):
        try:
            # 1. Construct and interest wiht the name "namePrefix" and payload <value>
            #@REMOVE
            interest = Interest(Name(namePrefix))
            interest.setPayload(value)

            # 2. Send the interest using the Portal
            #@REMOVE
            portal.send(interest)

            # 3. Receive a response from the Portal
            #@Remove
            message = portal.receive()

            # 4. Determine what type of message was received, and act appropriately
            #@REMOVE
            if isinstance(message, Interest):
                print "Received Interest: ", str(message)
            elif isinstance(message, Control):
                print "Received control message: ", str(message)
            elif isinstance(message, ContentObject):
                print "Received content message: ", str(message)
            elif isinstance(message, InterestReturn):
                print "Received InterestReturn message: ", str(message)

            # 5. Display the payload of the message, if one exists
            #@REMOVE
            payload = message.getPayload()
            if payload:
                print "Data: ", payload

        except Portal.CommunicationsError as x:
            sys.stderr.write("%s: comm error: %s\n" % (sys.argv[0], x.errno,))

        time.sleep(1)
