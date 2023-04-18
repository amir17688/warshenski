"""tournament.py: Swiss-Style Tournament Management."""


import psycopg2
import random
from tabulate import tabulate


class DB:

    def __init__(self, db_con_str="dbname=tournament"):
        """Create database connection with connection string provided
           db_con_str: contains the connetion string"""
        self.conn = psycopg2.connect(db_con_str)

    def cursor(self):
        """Returns the current cursor of the database"""
        return self.conn.cursor()

    def execute(self, sql_query_string, and_close=False):
        """Executes SQL queries.
           sql_query_string: the query string to be executed
           and_close: if true, close the database connection after executing"""

        cursor = self.cursor()
        cursor.execute(sql_query_string)
        if and_close:
            self.conn.commit()
            self.close()
        return {"conn": self.conn, "cursor": cursor if not and_close else None}

    def close(self):
        """Closes the current database connection"""
        return self.conn.close()


def registerGame(game_desc):
    """ Registers a game in the database."""

    SQL = """INSERT INTO games (gamedesc) VALUES ('%s');"""
    data = (game_desc, )
    DB().execute((SQL % data), True)


def registerTournament(tournament_desc, game_id):
    """ Registers a tournament in the database."""
    
    SQL = """INSERT INTO tournaments
             (tournamentdesc, gameid)
             VALUES ('%s', %s::integer);"""
    data = (tournament_desc, game_id)
    DB().execute((SQL % data), True)


def returnRoundCount(tournament_id):
    """Return the number of rounds required to identify a win"""

    SQL = """SELECT roundcount FROM tournaments
             WHERE tournamentid = (%s::integer);"""
    data = (tournament_id, )
    conn = DB().execute((SQL % data), False)
    roundcount = conn["cursor"].fetchone()

    return int(roundcount[0])


def registerPlayer(first_name, last_name):
    """ Insert the player into the players tables."""

    SQL = """INSERT INTO players (firstname, lastname)
             VALUES ('%s', '%s');"""
    data = (first_name.replace("'", ""), last_name.replace("'", ""))
    DB().execute((SQL % data), True)


def deletePlayers():
    """ Clear our all the player records from the database. """

    SQL = """TRUNCATE players CASCADE;"""
    DB().execute(SQL, True)


def countPlayers():
    """ Return the number of players in the database."""

    SQL = """SELECT COUNT(1) FROM players;"""
    conn = DB().execute(SQL, False)
    c = conn["cursor"].fetchone()[0]

    return int(c)


def returnPlayerID(lastname):
    """ Return the player ID for a given last name"""

    SQL = """SELECT playerid FROM players
             WHERE lastname = ('%s');"""
    data = (lastname.replace("'", ""), )
    conn = DB().execute((SQL % data), False)
    playerID = conn["cursor"].fetchone()

    return int(playerID[0])


def registerTournamentPlayer(tournament_id, player_id):
    ''' Add a player to a tournament '''

    SQL = """INSERT INTO tournplayer (tournamentid, playerid)
             VALUES (%s::integer, %s::integer)"""
    data = (tournament_id, player_id)
    DB().execute((SQL % data), True)

    deleteMatches()
    insertMatches(tournament_id)


def deleteTournamentPlayer():
    ''' Delete a player to a tournament '''

    tournament_id = raw_input("Enter tournament ID: ")
    player_id = raw_input("Enter player ID: ")

    SQL = """DELETE FROM tournplayer
             WHERE tournamentid = (%s::integer)
             AND playerid = (%s::integer)"""
    data = (tournament_id, player_id)
    DB().execute((SQL % data), True)


def insertMatches(tournament_id):
    """Insert the base matches for the rounds in matches"""

    SQL = """SELECT fn_insertrounds(%s)"""
    data = (tournament_id,)
    DB().execute((SQL % data), True)


def playerStandings(tournament_id):
    """Return player standings for the final round"""

    round_id = returnRoundCount(tournament_id)

    SQL = """SELECT a.playerid, a.playername, a.wincount, a.matchcount
             FROM playerstandings AS a
             WHERE a.tournamentid = (%s::integer)
             AND round = (%s::integer)
             ORDER BY a.WinCount;"""
    data = (tournament_id, round_id)
    conn = DB().execute((SQL % data), False)
    standings = conn["cursor"].fetchall()

    return standings


