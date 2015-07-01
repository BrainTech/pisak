"""
Module for managing database with music collection.
"""
import os.path
from contextlib import contextmanager

from sqlalchemy import Column, String, Table, ForeignKey, Integer, DateTime, \
     create_engine
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from pisak import res
from pisak.libs import dirs



_FAVOURITES_FOLDER_ALIAS = "ULUBIONE"

_MUSIC_DB_PATH = os.path.join(dirs.HOME_PISAK_DIR, "music.db")

_ENGINE_URL = "sqlite:///" + _MUSIC_DB_PATH


_Base = declarative_base()


class Folder(_Base):
    __tablename__ = "folders"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    tracks = orm.relationship("Track", backref="parent_folder",
                              cascade="all, delete, delete-orphan")


class Track(_Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True)
    title = Column(String)
    no = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    cover_path = Column(String, nullable=True)
    album = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    artist = Column(String, nullable=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)


class FavouriteTrack(_Base):
    __tablename__ = "favourite_tracks"
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"))
    track = orm.relationship("Track", uselist=False,
                             foreign_keys="FavouriteTrack.track_id",
                             single_parent=True,
                             backref=orm.backref("favourite",
                                                cascade="all, delete"))


@contextmanager
def _establish_session():
    engine = create_engine(_ENGINE_URL)
    _Base.metadata.create_all(engine)
    session = orm.sessionmaker(autoflush=False)
    session.configure(bind=engine)
    db_session = session()
    try:
        yield db_session
        db_session.commit()
    except:
        db_session.rollback()
        raise
    finally:
        db_session.close()


def collect_garbage():
    """
    Clear the db from all the non existing files.
    """
    with _establish_session() as sess:
        for track in sess.query(Track).all():
            if not os.path.isfile(track.path):
                sess.delete(track)

def get_all_folders_with_covers():
    """
    Get all avalaible folders with corresponding images.
    """
    pack = []
    with _establish_session() as sess:
        for folder in sess.query(Folder).all():
            tracks = folder.tracks
            if len(tracks) == 0:
                sess.delete(folder)
            else:
                cover = tracks[0].cover_path
                if cover is not None and not os.path.isfile(cover):
                    cover = None
                pack.append([folder, cover])
        _include_fake_favourites_folder(sess, pack)
        sess.expunge_all()
    return pack


def _include_fake_favourites_folder(sess, pack):
    favs = Folder(id=len(pack)+1, name=_FAVOURITES_FOLDER_ALIAS)
    favs.tracks.extend([fav.track for fav in sess.query(FavouriteTrack).all()])
    if len(favs.tracks) > 0:
        pack.append([favs, favs.tracks[0].cover_path])


def get_tracks_from_folder(folder_id):
    """
    Get tracks from the folder with the given index.

    :param folder_id: index of the folder
    """
    with _establish_session() as sess:
        if folder_id <= len(sess.query(Folder).all()):
            tracks = sess.query(Folder).filter(
                Folder.id == folder_id).first().tracks
        else:
            tracks = []
            _get_favourite_tracks(sess, tracks)
        sess.expunge_all()
    return sorted(tracks, key=lambda track: track.no)


def _get_favourite_tracks(sess, pack):
    pack.extend([fav.track for fav in sess.query(FavouriteTrack).all()])


def is_track_in_favourites(path):
    """
    Check if track with the given path is in the favourites

    :param path: path to the track
    """
    with _establish_session() as sess:
        return path in [
            fav.track.path for fav in sess.query(FavouriteTrack).all()]


def add_track_to_favourites(path):
    """
    Add track with the given path to the favourites

    :param path: path to the track
    """
    with _establish_session() as sess:
        track = sess.query(Track).filter(Track.path == path).first()
        if track:
            sess.add(FavouriteTrack(track=track))


def remove_track_from_favourites(path):
    """
    Remove track with the given path from the favourites

    :param path: path to the track
    """
    with _establish_session() as sess:
        track = sess.query(Track).filter(Track.path == path).first()
        if track:
            sess.query(FavouriteTrack).filter(
                FavouriteTrack.track == track).delete()


def insert_folder_tree(tree_desc):
    """
    Add the whole construction consisting of folders and tracks they contain.

    :param tree_desc: dictionary where keys are folder names and values
    are lists containing track description. List consists of track title,
    path, number of an album, date of release and path to an related image.
    """
    with _establish_session() as sess:
        for folder_name in tree_desc.keys():
            folder = sess.query(Folder).filter(
                Folder.name == folder_name).first()
            if not folder:
                folder = Folder(name=folder_name)
                sess.add(folder)
            for track_desc in tree_desc[folder_name]:
                track = sess.query(Track).filter(Track.path == track_desc[1]).first()
                if not track:
                    track = Track(title=track_desc[0], path=track_desc[1],
                                  no=track_desc[2], year=track_desc[3],
                                  cover_path=track_desc[4], album=track_desc[5],
                                  artist=track_desc[6], genre=track_desc[7])
                    sess.add(track)
                folder.tracks.append(track)
