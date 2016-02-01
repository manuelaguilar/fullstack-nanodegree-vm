# Multi tournament simulator v0.2

This project simulates tournament pairings for one or more tournaments.

1. To run the basic model with no tournament registry, no draws allowed, and no multi-point match wins, setup the database by executing the tournament.sql file:
  * psql -f tournament.sql
2. Execute the test driver:
  * ./tournament_test.py
3. To run the multi-tournament with, 3 point matches, draws, and player byes, setup the database again:
  * psql -f tournament.sql
4. Run the multi tournament test driver. This test driver creates 2 tournaments with registered players, but will only play matches for the U.S. Open tournament.
  * ./multi_tournament_test.py

### OPTIONAL

a. A json file is provided (atp_rankings.json). In order to modify the number of players, use the atp_rankings scrapy project and modify the vagrant/atp_rankings/atp_rankings/spiders/atp_rankings_spider.py file. Afterwards, execute the script run.sh in the atp_rankings directory. That will generate a new atp_rankings.json file.

