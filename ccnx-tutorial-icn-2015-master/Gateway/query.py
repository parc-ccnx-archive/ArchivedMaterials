#!/usr/bin/python

# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-

# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
# Copyright 2015 Palo Alto Research Center, Inc. (PARC), a Xerox company.  All Rights Reserved.
# The content of this file, whole or in part, is subject to licensing terms.
# If distributing this software, include this License Header Notice in each
# file and provide the accompanying LICENSE file.

# @author Christopher A. Wood, System Sciences Laboratory, PARC
# @copyright 2015 Palo Alto Research Center, Inc. (PARC), A Xerox Company. All Rights Reserved.

import sys, getopt
sys.path.append("../")
from CCNxClient import *

def usage(argv):
    print "Usage: %s [-h] lci:/query/1 lci:/query/2 ... " % argv[0]

def parse_args(argv):
    namePrefix = None
    try:
        opts, args = getopt.getopt(argv[1:], "l:h", ["help"])
    except getopt.GetoptError:
        usage(argv)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(argv)
            sys.exit()

    return args

def main(uris):
    fail_fast()
    client = CCNxClient()
    for uri in uris:
        data = client.get(uri, "")
        print data

if __name__ == "__main__":
    uris = parse_args(sys.argv)
    main(uris)
