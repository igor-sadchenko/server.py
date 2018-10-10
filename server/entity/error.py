""" Error entity.
"""
from entity.serializable import Serializable


class Error(Serializable):

    def __init__(self, exception=None):
        self.error = str(exception) if exception is not None else ''

    def __repr__(self):
        return '<Error(error={})>'.format(self.error)
