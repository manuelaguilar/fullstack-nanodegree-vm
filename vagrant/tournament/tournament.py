#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import itertools
import random

def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    DB = connect()
    c = DB.cursor()
    #c.execute("DELETE from matches")
    c.execute("TRUNCATE table matches RESTART IDENTITY CASCADE")
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
    c.execute("SELECT currval('player_id')") # from players where name = %s" , (name,)) 
    player_id = c.fetchall()[0][0]
    c.execute("INSERT INTO standings (player_id, matches, wins, losses, draws) values ( %s, 0, 0, 0, 0 )" , (player_id,))
    DB.commit()
    DB.close()

def registerTournamentPlayer(name, tournament_name):
    """Adds a registered player in a specific tournament.

    Args:
      Both name and tournament_name exist in the database.
    """
    DB = connect()
    c = DB.cursor()
    c.execute("SELECT id from players where name = %s", (name,))
    player_id = c.fetchall()[0][0]
    c.execute("SELECT id from tournament where name = %s", (tournament_name,))
    tournament_id = c.fetchall()[0][0] 
    c.execute("INSERT INTO tournament_registry (tournament_id, player_id) values (%s, %s)", (tournament_id, player_id)) 
    c.execute("INSERT INTO standings (tournament_id, player_id, matches, wins, losses, draws) values (%s, %s, 0, 0, 0, 0)", (tournament_id, player_id)) 
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
    c.execute("UPDATE standings set wins=wins+1 where player_id=%s", (winner,))
    c.execute("UPDATE standings set matches=matches+1 where player_id in (%s, %s)", (winner, loser))
    DB.commit()
    DB.close()

def reportTournamentMatch(tournament_id,winner, loser, draw=False):
    """Records the outcome of a single match between two players.

    Args:
      tournament_id: the id of an existing tournament
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
      draw: true or false if match was a draw or not.

    If not draw, winner standings are increased by 3.
    If draw, winner and loser standings are increased by 1 point each.
    """
    DB = connect()
    c = DB.cursor()
    c.execute("INSERT into matches (winner, loser, draw) values (%s, %s, %s)", (winner, loser, draw))
    c.execute("SELECT currval('match_seq_id')")
    match_id = c.fetchall()[0][0]
    c.execute("INSERT into tournament_matches (tournament_id, match_id) values (%s, %s)", (tournament_id,match_id))
    if not draw:
    	c.execute("UPDATE standings set wins=wins+1 where player_id=%s and tournament_id=%s", (winner,tournament_id))
        c.execute("UPDATE standings set losses=losses+1 where player_id=%s and tournament_id=%s", (loser,tournament_id))
    else:
	c.execute("UPDATE standings set draws=draws+1 where player_id in (%s, %s) and tournament_id=%s", (winner, loser, tournament_id))
    c.execute("UPDATE standings set matches=matches+1 where player_id in (%s, %s) and tournament_id=%s", (winner, loser,tournament_id))
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
	c.execute("SELECT player_id from standings where wins=%s", (i,))
        group_players = [item[0] for item in c.fetchall()]
        #combine players
	#possible_matches = itertools.combinations(group_players,2)
        possible_matches = getRoundMatches(group_players)
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

def getRoundMatches (group_players):
    choose_set = group_players 
    round_matches = []
    while choose_set:
        round_combinations = itertools.combinations(choose_set,2)
        #print "round combinations"
        #print round_combinations
        selected_match = random.choice(list(round_combinations))
        #print "selected match"
        #print selected_match
        round_matches.append(selected_match)
        for item in selected_match:
            choose_set.remove(item)
    return round_matches

