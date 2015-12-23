#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import itertools

def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    DB = connect()
    c = DB.cursor()
    #c.execute("DELETE from matches")
    c.execute("TRUNCATE table matches RESTART IDENTITY")
    DB.commit()
    DB.close()

def deletePlayers():
    """Remove all the player records from the database."""
    DB = connect()
    c = DB.cursor()
    #c.execute("DELETE from players")
    c.execute("TRUNCATE table players RESTART IDENTITY CASCADE")
    DB.commit()
    DB.close()

def countPlayers():
    """Returns the number of players currently registered."""
    DB = connect()
    c = DB.cursor()
    c.execute("SELECT count(1) from players")
    count = c.fetchall()[0][0]
    DB.close()
    return count

def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    DB = connect()
    c = DB.cursor()
    c.execute("INSERT INTO players (name) values (%s)" , (name,))
    c.execute("SELECT id from players where name = %s" , (name,)) 
    player_id = c.fetchall()[0][0]
    c.execute("INSERT INTO standings (id, wins, matches) values ( %s, 0, 0 )" , (player_id,))
    DB.commit()
    DB.close()

def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    DB = connect()
    c = DB.cursor()
    #c.execute("SELECT s.id, p.name, s.wins, s.matches from players as p, standings as s where p.id = s.id")
    c.execute("SELECT * from v_standings")
    results = c.fetchall()
#    print "DEBUG:"
#    print results
    return results

def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    DB = connect()
    c = DB.cursor()
    c.execute("INSERT into matches (winner, loser) values (%s, %s)", (winner, loser))
    c.execute("UPDATE standings set wins=wins+1 where id=%s", (winner,))
    c.execute("UPDATE standings set matches=matches+1 where id in (%s, %s)", (winner, loser))
    DB.commit()
    DB.close()
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    #set matching groups
    DB = connect()
    c = DB.cursor()
    c.execute("SELECT wins FROM standings GROUP BY wins ORDER BY WINS DESC")
    groups = [item[0] for item in c.fetchall()]
    pairings = []
    for i in groups:
	c.execute("SELECT id from standings where wins=%s", (i,))
        group_players = [item[0] for item in c.fetchall()]
        #combine players
	possible_matches = itertools.combinations(group_players,2)
        for match in possible_matches:
            #discard matches in database
            c.execute("SELECT 1 from matches where (winner=%s and loser=%s) or (winner=%s and loser=%s)", (match[0],match[1],match[1],match[0]))
            played = c.fetchall()
            if not played :
    	        c.execute("SELECT id, name from players where id in %s", (match,))
                match_players = c.fetchall()
                pairings.append([match_players[0][0],match_players[0][1],match_players[1][0],match_players[1][1]])
    DB.commit()
    DB.close()
    
#    print "DEBUG pairings:"
#    print pairings
    return pairings


