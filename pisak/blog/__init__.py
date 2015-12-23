REQUEST_TIMEOUT = 5  # web request duration limit in seconds


def test(config):
    """
    Test provided blog settings or server connection.
    """
    import socket

    from pisak.loc import BLOG_MESSAGES as MESSAGES
    from pisak.blog.wordpress import _OwnBlog
    from pisak.blog import exceptions

    socket.setdefaulttimeout(5)

    try:
        _OwnBlog(config)
    except (socket.timeout, exceptions.BlogInternetError):
        ret = False, MESSAGES['no_internet']
    except exceptions.BlogAuthenticationError:
        ret = False, MESSAGES['invalid_credentials']
    except Exception:
        ret = False, MESSAGES['unknown']
    else:
        ret = True, MESSAGES['success']

    socket.setdefaulttimeout(None)

    return ret