def playerStandingsTable(tournament_id, round_id):
    """Return player standings for the final round in table format"""

    SQL = """SELECT * FROM playerstandings AS a
             WHERE a.tournamentid = (%s::integer)
             AND round = (%s::integer)
             ORDER BY a.rank_id;"""
    data = (tournament_id, round_id)
    conn = DB().execute((SQL % data), False)
    standings = conn["cursor"].fetchall()

    print tabulate(standings, headers=(['Tourn ID', 'Tournament',
                                        'PlayerID', 'Player', 'Round', 
                                        'Wins', 'Matches', 'Opponent', 'OMW',
                                        'Rank']),
                   tablefmt='orgtbl')


def deleteMatches():
    """Delete all matches for a specific tournament."""

    SQL = """DELETE FROM matches;"""
    DB().execute(SQL, True)


def firstRound(tournament_id):
    """Create the first round matching, including bye"""

    SQL = """DROP TABLE IF EXISTS tmp_roundpair;
             SELECT row_number() over() as rownum, *
             INTO TABLE tmp_roundpair
             FROM tournplayer AS a
             WHERE a.tournamentid = (%s);"""
    data = (tournament_id, )
    DB().execute((SQL % data), True)

    SQL = """SELECT a.playercount
             FROM tournaments AS a
             WHERE a.tournamentid = (%s);"""
    conn = DB().execute((SQL % data), False)
    players = conn["cursor"].fetchone()

    SQL = """SELECT MAX(matchnum)
             FROM matches AS a
             WHERE a.tournamentid = (%s)
             AND a.round = 1;"""
    data = (tournament_id, )
    conn = DB().execute((SQL % data), False)
    matches = conn["cursor"].fetchone()


    if int(players[0]) % 2 == 0:
        for match in range(1, int(matches[0])+1):
            SQL = """SELECT first_round_player(%s, 1, %s);"""
            data = (tournament_id, match)
            DB().execute((SQL % data), True)
    else:
        SQL = """SELECT round_bye_player(%s, 1, %s);"""
        data = (tournament_id, int(matches[0]))
        DB().execute((SQL % data), True)

        for match in range(1, int(matches[0])):
            SQL = """SELECT first_round_player(%s, 1, %s);"""
            data = (tournament_id, match)
            DB().execute((SQL % data), True)


def subsequentRound(tournament_id, round_id):
    """Create the subsequent round matching, including bye"""

    SQL = """SELECT a.playercount
             FROM tournaments AS a
             WHERE a.tournamentid = (%s);"""
    data = (tournament_id, )
    conn = DB().execute((SQL % data), False)
    players = conn["cursor"].fetchone()

    SQL = """SELECT MAX(matchnum)
             FROM matches AS a
             WHERE a.tournamentid = (%s)
             AND a.round = 1;"""
    data = (tournament_id, )
    conn = DB().execute((SQL % data), False)
    matches = conn["cursor"].fetchone()

    if int(players[0]) % 2 == 0:
        SQL = """SELECT a.rank_id, a.playerid
                 FROM playerstandings AS a
                 WHERE tournamentid = (%s)
                 AND round = (%s);"""
        data = (tournament_id, int(round_id)-1)
        conn = DB().execute((SQL % data), False)
        pairings = conn["cursor"].fetchall()

        match = 1

        for player in range(0, len(pairings), 2):
            SQL = """SELECT round_player(%s, %s, %s, %s, %s);"""
            data = (tournament_id, round_id, match,
                    pairings[player][1],
                    pairings[player+1][1])
            match += 1
            DB().execute((SQL % data), True)
    else:
        SQL = """DROP TABLE IF EXISTS tmp_roundpair;
                 SELECT row_number() over() rownum, *
                 INTO tmp_roundpair
                 FROM tournplayer AS a
                 WHERE a.tournamentid = (%s)
                 AND a.playerid NOT IN (
                 SELECT playerone
                 FROM byesplayed
                 WHERE tournamentid = (%s)); """
        data = (tournament_id, tournament_id)
        DB().execute((SQL % data), True)

        SQL = """SELECT round_bye_player(%s,
                 %s, %s);"""
        data = (tournament_id, round_id, int(matches[0]))
        DB().execute((SQL % data), True)

        SQL = """SELECT a.rank_id, a.playerid
                 FROM playerstandings AS a
                 WHERE tournamentid = (%s)
                 AND round = (%s)
                 AND a.playerid <> (SELECT playerone FROM matches
                 WHERE tournamentid = (%s)
                 AND round = (%s)
                 AND playerone = playertwo);"""
        data = (tournament_id, int(round_id)-1, tournament_id, round_id)
        conn = DB().execute((SQL % data), False)
        pairings = conn["cursor"].fetchall()

        match = 1

        for player in range(0, len(pairings), 2):
            SQL = """SELECT round_player(%s, %s, %s, %s, %s);"""
            data = (tournament_id, round_id, match, pairings[player][1],
                    pairings[player+1][1])
            match += 1
            DB().execute((SQL % data), True)


