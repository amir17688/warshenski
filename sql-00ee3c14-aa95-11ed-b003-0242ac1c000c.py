"""This module is the playlist repository in charge of all database requests."""


def retrieve_playlists(db):
    db.execute('SELECT id, name from playlist;')
    rows = db.fetchall()
    return rows


def retrieve_playlist_by_id(id, db):
    db.execute(
        "SELECT id, name, video_position from playlist WHERE id={id};".format(id=id))
    row = db.fetchone()
    return row


def delete_playlist(id, db):
    db.execute("DELETE FROM playlist where id={id};".format(id=id))


def update_playlist(id, name, db):
    db.execute(
        "UPDATE playlist SET name='{name}' WHERE id={id};".format(name=name, id=id))


def update_playlist_video_position(id, position, db):
    db.execute(
        "UPDATE playlist SET video_position='{position}' WHERE id={id};".format(position=position, id=id))


def create_playlist(name, db):
    db.execute(
        "INSERT INTO playlist (name, video_position) VALUES('{name}', 0);".format(name=name))
