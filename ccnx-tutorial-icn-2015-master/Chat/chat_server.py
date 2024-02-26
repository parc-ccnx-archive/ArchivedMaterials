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
    A very simple chat server using CCNx Interests and ContentObjects to pass
    chat messages around. Please see the README for info on the names used and
    example payloads.
"""

import sys, tempfile, getopt, time, json, random, sqlite3, operator

from CCNx import *

SECONDS_BEFORE_CONSIDERED_GONE = 60

def nowInMillis():
    return int(round(time.time() * 1000))

def setup_identity():
    global IDENTITY_FILE
    IDENTITY_FILE = tempfile.NamedTemporaryFile(suffix=".p12")
    identity = create_pkcs12_keystore(IDENTITY_FILE.name, "foobar", "bletch", 1024, 10)
    return identity

def open_portal():
    identity = setup_identity()
    factory = PortalFactory(identity)
    portal = factory.create_portal()  # Works.
    #portal = factory.create_portal(transport=TransportType_RTA_Message,
    #                               attributes=PortalAttributes_NonBlocking)
    return portal

def create_add_link_message(host, port, nickName):
        lci = "lci:/local/forwarder/TransportLinkAdapter/add"
        payload = "tcp://%s:%d/name=%s" % (host, port, nickName)

        interest = Interest(Name(lci))
        interest.setPayload(payload)

        return interest

def create_add_route_message(lci, linkNickName):
        lci = "lci:/local/forwarder/FIB/add"
        payload = "%s %s" % (lci, linkNickName)

        interest = Interest(Name(lci))
        interest.setPayload(payload)

        return interest

def send_and_wait_for_response(portal, message):
        portal.send(message)

        response = None
        while not response:
            response = portal.receive()

        if response and isinstance(response, ContentObject):
            print response.payload.value
            #j = json.loads(response.payload.value)
            #print "Response:"
            #print json.dumps(j, sort_keys=True, indent=4, separators=(',', ': '))
            #print "\n"

class BaseHandler(object):

    def __init__(self, listenPrefix):
        self.listenPrefix = listenPrefix  # e.g. lci:/foo/bar

    def done_handler(self, message, nameComponents):
        """ if we get a xxx/done, return False"""
        m = { "status": 0, "msg": "bye!"}
        return False, ContentObject(message.name, json.dumps(m))

    def handle_message(self, message):
        print "Handle(): ", message
        content = None
        name = str(message.name)[len(self.listenPrefix):]
        nameComponents = name.split('/')
        try:
            return getattr(self, nameComponents[1] + '_handler')(message, nameComponents)
        except:
            m = { "status": 1, "error": "No handler for name [%s]" % (message.name) }
            return True, ContentObject(message.name, json.dumps(m))

class ChatUser(object):
    """ some state about the user, should we start adding any kind of security... """
    def __init__(self, nick):
        self.nickName  = nick

class ChatRoom(object):
    def __init__(self, name):
        self.name = name
        self.members = {}
        self.messages = []
        self.dbfilename = ".ccnxChatRoom-%s.db" % (name)  # Where the chat contents persist
        self.db = sqlite3.connect(self.dbfilename)
        self.create_backing_table()
        self.lastRowId = self.get_last_seq_number_from_db()

    def create_backing_table(self):
        cur = self.db.cursor()
        cur.execute(
        "CREATE TABLE IF NOT EXISTS chat\
            ( id INTEGER PRIMARY KEY, \
              timestamp INTEGER, \
              username TEXT, \
              text TEXT \
              )" \
            )
        self.db.commit()
        cur.close()

    def get_last_seq_number_from_db(self):
        c = self.db.cursor()
        c.execute("select id from chat order by id DESC limit 1")
        row = c.fetchone()
        c.close()
        if row:
            return row[0]
        return 0

    def add_text(self, timestamp, userName, text):
        """ add the incoming text to the DB """
        rowId = 0
        c = self.db.cursor()
        c.execute('INSERT INTO chat (timestamp, username, text) \
                    VALUES(?,?,?)', (timestamp, userName, text))
        self.db.commit()
        self.lastRowId = c.lastrowid
        c.close()
        return self.lastRowId

    def get_text_at_index(self, message, textIx):
        """ given a particular sequence number (id), find that row """
        m = {}
        try:
            #userName, text = self.messages[textIx]
            c = self.db.cursor()
            c.execute("select id, userName, timestamp, text from chat where id = ?", (int(textIx),))
            row = c.fetchone()
            seq = row[0]
            userName = row[1]
            timestamp = row[2]
            text = row[3]
            c.close()

            m = {
                  "status": 0,
                  "seq": seq,
                  "timestamp": timestamp,
                  "userName" : userName,
                  "text": text,
                }
        except:
            m = { "status": 1, "error": "no such text object" }

        return True, ContentObject(message.name, json.dumps(m))


    def expire_disconnected_members(self, maxAgeInSeconds):
        """ Remove users from self.members if they haven't been seen in maxAgeInSeconds """
        timeSortedMembers = sorted(self.members.items(), key=operator.itemgetter(1))
        expireTime = nowInMillis() - (maxAgeInSeconds * 1000)
        for (user, t) in timeSortedMembers:
            if t < expireTime:
                del self.members[user]
                print "Expiring: ", user


    def create_member_list_hash(self):
        """ Return a hash of the sorted list of users (sorted by name) """
        activeMemberList = sorted(self.members)
        print "Active: ", activeMemberList
        return hash(tuple(activeMemberList))

    ##
    ## handlers for names start here:
    ##

    def poke_handler(self, message, nameComponents):
        # TODO: poke someone - should be direct message?
        pass
        return True, None
   
    # Called for /command interests
    def who_handler(self, message, nameComponents):
        """ called for /who """
        activeMemberList = sorted(self.members)
        m = { "status": 0, 
              "members": activeMemberList,
              "timestamp": nowInMillis(),
        }
        return True, ContentObject(message.name, json.dumps(m))


    def seq_handler(self, message, nameComponents):
        """ /<room>/seq  - return the last sequence number / id that this room has seen """
    
        try:
            j = json.loads(message.getPayload())
            userName = j['user']

            # Update the time last seen for this user
            self.members[userName] = nowInMillis()

        except:
            # This is an older client that doesn't include a payload with the seq command
            print "Old client connected. No 'user' in the /seq payload."
            pass

        self.expire_disconnected_members(SECONDS_BEFORE_CONSIDERED_GONE)
        memberListHash = self.create_member_list_hash()

        m = {
              "status": 0,
              "timestamp": nowInMillis(),
              "seq": self.lastRowId,
              "memberhash" : memberListHash
            }
        return True, ContentObject(message.name, json.dumps(m))

    def text_handler(self, message, nameComponents):
        """ /base/lci/<room>/text - if there is number following the /text, then this is a
            request for a particular text. In that case, fetch it and return it.
            Otherwise, if there's no number at the end, then it's an incoming text
            message (text content is in the payload). Store it.
        """

        print 1, nameComponents
        if len(nameComponents) > 1:
            nextComponent = nameComponents[0]       
            # This could be a payload ID. Python doesn't yet support that type.
            # What SHOULD happen here is that we check the NameSegment type.
            if "PayloadId" not in nameComponents[1]:
                return self.get_text_at_index(message, int(nameComponents[1]))

        j = json.loads(message.getPayload())
        now = nowInMillis()   # We use the server time for the time of the text messages
        userName = j['user']
        text = j['text']
        rowId = self.add_text(now, userName, text)

        m = {"status": 0,
             "timestamp": now,
             "seq": rowId
            }
        
        # This message should NOT be cached by forwarders, so set an expiration.
        return True, ContentObject(message.name, json.dumps(m))


    def handle_message(self, message, nameComponents):
        #print "ChatRoom [%s] handle_message(): %s" % (self.name,  nameComponents)
        # Handlers are named <segment string>_handler, and we look them up here.
        handler = getattr(self, nameComponents[1] + '_handler') # e.g. text_handler
        if not handler:
            m = { "status": 1, "error": "No ChatRoom handler for name [%s]" % (message.name) }
            return True, ContentObject(message.name, json.dumps(m))

        # Ok, we had a handler. Try it.
        try:
            return getattr(self, nameComponents[1] + '_handler')(message, nameComponents[1:])

        except Exception as e:
            m = {"status": 1,
                 "timestamp": nowInMillis(),
                 "error" : str(e)
                }

            return True, ContentObject(message.name, json.dumps(m))

