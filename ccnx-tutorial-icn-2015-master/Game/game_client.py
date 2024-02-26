#!/usr/bin/python

# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-

# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
# Copyright 2015 Palo Alto Research Center, Inc. (PARC), a Xerox company.  All Rights Reserved.
# The content of this file, whole or in part, is subject to licensing terms.
# If distributing this software, include this License Header Notice in each
# file and provide the accompanying LICENSE file.

# @author Christopher A. Wood, System Sciences Laboratory, PARC
# @copyright 2015 Palo Alto Research Center, Inc. (PARC), A Xerox Company. All Rights Reserved.

import sys, json, tabulate
from CCNxClient import *

def state_to_string(state):
    size = state["radius"] * 2
    result = ""
    hits = map(lambda l : (l[0], l[1]), state["hits"])
    misses = map(lambda l : (l[0], l[1]), state["misses"])
    targets = map(lambda l : (l[0], l[1]), state["targets"])

    rows = []
    header = [" "]
    for j in range(size):
        header.append(str(j + 1))
    for i in range(size):
        row = []
        row.append(str(i + 1))
        for j in range(size):
            if (i, j) in hits:
                row.append("X")
            elif (i, j) in misses:
                row.append("O")
            elif (i, j) in targets:
                row.append("#")
            else:
                row.append("-")
        rows.append(row)
    return tabulate.tabulate(rows, headers=header)

class GameClient(object):
    def __init__(self, username):
        self.ccnxClient = CCNxClient()
        self.username = username

    #@Remove
    def init(self):
        self.connectUri = "lci:/tutorial/game/connect"
        self.personalPrefix = "lci:/tutorial/" + self.username
        self.actionPrefix = "lci:/tutorial/" + self.username + "/action"
        self.statePrefix = "lci:/tutorial/game/players/state/" + self.username

    #@Remove
    def connect(self):
        payload = {
            "ip" : "localhost",
            "port" : 9695,
            "username" : self.username,
            "teamplayer" : 0,
            "number-of-ships" : 1
        }
        self.ccnxClient.get(self.connectUri, json.dumps(payload)) # consume the result

    def run(self):
        listening = self.ccnxClient.listen(self.personalPrefix)
        while listening:
            name, data = self.ccnxClient.receive()

            if name == None:
                continue

            if "action" in name:
                self.display_state()
                self.take_action(name)
                listening = self.display_state()

    #@Remove
    def get_state(self, ship = 0):
        payload = {
            "username" : self.username,
            "ship-number" : ship,
        }
        data = self.ccnxClient.get(self.statePrefix, json.dumps(payload))
        while data == None:
            data = self.ccnxClient.get(self.statePrefix, json.dumps(payload))
        state = json.loads(data)
        return state

    def display_state(self, ship = 0):
        state = self.get_state(ship)
        if state["gameover"] == 1:
            print "Game over!"
            return False
        else:
            table = state_to_string(state)
            print table
            return True

    def get_input(self):
        action = str(raw_input('ACTION: '))
        x = int(input('ROW: '))
        y = int(input('COL: '))
        # ship = int(input('ship: '))
        return (action, x, y, 0)

    #@Remove
    def take_action(self, name):
        (action, x, y, ship) = self.get_input()
        params = {"x": x, "y": y, "ship-number": ship}
        response = { "username" : self.username, "action" : action, "params" : params }
        payload = json.dumps(response)
        self.ccnxClient.reply(name, payload)

def main(username):
    fail_fast()
    client = GameClient(username)
    client.init()
    client.connect()
    client.run()

if __name__ == "__main__":
    main(sys.argv[1])
