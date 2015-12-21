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

CREATE SEQUENCE player_id START 100;
CREATE SEQUENCE match_id START 1;

CREATE TABLE IF NOT EXISTS players (
	id	integer	PRIMARY KEY,
	name	varchar(120) NOT NULL 
);

CREATE TABLE IF NOT EXISTS matches (
	id	integer PRIMARY KEY,
	player1_id	integer REFERENCES players (id),
	player2_id	integer REFERENCES players (id),
	winner_id 	integer REFERENCES players (id)
);

CREATE TABLE IF NOT EXISTS standings (
	position integer UNIQUE,
	points integer
);
