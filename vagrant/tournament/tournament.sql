-- Table definitions for the tournament project.
--
-- Put your SQL 'CREATE TABLE' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

DROP DATABASE IF EXISTS tournament;

CREATE DATABASE tournament;

\c tournament

CREATE SEQUENCE player_id START 100; ---owned by players.id;
CREATE SEQUENCE match_id START 1; -- owned by matches.id;

CREATE TABLE IF NOT EXISTS players (
	id	integer	PRIMARY KEY default nextval('player_id'),
	name	varchar(120) NOT NULL 
);

CREATE TABLE IF NOT EXISTS matches (
	id	integer PRIMARY KEY default nextval('match_id'),
	winner	integer REFERENCES players (id),
	loser	integer REFERENCES players (id)
);


CREATE TABLE IF NOT EXISTS standings (
        id	integer references players(id) ON DELETE CASCADE, 
	wins	integer,
	matches integer
);

ALTER SEQUENCE player_id owned by players.id;
ALTER SEQUENCE match_id owned by matches.id;

CREATE VIEW v_standings AS
	SELECT s.id, p.name, s.wins, s.matches from players as p, standings as s where p.id = s.id order by s.wins desc, p.name asc;

CREATE VIEW v_matches_detail AS
	SELECT m.id, m.winner as winner_id, p1.name as winner, m.loser as loser_id, p2.name as loser from matches m left join players p1 on m.winner = p1.id left join players p2 on  m.loser = p2.id;
