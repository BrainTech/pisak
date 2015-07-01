"""
Module for storing and managing all the blog configuration parameters.
"""
import configobj

from pisak.libs import dirs


"""
Runtime cache of the user password if chosen not to be stored permanently.
"""
PASSWORD = None


def get_blog_config():
    """
    Get all the blog configurations.

    :returns: tuple consisting of blog address, user name and user password
    """
    config = configobj.ConfigObj(dirs.HOME_BLOG_CONFIG, encoding='UTF8')
    return {"url": config.get("address"),
            "user_name": config.get("user_name"),
            "password": config.get("password") or PASSWORD,
            "title": config.get("title").upper()}
            # include the below line into the blog config dict in
            # order to get use of the password encryption mode: 
            #_decrypt_password(config.get("password"))


def save_blog_config(address, user_name, title, password=None):
    """
    Save all the blog configurations.

    :param address: URI with the blog address
    :param user_name: user login
    :param title: blog title
    :param password: user password
    """
    config = configobj.ConfigObj(dirs.HOME_BLOG_CONFIG, encoding='UTF8')
    config["address"] = address
    config["user_name"] = user_name
    config["title"] = title
    if password:
        config["password"] = _encrypt_password(password)
    config.write()


def _decrypt_password(encrypted):
    """
    Decrypt the given encrypted password.
    
    :param encrypted: encrypted password

    :returns: decrypted password
    """
    if isinstance(encrypted, str):
        return "".join([chr(ord(sign)-1) for sign in list(encrypted)[::-1]])


def _encrypt_password(password):
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
    return configobj.ConfigObj(dirs.HOME_FOLLOWED_BLOGS,
                               encoding='UTF8').get("all") or []


def follow_blog(blog_address):
    """
    Add blog to the list of followed blogs.

    :param blog_address: URL to the blog
    """
    store = configobj.ConfigObj(dirs.HOME_FOLLOWED_BLOGS, encoding='UTF8')
    if store.get("all"):
        store["all"].append(blog_address)
    else:
        store["all"] = [blog_address]
    store.write()
