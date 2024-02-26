#!/usr/bin/python

#shamelessly stolen from the sample code in the python directory

import sys, tempfile, time, json, random, urllib2

from CCNx import *

DEVICE_ID = "sender 001"

def setup_identity():
    global IDENTITY_FILE
    IDENTITY_FILE = tempfile.NamedTemporaryFile(suffix=".p12")
    identity = create_pkcs12_keystore(IDENTITY_FILE.name, "foobar", "bletch", 1024, 10)
    return identity

def openPortal():
    identity = setup_identity()
    factory = PortalFactory(identity)
    portal = factory.create_portal()
    return portal

def main():

    fail_fast()

    try:
        portal = openPortal()

        uris = ["lci:/local/forwarder/ContentStore/stat/size",
                "lci:/local/forwarder/ContentStore/stat/hits",
                "lci:/local/forwarder/PIT/stat/size",
                "lci:/local/forwarder/PIT/stat/avgEntryLifetime",
                "lci:/local/forwarder/Control/stats",
              #  "lci:/local/forwarder/FIB/list"
               ];

        while True:
            try:
                for uri in uris:
                    print "Sending: ", uri
                    interest = Interest(Name(uri))
                    portal.send(interest)

                    # We assume there'll be an ACK here.
                    response = portal.receive()
                    if response and isinstance(response, ContentObject):
                        queryResponse = json.loads(response.payload.value)
                        wrapper = {}
                        wrapper["query"] = uri
                        wrapper["response"] = queryResponse

                        print "   Response:"
                        jsonString = json.dumps(wrapper, sort_keys=True, indent=4, separators=(',', ': '))
                        print jsonString
                        print "\n"

                        # Send the data to the server...
                        #req = urllib2.Request('http://localhost:5000/data')
                        #req.add_header('Content-Type', 'application/json')
                        #response = urllib2.urlopen(req, jsonString)

                        #print response
            except:
                pass
            time.sleep(1)

    except Portal.CommunicationsError as x:
        sys.stderr.write("sender: comm error attempting to listen: %s\n" % (x.errno,))

if __name__ == "__main__":
    main()
