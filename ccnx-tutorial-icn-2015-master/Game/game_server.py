#!/usr/bin/python

# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-

# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
# Copyright 2015 Palo Alto Research Center, Inc. (PARC), a Xerox company.  All Rights Reserved.
# The content of this file, whole or in part, is subject to licensing terms.
# If distributing this software, include this License Header Notice in each
# file and provide the accompanying LICENSE file.

# @author Christopher A. Wood, System Sciences Laboratory, PARC
# @copyright 2015 Palo Alto Research Center, Inc. (PARC), A Xerox Company. All Rights Reserved.

import sys, json, random, threading
from CCNxClient import *

def createAddLinkMessage(host, port, nickName):
    lci = "lci:/local/forwarder/TransportLinkAdapter/add"
    payloadString = b"tcp://%s:%d/name=%s" % (str(host), port, str(nickName))
    return lci, payloadString

def createAddRouteMessage(lci, linkNickName):
    controlLci = "lci:/local/forwarder/FIB/add"
    payloadString = b"%s %s" % (str(lci), str(linkNickName))
    print "Route: ", payloadString
    return controlLci, payloadString

def state_to_string(state):
    size = state["radius"] * 2
    result = ""
    hits = state["hits"]
    misses = state["misses"]
    for i in range(size):
        for j in range(size):
            if (i, j) in hits:
                result = result + "X "
            elif (i, j) in misses:
                result = result + "O "
            else:
                result = result + "- "
        result = result + "\n"
    return result

class Cell(object):
    def __init__(self):
        self.symbol = "-"
        self.hit_flag = False
        self.empty = True

    def hit(self):
        self.hit_flag = True
        if not self.empty:
            self.symbol = "X"
        else:
            self.symbol = "O"

    def is_hit(self):
        return self.hit_flag and not self.empty

    def is_miss(self):
        return self.hit_flag and self.empty

    def is_empty(self):
        return self.empty

    def set_target(self):
        self.empty = False
        self.symbol = "#"

    def __str__(self):
        return self.symbol

class Board(object):
    def __init__(self, size):
        self.board = []
        self.size = size
        for i in range(size):
            self.board.append([])
            for j in range(size):
                cell = Cell()
                self.board[i].append(cell)

    def board_size(self):
        return self.size

    def get_cell_at(self, x, y):
        return self.board[x][y]

    def hit_cell_at(self, x, y):
        print self.board[x % self.size][y % self.size].hit()

    def slice(self, x, y, xsize, ysize = None):
        if ysize == None:
            ysize = xsize

        rows = []
        for r in range(xsize):
            row = []
            for c in range(ysize):
                xx = (x + r) % self.size
                yy = (y + c) % self.size
                row.append(self.board[xx][yy])
            rows.append(row)
        return rows

    def __str__(self):
        result = ""
        for i in range(self.size):
            for j in range(self.size):
                result = result + str(self.board[i][j]) + " "
            result = result + "\n"
        return result

class Target(object):
    def __init__(self, x, y, xsize, ysize, cells): # defines a bounding box
        self.x = x
        self.y = y
        self.xsize = xsize
        self.ysize = ysize
        self.cells = cells
        for cell_list in self.cells:
            for cell in cell_list:
                cell.set_target()

    def at(self, x, y):
        if (x >= self.x and x <= (self.x + xsize)) and (y >= self.y and y <= (self.y + ysize)):
            return True
        else:
            return False

    def is_destroyed(self):
        for cell_list in self.cells:
            for cell in cell_list:
                if not cell.is_hit():
                    return False
        return True

