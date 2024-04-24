"""Shared exception. Here because I want to have one root exception type"""


class PIMSError(Exception):
    pass


class PIMSClientError(PIMSError):
    pass


class InvalidPseudonymTemplateError(PIMSClientError):
    pass


class TypedKeyFactoryError(PIMSClientError):
    pass