class ChatHandler(BaseHandler):

    """ /base/lci/<room> - called to handle the base lci. Generally, there will be a room name appended.
        We just dispatch the message to the proper room handler. If one doesn't
        already exist for that room, create it and then pass it on.
    """

    def __init__(self, listenPrefix):
        BaseHandler.__init__(self, listenPrefix)
        self.rooms = {}

    def handle_message(self, message):
        content = None
        name = str(message.name)[len(self.listenPrefix):]
        nameComponents = name.split('/')
        try:
            roomName = nameComponents[1]

            if not roomName:
                m = { "status": 1, 
                      "error": "No handler for name [%s] - expected a room name." % (message.name) }
                return True, ContentObject(message.name, json.dumps(m))

            elif roomName == "list":
                # 'list' is a special case.
                m = { "status": 1, "roomList" : self.rooms.keys() }
                return True, ContentObject(message.name, json.dumps(m))

            try:
                room = self.rooms[roomName]
            except KeyError:
                room = ChatRoom(roomName)
                print "Created new ChatRoom: ", roomName
                self.rooms[roomName] = room

            return room.handle_message(message, nameComponents[1:])

        except Exception as e:
            m = { "status": 1, "timestamp" : nowInMillis(), "error": str(e) }
            return True, ContentObject(message.name, json.dumps(m))

def usage(argv):
    print "Usage: %s [-h ] [[-l | -lci] lci:/name/to/listen/on]" % argv[0]
    print "  e.g. ./%s -l lci:/ccnx/game/chat" % argv[0]

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
            print "Will answer for name [ %s ]" % namePrefix

    return (namePrefix, " ".join(args)) # listenPrefix, Everything left over

def main(lciPrefix):
    try:
        portal = open_portal()

        #linkMessage = create_add_link_message("eldorado.parc.xerox.com", 9695, "eldorado")
        #send_and_wait_for_response(portal, linkMessage)

        #routeMessage = create_add_route_message("lci:/foo/bar", "eldorado")
        #send_and_wait_for_response(portal, routeMessage)

        chatHandler = ChatHandler(lciPrefix)
        portal.listen(Name(lciPrefix))

        keepRunning = True
        while keepRunning:
            message = portal.receive()
            print "<== ", str(message)
            if message.getPayload():
                print "   payload: ", message.getPayload()
            keepRunning, response = chatHandler.handle_message(message)

            print "==>  ", response
            if response and response.getPayload():
                print "   payload: ", response.getPayload()
            if response:
                portal.send(response);


    except Portal.CommunicationsError as x:
        sys.stderr.write("sender: comm error attempting to listen: %s\n" % (x.errno,))

if __name__ == "__main__":

    lciPrefix, otherArgs = parse_args(sys.argv)
    if not lciPrefix:
        usage(sys.argv)
        sys.exit(2)

    main(lciPrefix)
