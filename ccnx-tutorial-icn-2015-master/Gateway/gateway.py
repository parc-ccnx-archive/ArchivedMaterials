#!/usr/bin/python

# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-

# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
# Copyright 2015 Palo Alto Research Center, Inc. (PARC), a Xerox company.  All Rights Reserved.
# The content of this file, whole or in part, is subject to licensing terms.
# If distributing this software, include this License Header Notice in each
# file and provide the accompanying LICENSE file.

# @author Christopher A. Wood, System Sciences Laboratory, PARC
# @copyright 2015 Palo Alto Research Center, Inc. (PARC), A Xerox Company. All Rights Reserved.

import sys, urllib2, getopt
sys.path.append("../")
from CCNxClient import *

def usage(argv):
    print "Usage: %s [-h] lci:/gateway/prefix" % argv[0]

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
        elif opt == '-d':
            global _debug
            _debug = 1

    return " ".join(args)

class HTTPGateway(object):
    def __init__(self, prefix):
        self.client = CCNxClient()
        self.prefix = prefix
        if len(prefix) == 0:
            self.prefix = "lci:/gateway"

    def build_schema(self):
        schema = "query = lci:/gateway/<authority>/[path]"
        schema = schema + "authority = domain name | IpAddr:port"
        schema = schema + "path = URI"
        return schema

    def run(self):
        client = CCNxClient()

        listening = client.listen(self.prefix)
        print "Lisening on %s" % (self.prefix)

        while listening:
            name, data = client.receive_raw()

            #@REMOVE
            schemaName = self.prefix + "/schema"
            if schemaName in str(name):
                client.reply(str(name), self.build_schema)
            else:
                url = "http://" + str(name[1].value)
                path = "/".join(map(lambda ns : str(ns.value), name[2:]))
                if len(path) > 0:
                    url = url + "/" + path

                print "Fetching %s" % (url)
                content = urllib2.urlopen(url).read()

                client.reply(str(name), content)

def main(argv):
    fail_fast()
    args = parse_args(argv)
    gateway = HTTPGateway(args)
    gateway.run()

if __name__ == "__main__":
    main(sys.argv)