class Ship(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move_by(self, x, y):
        self.x = self.x + x
        self.y = self.y + y

class Player(object):
    def __init__(self, name, numShips, size, ipAddress, port, teamplayer):
        self.name = name
        self.ships = []
        self.ipAddress = ipAddress
        self.port = port
        self.teamplayer = teamplayer

        for i in range(numShips):
            x = random.randint(0, size)
            y = random.randint(0, size)
            self.ships.append(Ship(x, y))

    def get_ship_locations(self):
        locations = []
        for ship in self.ships:
            locations.append((ship.x, ship.y))
        return locations

    def get_ship_location(self, ship):
        return self.ships[ship].x, self.ships[ship].y

    def move_ship_by(self, ship, x, y):
        self.ships[ship].move_by(x, y)

    def __str__(self):
        result = {
            "name" : self.name,
            "ip" : self.ipAddress,
            "port" : self.port,
            "teamplayer" : self.teamplayer
        }
        return json.dumps(result)

class Game(object):
    def __init__(self, size, num_targets, radius):
        self.board = Board(size)
        self.players = {}
        self.targets = []
        self.round = 0
        self.radius = radius
        self.init_targets(num_targets)
        self.isDone = False

    def init_targets(self, num_targets):
        for n in range(num_targets):
            x0 = random.randint(0, self.board.board_size())
            y0 = random.randint(0, self.board.board_size())

            # TODO: need a way to configure target size
            xsize = random.randint(1, 2)
            ysize = random.randint(1, 2)
            slice = self.board.slice(x0, y0, xsize, ysize)
            self.targets.append(Target(x0, y0, xsize, ysize, slice))

    def is_over(self):
        return all(map(lambda target : target.is_destroyed(), self.targets))

    def add_player(self, name, numShips, ipAddress = "", port = 0, teamplayer = False):
        player = Player(name, numShips, self.board.board_size(), ipAddress, port, teamplayer)
        self.players[name] = player

    def parse_shoot(self, name, params):
        y = params["y"] - 1
        x = params["x"] - 1
        ship = params["ship-number"]

        center_x, center_y = self.players[name].get_ship_location(ship)
        realx, realy = center_x + x, center_y + y

        self.board.hit_cell_at(realx, realy)

    def parse_move(self, name, params):
        y = params["y"] - 1
        x = params["x"] - 1
        ship = params["ship-number"]

        self.players[name].move_ship_by(ship, x, y)

    def parse_response(self, name, response):
        command = response["action"]
        timestamp = response["timestamp"]
        token = response["token"]
        params = response["params"]
        if (command == "move"):
            self.parse_move(name, params)
        elif (command == "shoot"):
            self.parse_shoot(name, params)
        pass

    def get_player_state(self, name, ship):
        center_x, center_y = self.players[name].get_ship_location(ship)
        boardSlice = self.board.slice(center_x, center_y, self.radius * 2)

        hits = []
        misses = []
        targets = []

        for row, cell_row in enumerate(boardSlice):
            for col, cell in enumerate(cell_row):
                x = row % (self.radius * 2)
                y = col % (self.radius * 2)
                if cell.is_hit():
                    hits.append((x, y))
                elif cell.is_miss():
                    misses.append((x, y))
                elif not cell.is_empty():
                    targets.append((x, y))

        doneFlag = 0
        if self.isDone:
            doneFlag = 1
        state = {
            "center_x" : center_x,
            "center_y" : center_y,
            "radius" : self.radius,
            "hits" : hits,
            "misses" : misses,
            "targets" : targets,
            "gameover" : doneFlag
        }

        return state

    def play(self):
        client = CCNxClient(async = True)
        while not self.is_over():
            for player in self.players.keys():
                print >> sys.stderr, "Asking " + str(player) + " for move..."
                playerActionName = "lci:/tutorial/" + str(player) + "/action"
                data = client.get_async(playerActionName, None, 5)
                if data != None:
                    payload = json.loads(data)
                    user = payload["username"]
                    action = payload["action"]
                    params = payload["params"]

                    print >> sys.stderr, user, params

                    if action == "move":
                        self.parse_move(user, params)
                    elif action == "shoot":
                        self.parse_shoot(user, params)

                    print self.board

        for player in self.players:
            gameOverName = "lci:/tutorial/" + str(player) + "/gameover"
            client.push(gameOverName, None)
        self.isDone = True

    def listen(self):
        client = CCNxClient()
        tutorialPrefix = "lci:/tutorial/game"
        gameInfoName = "lci:/tutorial/game/info"
        playerConnectName = "lci:/tutorial/game/connect"
        playerInfoName = "lci:/tutorial/game/players"
        playerStateName = "lci:/tutorial/game/players/state"

        listening = client.listen(tutorialPrefix)
        while listening:
            name, data = client.receive()

            # Short circuits
            if name == None or data == None:
                continue
            if self.isDone:
                listening = False
                continue

            if name == gameInfoName:
                payload = {
                    "connect-url" : str(playerConnectName),
                    "board-size" : self.board.board_size(),
                    "player-url" : str(playerInfoName),
                    "state-url" : str(playerStateName)
                }
                payload = json.dumps(payload)
                client.reply(name, payload)
            if name == playerInfoName:
                payload = json.dumps(str(self.players))
                client.reply(name, payload)
            if playerStateName in name:
                payload = json.loads(data)
                player = payload["username"]
                shipNumber = payload["ship-number"]
                state = self.get_player_state(player, 0)
                payload = json.dumps(state)
                client.reply(name, payload)
            if playerConnectName in name:
                payload = json.loads(data)
                username = payload["username"]
                ipAddress = payload["ip"]
                port = int(payload["port"])
                teamplayer = int(payload["teamplayer"])
                numberOfShips = int(payload["number-of-ships"])

                payload = json.dumps({ "result" : "OK" })
                client.reply(name, payload)

                # Configure a link and route back to the client
                name, data = createAddLinkMessage(ipAddress, port, username)
                client.push(name, data)
                name, data = createAddRouteMessage("lci:/tutorial/" + username, username)
                client.push(name, data)

                self.add_player(username, numberOfShips, ipAddress, port, teamplayer)
                print >> sys.stderr, "Adding player: " + username

def main(args):
    fail_fast()

    game = Game(10, 1, 5)

    gameThread = threading.Thread(target=game.play)
    gameThread.start()

    # Block and listen.
    handlerThread = threading.Thread(target=game.listen)
    handlerThread.start()

    # Wait until the game is completed.
    gameThread.join()

if __name__ == "__main__":
    main(sys.argv[1:])