def randomScore(tournament_id, round_id):
    """Generate random scores for matches in a tournament round."""

    SQL = """SELECT MAX(matchnum)
             FROM matches AS a
             WHERE a.tournamentid = (%s::integer)
             AND a.round = (%s::integer)
             AND playeronescore is null;"""
    data = (tournament_id, round_id)
    conn = DB().execute((SQL % data), False)
    matches = conn["cursor"].fetchone()

    for match in range(1, int(matches[0])+1):
        SQL = """SELECT random_score(%s::integer, %s::integer, %s::integer);"""
        data = (tournament_id, round_id, match)
        DB().execute((SQL % data), True)


def reportMatch(tournament_id, round_id, match_id, winner, loser):
    """Stores the outcome of a match between two players in the database"""

    SQL = """UPDATE matches
             SET playeronescore = 1, playertwoscore = 0,
             playerone = (%s::integer), playertwo = (%s::integer)
             WHERE tournamentid = (%s::integer)
             AND round = (%s::integer)
             AND matchnum = (%s::integer)
             AND (playerone = (%s::integer) OR playerone = (%s::integer))
             AND (playertwo = (%s::integer) OR playertwo = (%s::integer));"""
    data = (winner, loser, tournament_id, round_id, match_id, winner,
            loser, winner, loser)
    DB().execute((SQL % data), True)


def swissPairings(tournament_id, round_id):
    """Return the pairings for each match in the tournament and round."""

    SQL = """SELECT *
             FROM matchpairings AS a
             WHERE a.tournamentid = (%s::integer)
             AND a.round = (%s::integer)
             ORDER BY a.matchnum;"""
    data = (tournament_id, round_id)
    conn = DB().execute((SQL % data), False)
    pairings = conn["cursor"].fetchall()

    return pairings


def swissPairingsTable(tournament_id, round_id):
    """Return the pairings for each match in the tournament and round."""

    SQL = """SELECT *
             FROM matchpairings AS a
             WHERE a.tournamentid = (%s::integer)
             AND a.round = (%s::integer)
             ORDER BY a.matchnum;"""
    data = (tournament_id, round_id)
    conn = DB().execute((SQL % data), False)
    pairings = conn["cursor"].fetchall()

    print tabulate(pairings, headers=(['Tournament', 'Round', 'Match',
                                       'Player One ID', 'Player Two ID',
                                       'Player One', 'Player Two']),
                   tablefmt='orgtbl')


def reportTournaments():
    """Report tournaments in the database."""

    SQL = """SELECT * FROM listtournaments;"""
    conn = DB().execute(SQL, False)
    tournaments = conn["cursor"].fetchall()

    print tabulate(tournaments, headers=(['Game', 'ID', 'Tournament',
                                          'Players', 'Rounds']),
                   tablefmt='orgtbl')


def reportTournamentPlayers():
    """Report tournaments players in the database."""

    SQL = """SELECT * FROM listtournamentplayers;"""
    conn = DB().execute(SQL, False)
    tournaments = conn["cursor"].fetchall()

    print tabulate(tournaments, headers=(['Row', 'ID', 'Tournament',
                                          'Player ID', 'Player']),
                   tablefmt='orgtbl')


def reportPlayers():
    """Report players in the database."""

    SQL = """SELECT * FROM players;"""
    conn = DB().execute(SQL, False)
    tournaments = conn["cursor"].fetchall()

    print tabulate(tournaments, headers=(['ID', 'Player']),
                   tablefmt='orgtbl')

def reportGames():
    """Report games in the database."""

    SQL = """SELECT * FROM games;"""
    conn = DB().execute(SQL, False)
    tournaments = conn["cursor"].fetchall()

    print tabulate(tournaments, headers=(['ID', 'Game']),
                   tablefmt='orgtbl')