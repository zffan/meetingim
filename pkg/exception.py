# coding: utf-8


class ParseDocumentError(Exception):
    pass


class SomethingError(Exception):
    pass


class MyRequestError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class DatabaseError(Exception):
    pass


class RFExecuteError(Exception):
    pass
