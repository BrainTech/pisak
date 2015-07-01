from pisak import exceptions


class BlogInternetError(exceptions.PisakException):
    pass


class BlogAuthenticationError(exceptions.PisakException):
    pass


class BlogMethodError(exceptions.PisakException):
    pass
