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
    print "Usage: %s [-h ] [[-l | --lci] lci:/name/to/request]" % argv[0]
    print "  e.g. ./%s -l lci:/very/large/file" % argv[0]

def parse_args(argv):
    namePrefix = None
    try:
        opts, args = getopt.getopt(argv[1:], "l:hd", ["lci=", "help"])
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
        elif opt in ("-l", "--lci"):
            namePrefix = arg

    return (namePrefix, " ".join(args)) # listenPrefix, Everything left over


def setup_identity():
    filename = "/tmp/ccnx_stream_consumer_" + str(os.getpid())
    if os.path.exists(filename):
        os.unlink(filename)
    identity = create_pkcs12_keystore(filename, "consumer_password", "consumer", 1024, 30)
    return identity

def retrieve_chunked_thing(contentName):
    factory = PortalFactory(setup_identity())

    # Create a portal with the chunking flow controller enabled.
    portal = factory.create_portal(transport=TransportType_RTA_Chunked)
    assert portal is not None, "Expected a non-null Portal pointer."

    interest = Interest(Name(contentName))

    portal.send(interest)
    for response in portal:
        print('consumer:  %s' % (response,))
        if (isinstance(response, Control) and
            (response.value.get("notifyStatus") or {}).get("statusCode") == Control.FLOW_CONTROL_FINISHED):
            break

        # Could also check if the chunk number of the incoming ContentObject is equal to the end_chunk_nunber
        # in the ContentObjct. If so, we're done transferring. This is what the flow controller does.
    
        if isinstance(response, ContentObject):
            chunkNumberSegment = Name(response.getName())[-1]  # this object's chunk number
            endChunkNumber = response.getEndChunkNumber()  # what the producer thinks will be the final chunk number
            print "Received chunk %d of %d" % (chunkNumberSegment.value, endChunkNumber) 
            print response.getPayload()
    

    print('consumer: exiting')

if __name__ == "__main__":
    fail_fast()

    nameToRequest, otherArgs = parse_args(sys.argv)
    if not nameToRequest:
        usage(sys.argv)
        sys.exit(2)

    retrieve_chunked_thing(nameToRequest)
