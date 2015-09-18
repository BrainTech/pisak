import os

from sqlalchemy import Table, Column, Integer, String, Boolean, MetaData, \
    ForeignKey, select, create_engine
from sqlalchemy.exc import SQLAlchemyError

from pisak import dirs, logger


_FAVOURITES_FOLDER_ALIAS = 'ULUBIONE'

_MUSIC_DB_PATH = os.path.join(dirs.HOME_PISAK_DIR, 'music.db')

_ENGINE_URL = 'sqlite:///' + _MUSIC_DB_PATH

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
        Column('folder_id', Integer, ForeignKey('folders.id'), nullable=True)
)


engine = create_engine(_ENGINE_URL)

metadata.create_all(engine)


class DBConnector:
    """
    Database connector.
    """

    def __init__(self):
        self._conn = None

    def _execute(self, *args, **kwargs):
        try:
            if not self._conn:
                self._conn = engine.connect()
            return self._conn.execute(*args, **kwargs)
        except SQLAlchemyError as exc:
            _LOG.error(exc)

    def _close_connection(self):
        if self._conn:
            try:
                self._conn.close()
                self._conn = None
            except SQLAlchemyError as exc:
                _LOG.error(exc)

    def get_folder_count(self):
        """
        Get number of folders.

        :return: integer, number of folders.
        """
        favs = 1 if self._execute(select([tracks]).where(
            tracks.c.favourite)).fetchone() else 0
        count = len(self._execute(select([folders])).fetchall()) + favs
        self._close_connection()
        return count

    def get_folders_ids(self):
        """
        Get list of ids of all the folders from the database.

        :return: list of ids of all the folders,
        including -1 for fake favourites if there are any favourite tracks.
        """
        ids = [row['id'] for row in
               self._execute(select([folders.c.id])).fetchall()]
        if self._execute(select([tracks]).where(
                tracks.c.favourite)).fetchone():
            ids.insert(0, -1)  # for fake favourites folder
        self._close_connection()
        return ids

    def get_all_folders(self):
        """
        Get all available folders.

        :return: list of all folders.
        """
        folders_list = self._execute(select([folders])).fetchall()
        for folder in folders_list:
            if not self._execute(select([tracks]).where(
                    tracks.c.folder_id == folder['id'])).fetchone():
                self._execute(folders.delete().where(
                    folders.c.id == folder['id']))
                folders_list.remove(folder)
        self._include_fake_favourites_folder(folders_list)
        self._close_connection()
        return folders_list

    def _include_fake_favourites_folder(self, folders_list):
        sample_fav = self._execute(select([tracks.c.cover_path]).where(
            tracks.c.favourite)).fetchone()
        if sample_fav:
            folders_list.append({'id': -1,
                                 'name': _FAVOURITES_FOLDER_ALIAS,
                                 'cover_path': sample_fav['cover_path']})

    def get_tracks_from_folder(self, folder_id):
        """
        Get tracks from the folder with the given index.

        :param folder_id: index of the folder, -1 for the favourites folder.

        :return: list of tracks.
        """
        if self._is_folder(folder_id):
            ret = self._execute(select([tracks]).where(
                tracks.c.folder_id == folder_id).order_by(tracks.c.no)).fetchall()
        else:
            ret = self._get_favourite_tracks()
        self._close_connection()
        return ret

    def _is_folder(self, folder_id):
        return self._execute(select([folders]).where(
            folders.c.id == folder_id)).fetchone()

    def _get_favourite_tracks(self):
        return self._execute(select([tracks]).where(tracks.c.favourite)).fetchall()

    def is_track_in_favourites(self, track_path):
        """
        Check if track with the given path is in the favourites

        :param track_path: path to the track.

        :return: True or False.
        """
        ret = self._execute(select([tracks.c.favourite]).where(
            tracks.c.path == track_path)).fetchone()['favourite']
        self._close_connection()
        return ret

    def remove_track_from_favourites(self, track_path):
        """
        Remove track with the given path from the favourites

        :param track_path: path to the track
        """
        self._toggle_favourite(track_path, False)

    def add_track_to_favourites(self, track_path):
        """
        Add track with the given path to the favourites

        :param track_path: path to the track
        """
        self._toggle_favourite(track_path, True)

    def _toggle_favourite(self, track_path, boolean):
        self._execute(tracks.update().where(
            tracks.c.path == track_path).values(favourite=boolean))
        self._close_connection()


class DBLoader(DBConnector):
    """
    Use this to update the music library.
    Use `close` method when done.
    """

    def __init__(self):
        super().__init__()
        self._collect_garbage()

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
        self._close_connection()
