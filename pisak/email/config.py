"""
Email settings.
"""
import os
import configobj

from pisak import logger, exceptions, dirs


_LOG = logger.get_logger(__name__)


class EmailConfigError(exceptions.PisakException):
    pass


class Config:
    """
    Configuration object containing all the email related setup.
    """

    # path to the config file.
    PATH = dirs.HOME_MAIN_CONFIG

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
        for key in ["address", "password", "SMTP_port", "IMAP_port",
                    "SMTP_server", "IMAP_server"]:
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
        self._config = configobj.ConfigObj(self.PATH, encoding='UTF8')['email']

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
        if "sent_folder" not in ret_setup or not ret_setup["sent_folder"]:
            server = ret_setup['address'].split('@')[-1]
            ret_setup["sent_folder"] = \
                self.DEFAULT_SENT_BOX[server] if \
                server in self.DEFAULT_SENT_BOX else \
                self.DEFAULT_SENT_BOX["unknown"]
        return ret_setup

    @staticmethod
    def decrypt_password(encrypted):
        """
        Decrypt the given encrypted password.

        :param encrypted: encrypted password

        :returns: decrypted password
        """
        if isinstance(encrypted, str):
            return "".join([chr(ord(sign)-1) for sign in list(encrypted)[::-1]])

    @staticmethod
    def encrypt_password(password):
        """
        Not very safe solution. Only for people who really are unable to remember
        their password. Anyone who gets here will be able to decrypt
        the password so we do not need to be very inventive.

        param password: not encrypted password
        """
        return "".join([chr(ord(sign)+1) for sign in list(password)[::-1]])
