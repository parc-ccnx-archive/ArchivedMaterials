# CCNxChat

## Overview

CCNxChat is a simple group-based chat application based on CCNx 1.0. It uses names
to identity chat rooms, and Interest payloads to propagate messages from clients
to the server. The chat server is responsible for maintaining a sequential list
of text messages for each chat room. Each text message is associated with a monotonically
increasing sequence number. Clients send new chat messages to the server in Interest
messages, and the server synchronously appends them to the list. Clients poll the
chat server periodically to discover the size of the text list for a given chat room.
If their local state does not match that of the server, the client explicitly asks
for all missing messages based on their sequence number.

## Basic Usage

> athena  (do not enable content store... yet)
> python chat_server.py -l lci:/ccnx/chat
> python chat_client.py -l lci:/ccnx/chat/room -u username

Run either program with the "-h" or "--help" flag for more information.

## What's Missing?

Implement the `request_missing_texts()` function in the CCNxChatClient.py 
file, which is responsible for updating the local state of the chat client with
all messages that have been submitted by peers in the same chat room.

## Message Syntax

Interest:
    lci:/ccnx/game/chat/list
Content Object:
    lci:/ccnx/game/chat/list
    {"status": 1, "roomList": ["room"]}

Interest:
    lci:/ccnx/game/chat/room/seq  
Content Object:
    lci:/ccnx/game/chat/room/seq
    {"status": 0, "timestamp": 1443198637042, "seq": 410}

Interest:
    lci:/ccnx/game/chat/room/text/410
Content Object:
    lci:/ccnx/game/chat/room/text/410
    {"status": 0, "timestamp": 1443196067045, "userName": "Descartes", "seq": 410, "text": "checking restart"}

Interest:
    lci:/ccnx/game/chat/room/text
    {"user": "Descartes", "text": "I type, therefore I am? No, wait... that's not right."}

## Extensions:

Possible extensions include:

- If you enable the content store, the /seq interest gets a cached response from the forwarder.
  Make it work with the content store enabled.
- Add client and server support for more /slash commands, e.g., /kick, /whois, /msg.
- Add chat room encryption using group-shared keys.
- Implement Manifest support to store slices of a conversation (sets of text messages).
