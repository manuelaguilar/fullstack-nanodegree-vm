#!/usr/bin/env python
#
# Test cases for tournament.py

from tournament import *
from loader import *


def testTournamentPairings():
    """Two tournaments are created.
    Tournament U.S. Open 2016 will have 17 players registered using a json
    file.
    Tournament Test Tournament won't have any matches but meets the zero
    matches.
    tournament standings requirement.

    Output will print first round matchings and pairings will be run until all
    players have played against each other.
    """
    createTournament("Test Tournament")
    createTournament("U.S. Open 2016")
    players = loadPlayersFromJson("atp_rankings.json")
    # register players in database
    for player in players:
        registerPlayer(player['player'][0])
    # register recorded players from database in tournament
    for player in players:
        registerTournamentPlayer(player['player'][0], "Test Tournament")
        registerTournamentPlayer(player['player'][0], "U.S. Open 2016")
    pairings1 = tournamentSwissPairings("Test Tournament")

# START PAIRINGS
    print "First pairing:"
    for pair in pairings1:
        print pair
    pairings2 = tournamentSwissPairings("U.S. Open 2016")
    r = 1
    while len(pairings2) > 1:
        playRound("U.S. Open 2016", pairings2)
        tournament_standings1 = tournamentStandings("U.S. Open 2016")
        print "After round %s of U.S. Open 2016 the standings are:" % r
        r = r+1
        for position in tournament_standings1:
            print position
        pairings2 = tournamentSwissPairings("U.S. Open 2016")
    print "End of pairings. Final standings"
    for position in tournamentStandings("U.S. Open 2016"):
        print position
# END PAIRINGS

if __name__ == '__main__':
    testTournamentPairings()
    print "Success!  All tests pass!"
