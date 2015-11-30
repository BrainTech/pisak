"""
Module for managing text documents created with speller application and
database dedicated to them.
"""
import os
from contextlib import contextmanager

from sqlalchemy import Column, DateTime, String, Integer, func, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from pisak import res, dirs


#: Path to system's default documents directory
DOCUMENTS_DIR = dirs.get_user_dir("documents")


#: Common base for text documents' files' names
FILE_NAME_BASE = "text_file_no_"


#: Extension of files' names
FILE_NAME_EXTENSION = ".txt"


#: Path to database related to text documents
DOCUMENTS_DB_PATH = dirs.HOME_TEXT_DOCUMENTS_DB


#: String constant for sqlalchemy internal purposes
_ENGINE_URL = "sqlite:///" + DOCUMENTS_DB_PATH


#: Declarative base class for sqlalchemy classes definitions
_Base = declarative_base()


def get_all_documents():
    """
    Return all records from the database which are pointing to the
    existing files in the files' system.
    """
    with _establish_session() as sess:
        documents = sess.query(Document).all()
        sess.expunge_all()
    for item in documents:
        if not os.path.exists(item.path):
            remove_document(item.path)
            documents.remove(item)
    return documents


def remove_document(path):
    """
    Remove record from the datatabse pointing to the not existing file.

    :param path: path column of the requested to delete record.
    """
    with _establish_session() as sess:
        sess.query(Document).filter(Document.path == path).delete()


def add_document(name, path):
    """
    Insert new document related record to the database.
    Return path in the file system to the new document.

    :param name: name of the new document.

    :param path: path to the new document.
    """
    if not is_in_database(path):
        with _establish_session() as sess:
            sess.add(Document(path=path, name=name))


def is_in_database(path):
    """
    Check if document with the given path is already in the database.

    :param path: path to the document file.

    :return: boolean.
    """
    with _establish_session() as sess:
        document = sess.query(Document).filter(Document.path == path).first()
    if document:
        return True
    else:
        return False


def generate_new_path():
    """
    Generate path for the new document file.

    :return: path for a text document.
    """
    with _establish_session() as sess:
        file_no = sess.query(Document).count()
    file_name = FILE_NAME_BASE + str(file_no) + FILE_NAME_EXTENSION
    while os.path.exists(os.path.join(DOCUMENTS_DIR, file_name)):
        file_no += 1
        file_name = FILE_NAME_BASE + str(file_no) + FILE_NAME_EXTENSION
    return os.path.join(DOCUMENTS_DIR, file_name)


@contextmanager
def _establish_session():
    engine = create_engine(_ENGINE_URL)
    _Base.metadata.create_all(engine)
    session = sessionmaker(autoflush=False)
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


class Document(_Base):
    """
    Class representing a row in the documents table in the database.
    """
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    added_on = Column(DateTime, nullable=False, default=func.now())
