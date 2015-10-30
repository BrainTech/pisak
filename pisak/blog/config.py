"""
Module for storing and managing all the blog configuration parameters.
"""
import configobj

from pisak import dirs


"""
Runtime cache of the user password if chosen not to be stored permanently.
"""
PASSWORD = None


CONFIG_PATH = dirs.HOME_MAIN_CONFIG


def get_blog_config():
    """
    Get all the blog configurations.

    :returns: tuple consisting of blog address, user name and user password
    """
    config = configobj.ConfigObj(CONFIG_PATH, encoding='UTF8')['blog']
    return {"url": config["address"],
            "user_name": config["user_name"],
            "password": decrypt_password(config["password"]) or PASSWORD,
            "title": config["title"].upper()}
            # include the below line into the blog config dict in
            # order to get use of the password encryption mode: 
            # decrypt_password(config['password'])


def save_blog_config(address, user_name, title, password=None):
    """
    Save all the blog configurations.

    :param address: URI with the blog address
    :param user_name: user login
    :param title: blog title
    :param password: user password
    """
    config = configobj.ConfigObj(CONFIG_PATH, encoding='UTF8')
    blog_config = config['blog']
    blog_config["address"] = address
    blog_config["user_name"] = user_name
    blog_config["title"] = title
    if password:
        blog_config["password"] = encrypt_password(password)
    config.write()


def decrypt_password(encrypted):
    """
    Decrypt the given encrypted password.
    
    :param encrypted: encrypted password

    :returns: decrypted password
    """
    if isinstance(encrypted, str):
        return "".join([chr(ord(sign)-1) for sign in list(encrypted)[::-1]])


def encrypt_password(password):
    """
    Not very safe solution. Only for people who really are unable to remember
    their password. Anyone who gets here will be able to decrypt
    the password so we do not need to be very inventive.

    :param password: not encrypted password
    """
    return "".join([chr(ord(sign)+1) for sign in list(password)[::-1]])


def get_followed_blogs():
    """
    Get list of all followed blogs.

    :returns: list with all followed blogs
    """
    return list(configobj.ConfigObj(CONFIG_PATH,
            encoding='UTF8')['followed_blogs'].values())