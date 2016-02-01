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

/* SEQUENCES for auto-generated ids */
CREATE SEQUENCE player_id START 100; 
CREATE SEQUENCE match_seq_id START 1;
CREATE SEQUENCE tournament_id START 1000;

CREATE TABLE players
(
    id        integer    PRIMARY KEY default nextval('player_id'),
    name      varchar(120) NOT NULL 
);


CREATE TABLE matches 
(
    id        integer PRIMARY KEY default nextval('match_seq_id'),
    winner    integer REFERENCES players (id),
    loser     integer REFERENCES players (id),
    draw      boolean default false
);


CREATE TABLE tournament 
(
    id        integer PRIMARY KEY default nextval('tournament_id'),
    name      varchar(120)
);


CREATE TABLE tournament_matches 
(
    match_id         integer REFERENCES matches(id) ,
    tournament_id    integer REFERENCES tournament(id),
    UNIQUE (match_id, tournament_id)
);


CREATE TABLE tournament_registry 
(
    tournament_id    integer REFERENCES tournament (id),
    player_id        integer REFERENCES players(id),
    UNIQUE (tournament_id, player_id)
);

/* VIEW v_overall_standings
 * This view will generate standings for all players registered
 * in any tournament.
 * It matches only players registered in a tournament,
 * and joins any existing match in a tournament where the player 
 * has participated, which is registered in the winner and loser fields.
 * For each match it adds 1 per case --win, loss, draw-- or it defaults
 * to ZERO if no case is found. This will ensure standings will
 * exist even if no matches have been played for a tournament player
 */
CREATE VIEW v_overall_standings AS
       select tr.tournament_id, p.id, p.name, 
           sum (case when m.winner=p.id and m.draw=false then 1 else 0 end) as wins,
           sum (case when m.loser=p.id and m.draw=false then 1 else 0 end) as losses,
           sum (case when (m.winner=p.id or m.loser=p.id) and m.draw=true then 1 else 0 end) as draws,
           sum (case when m.winner=p.id or m.loser=p.id then 1 else 0 end) as matches 
           from players p
               join tournament_registry tr on tr.player_id=p.id
               left outer join tournament_matches tm on tr.tournament_id=tm.tournament_id               
               left outer join matches m on m.id=tm.match_id and (tr.player_id=m.winner or tr.player_id=m.loser) 
               group by tr.tournament_id, p.id, p.name; 

/* AFTER tables created, assign SEQUENCE owners for each */
ALTER SEQUENCE player_id owned by players.id;
ALTER SEQUENCE match_seq_id owned by matches.id;
ALTER SEQUENCE tournament_id owned by tournament.id;

/* VIEW v_standings
 * Standard view for matches
 * where matches won by a player are counted, and the total 
 * number of matches is counted separately. Hence, the two left joins.
 */
CREATE VIEW v_standings AS
        SELECT p.id,p.name,count(m2.winner) as wins, count(m1.id) as matches from players p 
            left join matches m1 on m1.winner=p.id or m1.loser=p.id 
            left join matches m2 on m2.winner=p.id group by p.id order by wins desc;    

/* VIEW v_tournament_points
 * View to compute player points based on wins and draws
 * Winner gets 3 points per won match
 * Draw gets 1 point per drawn match
 */
CREATE VIEW v_tournament_points AS
        SELECT s.tournament_id, p.id, p.name, s.matches, s.wins, s.losses, s.draws, 
            (s.wins*3)+(s.draws*1) as points 
	    from players p, v_overall_standings s 
            where p.id=s.id order by points desc;

/* VIEW v_matches_details
 * Simple view to visualize matches and players
 */
CREATE VIEW v_matches_detail AS
    SELECT m.id, m.winner as winner_id, p1.name as winner, m.loser as loser_id, p2.name as loser 
            from matches m left join players p1 on m.winner = p1.id 
                left join players p2 on  m.loser = p2.id;

/* VIEW v_players_opponents
 * This view is the union of two sets.
 * The set of all player's opponents where the opponent won the match
 * union with the set of all player's opponents where the opponent lost the match.
 * For each tournament match, a player has and opponent identified as 'opponent'. 
 */
CREATE VIEW v_players_opponents AS
    (
        select tm.tournament_id, m.id as match,p.id as player,m.winner as opponent from players p 
            join matches m on (p.id=m.winner or p.id=m.loser) and m.winner != p.id join tournament_matches tm on tm.match_id=m.id  
        union
        select tm.tournament_id,m.id as match,p.id as player,m.loser as opponent from players p 
            join matches m on (p.id=m.winner or p.id=m.loser) and m.loser != p.id join tournament_matches tm on tm.match_id=m.id
    )
    order by player;

/* VIEW v_players_opponents_wins
 * For each tournament player, each opponent tournament wins is added based on the result 
 * obtained from the v_players_opponents view.
 */
CREATE VIEW v_players_opponents_wins AS
    select tm.tournament_id, p.id as player, count(m.winner) as opponents_wins 
            from matches m, v_players_opponents vpo, players p, tournament_matches tm 
            where tm.match_id=m.id and vpo.player=p.id and vpo.opponent=m.winner and m.draw=false 
            group by tm.tournament_id,p.id ;

/* VIEW v_tournament_standings
 * Left join of views v_tournament_points with v_players_opponents_wins, per tournament player
 * sorted by tournament points and by opponnents wins
 */
CREATE VIEW v_tournament_standings AS
    select vtp.tournament_id , id , name , matches , wins , losses , draws , points , player , 
        CASE WHEN opponents_wins is NULL then 0 ELSE opponents_wins END 
            from v_tournament_points vtp 
            left join v_players_opponents_wins vpow on vtp.id=vpow.player and vtp.tournament_id=vpow.tournament_id 
            order by points desc, opponents_wins desc;

