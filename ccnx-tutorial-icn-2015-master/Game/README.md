# Game

## Overview

This is a turn-based search-and-destroy game in which clients move around a
3D surface to shoot at targets. The game is over when all targets have been
hit. The client application works by connecting to the server and requesting
to join the game, providing its own name prefix in the process. The server
uses this prefix to issue Interests to each player (in sequence) when it is
their turn to make a move. Clients will dynamically fetch the state of their
own ship in the world before making a move. Clients will see hits and misses
of other players.

## Basic Usage

> python game_server.py
> python game_client.py username

Run either program with the "-h" or "--help" flag for more information.

## What's Missing?

Finish the implementation of the GameClient class in game_client.py. It is
missing the following functions: `init()`, `connect()`, `get_state()`,
and `take_action()`.

## Message Syntax

Interest:
    lci:/tutorial/game/info
Content Object:
    lci:/tutorial/game/info
    {
        "connect-url" : "lci:/tutorial/game/connect",
        "board-size" : 100,
        "player-url" : "lci:/tutorial/game/players",
        "state-url" : "lci:/tutorial/game/players/state"
    }

Interest:
    lci:/tutorial/game/connect
    {
        "ip" : "localhost",
        "port" : 9695,
        "username" : username,
        "teamplayer" : 0,
        "number-of-ships" : 1
    }
Content Object:
    lci:/tutorial/game/connect
    { "result" : "OK" }

Interest:
    lci:/tutorial/game/players/state
Content Object:
    lci:/tutorial/game/players/state
    {
        "center_x" : <integer>,
        "center_y" : <integer>,
        "radius" : <integer,
        "hits" : [],
        "misses" : [],
        "targets" : [],
        "gameover" : (0 | 1)
    }

Interest:
    lci:/tutorial/game/players
Content Object:
    lci:/tutorial/game/players
    {["user1", "user2", ...]}

## Extensions:

Possible extensions include:

- Add support for multiple ships per-user.
- Enable players to issue interests to other players for their state information,
e.g., for team-oriented gameplay.
- Add support for cheat messages to the server, e.g., to reveal the location
of all targets on the board.