def tournamentSwissPairings(tournament_name):
    """Returns a list of pairs of players for the next round of a match for a specific tournament.

    If first round, and number of players is odd, a random player gets a bye.
    """
    tournament_pairings = []
    bye_player = []
    DB = connect()
    c = DB.cursor()
    c.execute("SELECT id from tournament where name= %s", (tournament_name,))
    tournament_id = [item[0] for item in c.fetchall()][0]
    c.execute("SELECT count(1) from tournament_matches where tournament_id =%s", (tournament_id,))
    matches = [item[0] for item in c.fetchall()]
    c.execute("SELECT count(1) from tournament_registry where tournament_id=%s", (tournament_id,))
    players = [item[0] for item in c.fetchall()]
    if matches[0] == 0:
       #one player gets a bye
       if players[0] % 2 == 1:
           c.execute("select t.player_id,p.name from tournament_registry t, players p where t.tournament_id=%s and t.player_id=p.id order by random() limit 1", (tournament_id,))
           bye_player = c.fetchall()
           print "bye_player" 
           print bye_player
           #tournament_pairings.append(([bye_player[0][0],bye_player[0][1]]))
           tournament_pairings.append( bye_player )
           c.execute("select t.player_id from tournament_registry t where t.tournament_id=%s and t.player_id!=%s", (tournament_id,bye_player[0][0]))
       else:
           c.execute("select t.player_id from tournament_registry t where t.tournament_id=%s", (tournament_id,))
       group_players = [item[0] for item in c.fetchall()]
       print group_players
       first_round_matches = getRoundMatches(group_players) 
       for match in first_round_matches:
           #discard duplicate matches
           c.execute("SELECT 1 from matches m join tournament_matches tm on m.id=tm.match_id where tm.tournament_id=%s and ( (winner=%s and loser=%s) or (winner=%s and loser=%s) )", (tournament_id, match[0],match[1],match[1],match[0]))
           played = c.fetchall()
           if not played:
               c.execute("SELECT id, name from players where id in %s", (match,))
               match_players = c.fetchall()
               #tournament_pairings.append((([match_players[0][0],match_players[0][1]),(match_players[1][0],match_players[1][1]])))
               tournament_pairings.append( ((match_players[0]),(match_players[1])) )
    else:
        c.execute("SELECT id from v_tournament_standings where tournament_id=%s",(tournament_id,))
        standings_players = [item[0] for item in c.fetchall()]
        print "Standings ids:"
        print standings_players
        match_list = standings_players[:]
        for idx, player1 in enumerate(standings_players): 
            print "Finding match for "
            print player1
            match_list.remove(player1)
            print match_list
            if not match_list:
                #player gets bye
                c.execute("select id, name from players where id=%s",(player1,))
                bye_player = c.fetchall()
                print "round bye player"
                print bye_player
                tournament_pairings.append(bye_player)
            for player2 in match_list: 
                if not matchExists(tournament_id,player1,player2):
                    #print player1
                    #print player2
                    c.execute("SELECT id, name from players where id in (%s,%s)", (player1, player2))
                    match_players = c.fetchall()
                    print "Matched:"
                    print match_players
                    tournament_pairings.append( ((match_players[0]),(match_players[1])))
                    #standings_players.remove(player1)
                    standings_players.remove(player2)
                    #match_list.remove(player1)
                    match_list.remove(player2)
                    print "Left in pool:"
                    print standings_players
                    print idx
                    #print sp
                    break
    DB.commit()
    DB.close()
    return tournament_pairings
 
def createTournament(tournament_name):
    """Creates a tournament with a generated tournament id
    
    Args:
      tournament_name: a unique tournament name
    """
    DB = connect()
    c = DB.cursor()
    c.execute("INSERT into tournament (name) values (%s)",(tournament_name,))
    DB.commit()
    DB.close()

def matchExists(tournament_id, player1, player2):
    #player cannot play with himself or herself
    if player1 == player2 :
        return True    
    DB = connect()
    c = DB.cursor()
    c.execute("SELECT 1 from matches m join tournament_matches tm on m.id=tm.match_id where tm.tournament_id=%s and ( (winner=%s and loser=%s) or (winner=%s and loser=%s) )", (tournament_id, player1,player2,player2,player1)) 
    match_exists = c.fetchall()
    DB.commit()
    DB.close()
    return match_exists

def tournamentStandings(tournament_name):
    tournament_standings=[]
    DB = connect()
    c = DB.cursor()
    c.execute("SELECT id from tournament where name=%s",(tournament_name,))
    tournament_id = [item[0] for item in c.fetchall()][0]
    c.execute("SELECT * from v_tournament_standings where tournament_id=%s", (tournament_id,))
    tournament_standings = c.fetchall()
    DB.commit()
    DB.close()
    return tournament_standings

def playRound(tournament_name, pairings_list):
    DB = connect()
    c = DB.cursor()
    c.execute("SELECT id from tournament where name=%s",(tournament_name,))
    tournament_id = [item[0] for item in c.fetchall()][0]
    print "tournament id:"
    print tournament_id
    for players in pairings_list:
        if len(players)==1 :
            print "bye for:"
            print players
            c.execute("UPDATE standings set wins=wins+1 where player_id=%s and tournament_id=%s", (players[0][0],tournament_id))
            
        else:
            outcome = random.randint(1,3)
            if outcome == 1:
                print "winner:"
                print players[0]
                reportTournamentMatch(tournament_id,players[0][0],players[1][0])
            elif outcome == 2:
                print "winner:"
                print players[1]
                reportTournamentMatch(tournament_id,players[1][0],players[0][0])
            else :
                print "Draw"
                print players
                reportTournamentMatch(tournament_id,players[0][0],players[1][0],True)
    DB.commit()
    DB.close()


