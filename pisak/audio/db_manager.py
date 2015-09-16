import os

from sqlalchemy import Table, Column, Integer, String, Boolean, MetaData, \
    ForeignKey, select, func, create_engine

from pisak import dirs, logger


_LOG = logger.get_logger(__name__)


metadata = MetaData()


folders = Table('folders', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String, unique=True, nullable=False),
        Column('cover_path', String, nullable=True)
)


tracks = Table('tracks', metadata,
        Column('id', Integer, primary_key=True),
        Column('path', String, unique=True, nullable=False),
        Column('title', String, nullable=False),
        Column('no', Integer, nullable=True),
        Column('year', Integer, nullable=True),
        Column('cover_path', String, nullable=True),
        Column('album', String, nullable=True),
        Column('genre', String, nullable=True),
        Column('artist', String, nullable=True),
        Column('favourite', Boolean, default=False),
        Column('folder_id', Integer, ForeignKey("folders.id"), nullable=True)
)


_FAVOURITES_FOLDER_ALIAS = "ULUBIONE"

_MUSIC_DB_PATH = os.path.join(dirs.HOME_PISAK_DIR, "music.db")

_ENGINE_URL = "sqlite:///" + _MUSIC_DB_PATH


engine = create_engine(_ENGINE_URL)

metadata.create_all(engine)


def get_folder_count():
    """
    Get number of folders.
    """
    conn = engine.connect()
    favs = 1 if conn.execute(select([tracks]).where(tracks.c.favourite)).fetchone() else 0
    count = len(conn.execute(select([folders])).fetchall()) + favs
    conn.close()
    return count


def get_all_folders():
    """
    Get all available folders.
    """
    conn = engine.connect()
    folders_list = conn.execute(select([folders])).fetchall()
    for folder in folders_list:
        if not conn.execute(select([tracks]).where(tracks.c.folder_id == folder['id'])).fetchone():
            conn.execute(folders.delete().where(folders.c.id == folder['id']))
            folders_list.remove(folder)
    _include_fake_favourites_folder(conn, folders_list)
    conn.close()
    return folders_list


def _include_fake_favourites_folder(conn, folders_list):
    sample_fav = conn.execute(select([tracks.c.cover_path]).where(
        tracks.c.favourite)).fetchone()
    if sample_fav:
        folders_list.append({'id': -1,
                             'name': _FAVOURITES_FOLDER_ALIAS,
                             'cover_path': sample_fav['cover_path']})


def get_tracks_from_folder(folder_id):
    """
    Get tracks from the folder with the given index.

    :param folder_id: index of the folder, -1 for the favourites folder.
    """
    conn = engine.connect()
    if _is_folder(conn, folder_id):
        ret = conn.execute(select([tracks]).where(
            tracks.c.folder_id == folder_id).order_by(tracks.c.no)).fetchall()
    else:
        ret = _get_favourite_tracks(conn)
    conn.close()
    return ret


def _is_folder(conn, folder_id):
    return conn.execute(select([folders]).where(folders.c.id == folder_id)).fetchone()


def _get_favourite_tracks(conn):
    return conn.execute(select([tracks]).where(tracks.c.favourite)).fetchall()


def is_track_in_favourites(track_path):
    """
    Check if track with the given path is in the favourites

    :param path: path to the track
    """
    return engine.execute(select([tracks.c.favourite]).where(
        tracks.c.path == track_path)).fetchone()['favourite']


def remove_track_from_favourites(track_path):
    """
    Remove track with the given path from the favourites

    :param path: path to the track
    """
    _toggle_favourite(track_path, False)


def add_track_to_favourites(track_path):
    """
    Add track with the given path to the favourites

    :param path: path to the track
    """
    _toggle_favourite(track_path, True)


def _toggle_favourite(track_path, boolean):
    engine.execute(tracks.update().where(tracks.c.path == track_path).values(favourite=boolean))


class DBLoader:
    """
    Use this to update the music library.
    """

    def __init__(self):
        self._conn = engine.connect()
        self._collect_garbage()

    def _execute(self, *args, **kwargs):
        try:
            return self._conn.execute(*args, **kwargs)
        except Exception as exc:
            _LOG.error(exc)

    def _collect_garbage(self):
        """
        Clear the db from all the non existing files.
        """
        for track in self._execute(select([tracks])).fetchall():
            if not os.path.isfile(track['path']):
                self._execute(
                    tracks.delete().where(tracks.c.id == track['id']))

    def insert_many_tracks(self, tracks_list):
        """
        Insert many tracks to the db.

        :param tracks_list: list of dictionaries with the tracks.
        """
        self._execute(
            tracks.insert().prefix_with('OR IGNORE'), tracks_list)

    def insert_folder(self, name, cover_path):
        """
        Insert single folder to the db.

        :param name: name of the folder.
        :param cover_path: path to a cover of the given folder.
        """
        ret = self._execute(folders.insert().prefix_with('OR IGNORE'),
                name=name, cover_path=cover_path)
        if ret and ret.inserted_primary_key[0]:
            rowid = ret.inserted_primary_key[0]
        else:
            rowid = self._execute(select([folders.c.id]).where(
                folders.c.name == name)).fetchone()['id']
        return rowid

    def close(self):
        """
        Close the db loader, close any open connections.
        """
        self._conn.close()