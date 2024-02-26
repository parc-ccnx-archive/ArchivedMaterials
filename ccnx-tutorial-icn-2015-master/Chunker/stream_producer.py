# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-

# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
# Copyright 2014-2015 Palo Alto Research Center, Inc. (PARC), a Xerox company.  All Rights Reserved.
# The content of this file, whole or in part, is subject to licensing terms.
# If distributing this software, include this License Header Notice in each
# file and provide the accompanying LICENSE file.

# @author Bill Janssen, Alan Walendowski, System Sciences Laboratory, PARC
# @copyright 2014-2015 Palo Alto Research Center, Inc. (PARC), A Xerox Company. All Rights Reserved.

import sys, os, time, getopt

from CCNx import *

def usage(argv):
    print "Usage: %s [-h ] [-l | --lci] lci:/name/to/provide [-n numChunks] [-s chunkSize]" % argv[0]
    print "  e.g. ./%s -l lci:/very/large/file -n 100 -s 1200 " % argv[0]

def parse_args(argv):
    name = None
    chunkSize = None
    numChunks = None
    try:
        opts, args = getopt.getopt(argv[1:], "l:hds:n:", ["lci=", "help"])
    except getopt.GetoptError:
        usage(argv)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(argv)
            sys.exit()
        elif opt == '-n':
            numChunks = arg
        elif opt == '-s':
            chunkSize = arg
        elif opt == '-d':
            global _debug
            _debug = 1
        elif opt in ("-l", "--lci"):
            name = arg

    return (name, numChunks, chunkSize, " ".join(args))


def setup_identity():
    filename = "/tmp/ccnx_stream_producer_" + str(os.getpid())
    if os.path.exists(filename):
        os.unlink(filename)
    identity = create_pkcs12_keystore(filename, "producer_password", "producer", 1024, 30)
    return identity


def provide_chunked_thing(nameToProvide, numChunks, chunkSize):
    print ("Will provide %d chunks of roughly %d bytes each, for name %s" %
            (numChunks, chunkSize, nameToProvide))

    factory = PortalFactory(setup_identity())

    # Create a portal for receiving chunk requests. We'll receive and handle one at a time.
    portal = factory.create_portal(attributes=PortalAttributes_Blocking)

    name = Name(nameToProvide)
    portal.listen(name)
    print(str(portal) + "is listening for" + str(name))

    while True:
        request = portal.receive()

        if request is None:
            break

        if isinstance(request, Interest):
            print("producer: Interest in %s received" % (str(request),))

            if request.name.startswith(name):

                chunkNumberRequested = Name(request.getName())[-1].value

                payload = ("%05d " % (chunkNumberRequested,)) * int(chunkSize / 6)

                try:
                    # Reply with a ContentObject containitn the specified chunk number.
                    # Since the chunk number is in the name, we can just reply with the
                    # same name. We do update the end_chunk_number every time, though.
                    response = ContentObject(request.name, payload, end_chunk_number=(numChunks-1))
                    portal.send(response)

                except Portal.CommunicationsError as x:
                    sys.stderr.write("ccnxPortal_Write failed: %s\n" % (x,))

if __name__ == "__main__":
    fail_fast()

    nameToProvide, numChunks, chunkSize, otherArgs = parse_args(sys.argv)
    if not nameToProvide:
        usage(sys.argv)
        sys.exit(2)

    if not numChunks:
        numChunks = 10

    if not chunkSize:
        chunkSize = 512

    provide_chunked_thing(nameToProvide, int(numChunks), int(chunkSize))
