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
CREATE SEQUENCE match_seq_id START 1; -- owned by matches.id;
CREATE SEQUENCE tournament_id START 1000;

CREATE TABLE players (
	id	integer	PRIMARY KEY default nextval('player_id'),
	name	varchar(120) NOT NULL 
);

CREATE TABLE matches (
	id	integer PRIMARY KEY default nextval('match_seq_id'),
	winner	integer REFERENCES players (id),
	loser	integer REFERENCES players (id),
        draw	boolean default false
);

CREATE TABLE tournament (
        id      integer PRIMARY KEY default nextval('tournament_id'),
        name    varchar(120)
);


CREATE TABLE standings (
        tournament_id integer references tournament(id),
        player_id	integer references players(id) ON DELETE CASCADE, 
	wins	integer,
        draws   integer,
        losses  integer,
	matches integer
);



CREATE TABLE tournament_matches (
        match_id integer REFERENCES matches(id) ,
        tournament_id integer REFERENCES tournament(id),
        UNIQUE (match_id, tournament_id)
);

CREATE TABLE tournament_registry (
        tournament_id   integer REFERENCES tournament (id),
        player_id       integer REFERENCES players(id),
        UNIQUE (tournament_id, player_id)
);

CREATE VIEW v_standings_post AS
       ---select tr.tournament_id, tr.player_id, count(m.winner),count(m.loser),count(m.draw),count(id) from tournament_registry tr, tournament_matches tm, matches m where tm.match_id=m.id and (tr.player_id=m.winner or tr.player_id=m.loser) group by tr.tournament_id, tr.player_id;
       select tr.tournament_id, tr.player_id, 
           sum (case when m.winner=tr.player_id and m.draw=false then 1 else 0 end) as wins,
           sum (case when m.loser=tr.player_id and m.draw=false then 1 else 0 end) as losses,
           sum (case when (m.winner=tr.player_id or m.loser=tr.player_id) and m.draw=true then 1 else 0 end) as draws,
           sum (case when m.winner=tr.player_id or m.loser=tr.player_id then 1 else 0 end) as matches
           from tournament_registry tr, tournament_matches tm, matches m where tm.match_id=m.id and tr.tournament_id=tm.tournament_id group by tr.tournament_id, tr.player_id;


ALTER SEQUENCE player_id owned by players.id;
ALTER SEQUENCE match_seq_id owned by matches.id;
ALTER SEQUENCE tournament_id owned by tournament.id;

CREATE VIEW v_standings AS
	SELECT s.player_id, p.name, s.wins, s.matches from players p, standings s where p.id = s.player_id order by s.wins desc, p.name asc;

CREATE VIEW v_tournament_points AS
        SELECT s.tournament_id, p.id, p.name, s.matches, s.wins, s.losses, s.draws, (s.wins*3)+(s.draws*1) as points from players p, standings s where p.id=s.player_id order by points desc;

CREATE VIEW v_matches_detail AS
	SELECT m.id, m.winner as winner_id, p1.name as winner, m.loser as loser_id, p2.name as loser from matches m left join players p1 on m.winner = p1.id left join players p2 on  m.loser = p2.id;

CREATE VIEW v_players_opponents AS
	(select m.id as match,p.id as player,m.winner as opponent from players p join matches m on (p.id=m.winner or p.id=m.loser) and m.winner != p.id union
	select m.id as match,p.id as player,m.loser as opponent from players p join matches m on (p.id=m.winner or p.id=m.loser) and m.loser != p.id ) order by player;

CREATE VIEW v_players_opponents_wins AS
	select tm.tournament_id, p.id as player, count(m.winner) as opponents_wins from matches m, v_players_opponents vpo, players p, tournament_matches tm where tm.match_id=m.id and vpo.player=p.id and vpo.opponent=m.winner and m.draw=false group by tm.tournament_id,p.id ;

CREATE VIEW v_tournament_standings AS
	select vtp.tournament_id , id , name , matches , wins , losses , draws , points , player , CASE WHEN opponents_wins is NULL then 0 ELSE opponents_wins END from v_tournament_points vtp left join v_players_opponents_wins vpow on vtp.id=vpow.player order by points desc, opponents_wins desc;

CREATE FUNCTION update_tournament_registry()
    RETURNS TRIGGER AS
    $BODY$
    BEGIN
    INSERT INTO standings (tournament_id, player_id, matches, wins, losses, draws) values (currval('tournament_id'), currval('player_id'), 0, 0, 0, 0);
    END;
    $BODY$ LANGUAGE plpgsql;

---CREATE TRIGGER tournament_registry_entry AFTER INSERT ON tournament_registry
---    EXECUTE PROCEDURE update_tournament_registry();

CREATE FUNCTION tournament_standings(tid integer) RETURNS TABLE (tournament_id integer, id integer, name varchar, matches integer , wins integer, losses integer , draws integer , points integer, player integer , opponents_wins bigint) AS $$
    select vtp.tournament_id , id , name , matches , wins , losses , draws , points , player , CASE WHEN opponents_wins is NULL then 0 ELSE opponents_wins END from v_tournament_points vtp left join v_players_opponents_wins vpow on vtp.id=vpow.player where vtp.tournament_id=tournament_standings.tid order by vtp.points desc, vpow.opponents_wins desc;   
$$ LANGUAGE SQL;


CREATE TABLE test_players(
	id	integer
);

CREATE TABLE test_matches(
        id	integer,
        winner	integer,
	loser	integer,
	draw	boolean
);

insert into test_players values (1);
insert into test_players values (2);
insert into test_players values (3);
insert into test_players values (4);

insert into test_matches values (1,1,2,false);
insert into test_matches values (2,3,4,false);
insert into test_matches values (3,3,1,false);
insert into test_matches values (4,2,4,false);

CREATE VIEW v_test AS
	(select m.id as match,p.id as player,m.winner as opponent from test_players p join test_matches m on (p.id=m.winner or p.id=m.loser) and m.winner != p.id union
select m.id as match,p.id as player,m.loser as opponent from test_players p join test_matches m on (p.id=m.winner or p.id=m.loser) and m.loser != p.id ) order by player;

