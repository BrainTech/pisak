"""
Email settings.
"""
import os
import configobj

from pisak import logger, exceptions
from pisak.libs import dirs


_LOG = logger.get_logger(__name__)


class EmailConfigError(exceptions.PisakException):
    pass


class Config:
    """
    Configuration object containing all the email related setup.
    """

    # path to the config file.
    PATH = dirs.HOME_EMAIL_SETUP

    # default sent box names for different providers of the email service.
    DEFAULT_SENT_BOX = {
        "unknown": "Sent",
        "gmail.com": "[Gmail]/Wa&AXw-ne"
    }

    def __init__(self):
        self._config = None
        self._load_config()

    def _validate_config(self):
        """
        Validate config content. Check if all the required keys exist.
        """
        for key in ["server_address", "user_address",
                    "password", "port_out", "port_in"]:
            if key not in self._config:
                raise AssertionError(
                    "No '{}' key in the email configuration file.".format(key))

    def _load_config(self):
        """
        Load the email configuration file from a proper directory.
        If the file does not exist raise `FileNotFoundError`.
        """
        if not os.path.isfile(self.PATH):
            msg = "No email configuration file. " \
                  "Such file should be here:  {}.".format(self.PATH)
            _LOG.critical(msg)
            raise FileNotFoundError(msg)
        self._config = configobj.ConfigObj(self.PATH, encoding='UTF8')

    def get_account_setup(self):
        """
        Get previously saved email account settings. If the configuration
        object's content is not valid raise `EmailConfigError`.

        :returns: config object with email settings.
        """
        try:
            self._validate_config()
        except AssertionError as exc:
            raise EmailConfigError(exc) from exc
        ret_setup = self._config.copy()
        if "sent_box_name" not in ret_setup or not ret_setup["sent_box_name"]:
            ret_setup["sent_box_name"] = \
                self.DEFAULT_SENT_BOX[ret_setup["server_address"]] if \
                ret_setup["server_address"] in self.DEFAULT_SENT_BOX else \
                self.DEFAULT_SENT_BOX["unknown"]
        return ret_setup

    def save_account_setup(self, server_address, user_address, password, sent_box_name,
                           port_out=587, port_in=993, keyfile=None, certfile=None):
        """
        Save server and email account settings to a file.

        :param server_address: address of the server that the email account is on.
        :param user_address: user address for the email account.
        :param password: password to the email account.
        :param sent_box_name: name of the mailbox for sent messages specific for
        a given email service provider.
        :param port_out: port used for outcoming mail.
        :param port_in: port used for incoming mail.
        :param keyfile: path to the file containing key.
        :param certfile: path to the file containing certificate.
        """
        self._config["server_address"] = server_address
        self._config["user_address"] = user_address
        self._config["password"] = encrypt_password(password)
        self._config["sent_box_name"] = sent_box_name
        self._config["port_out"] = port_out
        self._config["port_in"] = port_in
        if keyfile:
            self._config["keyfile"] = keyfile
        if certfile:
            self._config["certfile"] = certfile
        self._config.write()

    def decrypt_password(self, encrypted):
        """
        Decrypt the given encrypted password.

        :param encrypted: encrypted password

        :returns: decrypted password
        """
        if isinstance(encrypted, str):
            return "".join([chr(ord(sign)-1) for sign in list(encrypted)[::-1]])

    def encrypt_password(self, password):
        """
        Not very safe solution. Only for people who really are unable to remember
        their password. Anyone who gets here will be able to decrypt
        the password so we do not need to be very inventive.

        param password: not encrypted password
        """
        return "".join([chr(ord(sign)+1) for sign in list(password)[::-1]])
