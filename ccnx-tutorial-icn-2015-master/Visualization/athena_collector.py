#!/usr/bin/python

from CCNx import *

import npyscreen
import thread
import sys, time, tempfile
import json

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

def update_cs_stats(form, responsePayload):
    #print responsePayload
    for k in responsePayload:
        if k == u'numEntries':
            form.csNumEntries.value = str(responsePayload[k])
        elif k == u'sizeInBytes':
            sizeInMb = float(responsePayload[k]) / (1024.0*1024.0)
            form.csSize.value = "%f" % sizeInMb
        elif k == u'numAdds':
            form.csAdds.value = str(responsePayload[k])
        elif k == u'numHits':
            form.csHits.value = str(responsePayload[k])
        elif k == u'numMisses':
            form.csMisses.value = str(responsePayload[k])
    form.display() 

def update_pit_stats(form, responsePayload):
    for k in responsePayload:
        if k == u'avgEntryLifetime':
            form.pAvgLifetime.value = str(responsePayload[k]) + " (ms)"
        elif k == u'numEntries':
            form.pNumEntries.value = str(responsePayload[k])
        elif k == u'numPendingEntries':
            form.pNumPending.value = str(responsePayload[k])
    form.display() 

def update_athena_stats(form, responsePayload):
    #print responsePayload
    for k in responsePayload:
        if k == u'numProcessedContentObjects':
            form.fNumCOs.value = str(responsePayload[k])
        elif k == u'numProcessedInterests':
            form.fNumInterests.value = str(responsePayload[k])
        elif k == u'numProcessedInterestReturns':
            form.fNumInterestReturns.value = str(responsePayload[k])
        elif k == u'numProcessedControlMessages':
            form.fNumControl.value = str(responsePayload[k])
    form.display() 

def poll_athena_for_stats(threadName, app, numSecondsToSleep):

    uris = [
            ("lci:/local/forwarder/Control/stats", update_athena_stats),
            ("lci:/local/forwarder/ContentStore/stat/size", update_cs_stats),
            ("lci:/local/forwarder/ContentStore/stat/hits", update_cs_stats),
            ("lci:/local/forwarder/PIT/stat/size", update_pit_stats),
            ("lci:/local/forwarder/PIT/stat/avgEntryLifetime", update_pit_stats),
            #"lci:/local/forwarder/FIB/list"
            ];

    portal = open_portal()

    while True:
        #try:
        if True:
            for uri, updater in uris:
                interest = Interest(Name(uri))
                portal.send(interest)

                # We assume there'll be an ACK here.
                response = portal.receive()
                if response and isinstance(response, ContentObject):
                    #print "PAYLOAD: ", response.payload.value
                    queryResponse = json.loads(response.payload.value)

                    if updater:
                        form = app.getForm("MAIN")
                        if form:
                            updater(form, queryResponse)

                    wrapper = {}
                    wrapper["query"] = uri
                    wrapper["response"] = queryResponse

                    # CHRIS! Re-enable this to update your server.
                    #print "   Response:"
                    #jsonString = json.dumps(wrapper, sort_keys=True, indent=4, separators=(',', ': '))
                    #print jsonString
                    #print "\n"

                    #statsForm.csSize.value = jsonString

                    # Send the data to the server...
                    #req = urllib2.Request('http://localhost:5000/data')
                    #req.add_header('Content-Type', 'application/json')
                    #response = urllib2.urlopen(req, jsonString)

                    #print response
        #except:
        #    pass
        time.sleep(numSecondsToSleep)


class CollectorApp(npyscreen.NPSAppManaged):
    #def __init__(self):
    #    super(npyscreen.NPSAppManaged, self).__init__()
    #    self.statsForm = None

    def onStart(self):
        self.statsForm = StatsForm()
        self.registerForm("MAIN", self.statsForm)

    def getMainForm(self):
        return self.statsForm

#class BoxTitle(npyscreen.BoxBasic):
#    _contained_widget = npyscreen.TitleFixedText

class StatsForm(npyscreen.FormBaseNew):
    def create(self):
        self.dataColOffset = 25
        self.max_width=80
        self.csTitle  = self.add(npyscreen.TitleFixedText, editable = True, 
                                 name = "ContentStore:", value=None,
                                 max_width=80, begin_entry_at=self.dataColOffset)
        self.csSize   = self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                 name = "Size (Mb):", value="some text",
                                 max_width=80, begin_entry_at=self.dataColOffset)
        self.csNumEntries  = self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                 name = "# Entries:", value="some text",
                                 max_width=80, begin_entry_at=self.dataColOffset)
        self.csAdds   = self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                 name = "# Adds:", value="some text",
                                 max_width=80, begin_entry_at=self.dataColOffset)
        self.csHits   = self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                 name = "# Hits:", value="some text",
                                 max_width=80, begin_entry_at=self.dataColOffset)
        self.csMisses = self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                 name = "# Misses:", value="some text",
                                 max_width=80, begin_entry_at=self.dataColOffset)

        # Seperator.
        self.add(npyscreen.TitleFixedText, editable=False, name=" ", value ="")

        self.fTitle  = self.add(npyscreen.TitleFixedText, editable = True, 
                                 name = "Athena:", value=None, 
                                  max_width=80, begin_entry_at=self.dataColOffset)
        self.fNumCOs   = self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                  name = "# ContentObjects:", value="some text",
                                  max_width=80, begin_entry_at=self.dataColOffset)
        self.fNumInterests   = self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                  name = "# Interests:", value="some text",
                                  max_width=80, begin_entry_at=self.dataColOffset)
        self.fNumInterestReturns   = self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                  name = "# Int Returns:", value="some text",
                                  max_width=80, begin_entry_at=self.dataColOffset)
        self.fNumControl = self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                  name = "# Control:", value="some text",
                                  max_width=80, begin_entry_at=self.dataColOffset)
        # Seperator.
        self.add(npyscreen.TitleFixedText, editable=False, name=" ", value ="")

        self.pTitle  = self.add(npyscreen.TitleFixedText, editable = True, 
                                 name = "PIT:", value=None, 
                                 max_width=80, begin_entry_at=self.dataColOffset)
        self.pAvgLifetime = self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                     name = "# Avg. Entry Lifetime:", value="some text",
                                     max_width=80, begin_entry_at=self.dataColOffset)
        self.pNumEntries= self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                   name = "# Entries:", value="some text",
                                   max_width=80, begin_entry_at=self.dataColOffset)
        self.pNumPending = self.add(npyscreen.TitleFixedText, editable=False, relx = 4,
                                    name = "# Pending Entries:", value="some text",
                                    max_width=80, begin_entry_at=self.dataColOffset)

if __name__ == "__main__":
    app = CollectorApp()

    thread.start_new_thread(poll_athena_for_stats, ("BGSync", app, 1,))

    app.run()





