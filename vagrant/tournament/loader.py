import json


def loadPlayersFromJson(players_file):
    players_json_file = open(players_file)
    players_json = players_json_file.read()
    players = json.loads(players_json)
    players_json_file.close()
    return players
