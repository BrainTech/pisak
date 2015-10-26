def test():
    """
    Test provided blog settings or server connection.
    """
    from pisak.blog.wordpress import _OwnBlog

    ERRORS = {
        0: 'Brak połączenia z internetem.',
        1: 'Blog nie istnieje. Jeśli chcesz założyć swojego bloga skontaktuj się z obsługą techniczną.'
    }

    try:
        dummy_blog = _OwnBlog()
    except:
        pass