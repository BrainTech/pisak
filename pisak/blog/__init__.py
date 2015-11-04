def test(config):
    """
    Test provided blog settings or server connection.
    """
    from pisak.loc import BLOG_MESSAGES as MESSAGES
    from pisak.blog.wordpress import _OwnBlog
    from pisak.blog import exceptions

    try:
        dummy_blog = _OwnBlog(config)
    except exceptions.BlogInternetError:
        ret = False, MESSAGES['no_internet']
    except exceptions.BlogAuthenticationError:
        ret = False, MESSAGES['invalid_credentials']
    except Exception:
        ret = False, MESSAGES['unknown']
    else:
        ret = True, MESSAGES['success']
    return ret