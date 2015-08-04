from contextlib import contextmanager
from functools import wraps

from sqlalchemy import orm, func, Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

from pisak import logger, exceptions, text_tools, dirs


_LOG = logger.get_logger(__name__)


_DB_ENGINE_URL = "sqlite:///" + dirs.HOME_EMAIL_ADDRESS_BOOK


_Base = declarative_base()


class _Contact(_Base):
    """
    Object representing record in the address book database.
    """
    __tablename__ = "address_book"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    address = Column(String, unique=True)
    photo = Column(String, nullable=True)


@contextmanager
def _establish_db_session():
    engine = create_engine(_DB_ENGINE_URL)
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


def _db_session_handler(func):
    """
    Decorator for handling all the database session operations
    and database API related errors.
    Provides an access to the database to the object that the decorated
    function belongs to, by setting its `sess` field with the database
    session instance.

    :param func: function to be decorated.
    """
    @wraps(func)
    def wrapper(obj, *args, **kwargs):
        try:
            with _establish_db_session() as obj.sess:
                ret = func(obj, *args, **kwargs)
            obj.sess = None
            return ret
        except SQLAlchemyError as exc:
            raise AddressBookError(exc) from exc
    return wrapper


class AddressBookError(exceptions.PisakException):
    pass


class AddressBook(text_tools.Predictor):
    """
    Book of mail contacts. Serves also as a predictor
    for new message address inserts.
    Internally, the entire address book content is stored
    inside a database. Database session instance that is used by some of the
    methods, each time is provided to them by the '_db_session_handler'
    decorator. After executing one of these methods all changes
    made to the session  are commited and the session is closed.
    """
    __gtype_name__ = "PisakEmailAddressBook"

    def __init__(self):
        super().__init__()
        self.sess = None  # database session instance
        self.basic_content = self._book_lookup()
        self.apply_props()

    def do_prediction(self, text, position):
        """
        Implementation of the `text_tools.Predictor` method.
        """
        feed = text[0 : position]
        self.content = self._book_lookup(feed)
        self.notify_content_update()

    @_db_session_handler
    def get_contact(self, contact_id):
        """
        Get single contact from the address book.

        :param contact_id: identification number of a contact that should
        be returned.

        :returns: single instance of a `_Contact` with the given id or None if
        there was no match.
        """
        contact = self.sess.query(_Contact).filter(
            _Contact.id == contact_id).first()
        self.sess.expunge_all()
        return contact

    @_db_session_handler
    def get_contact_by_address(self, address):
        """
        As each address in the address book is unique one can
        query for a given contact by its address.

        :param address: address of the contact.

        :return: `_Contact` object with a given address
        or None if nothing found.
        """
        contact = self.sess.query(_Contact).filter(
            _Contact.address == address).first()
        self.sess.expunge_all()
        return contact

    @_db_session_handler
    def get_count(self):
        """
        Get number of contacts in the address book.

        :returns: integer with number of contacts in the address book
        """
        return self.sess.query(func.count(_Contact.id)).scalar()

    @_db_session_handler
    def get_all_contacts(self):
        """
        Retrieve all records from the address book.

        :returns: list of all contacts.
        """
        contacts = self.sess.query(_Contact).all()
        self.sess.expunge_all()
        return contacts

    @_db_session_handler
    def search_contacts(self, feed):
        """
        Look for all the contacts that contain the given feed in their name
        or address, sort them properly and return as a list.

        :param feed: string that the search will be based on.

        :return: list of all the matching contacts, sorted properly.
        """
        contacts = sorted(self.sess.query(_Contact).filter(feed in
            _Contact.address | (_Contact.name & feed in _Contact.name)).all(),
                key=lambda contact: (contact.address if feed in
                    contact.address else contact.name).index(feed))
        self.sess.expunge_all()
        return contacts

    @_db_session_handler
    def add_contact(self, contact):
        """
        Add new contact to the address book. Contact must contain 'address' key
        and can contain the following keys: 'name' and 'photo'.

        :param contact: dictionary with new contact.

        :returns: True on successfull update of the book with the given
        contact or False otherwise, for example when address same as the
        one of the given contact has already been in the book.
        """
        address = contact["address"]
        if not self.sess.query(_Contact).filter(
                        _Contact.address == address).first():
            self.sess.add(
                 _Contact(
                    name=contact.get("name"),
                    address=address,
                    photo=contact.get("photo")))
            return True
        else:
            _LOG.warning(
                "Contact with address {} already in the "
                "address book.".format(address))
            return False

    @_db_session_handler
    def remove_contact(self, contact_id):
        """
        Remove contact from the book. If the book does not contain
        the given contact then nothing happens.

        :param contact: id of the contact to be removed
        """
        contact = self.sess.query(_Contact).filter(
             _Contact.id == contact_id).first()
        if contact:
            self.sess.delete(contact)
        else:
            _LOG.warning("Trying to delete not existing "
                            "contact with id: {}.".format(contact_id))

    def edit_contact_name(self, contact_id, name):
        """
        Edit name of a contact.

        :param contact_id: id of the contact
        :param name: new name
        """
        self._edit_contact(contact_id, "name", name)

    def edit_contact_photo(self, contact_id, photo):
        """
        Edit photo path for a contact.

        :param contact_id: id of the contact
        :param photo: path to the new photo
        """
        self._edit_contact(contact_id, "photo", photo)

    def edit_contact_address(self, contact_id, address):
        """
        Edit email address of a contact.

        :param contact_id: id of the contact
        :param name: new email address
        """
        self._edit_contact(contact_id, "address", address)

    @_db_session_handler
    def _edit_contact(self, contact_id, key, value):
        contact = self.sess.query(_Contact).filter(
             _Contact.id == contact_id).first()
        if contact:
            setattr(contact, key, value)

    @_db_session_handler
    def _book_lookup(self, feed=""):
        match = self.sess.query(_Contact.address).filter(
             _Contact.address.startswith(feed) |
            (_Contact.name & _Contact.name.startswith(feed))).order_by(
            _Contact.address).all()
        self.sess.expunge_all()
        return match
