

from builtins import str
from builtins import object
import stringtemplate3


def isiterable(o):
    """
    Like any other iterable except for not considering strings and templates as iterables
    """
    if isinstance(o, (str, stringtemplate3.StringTemplate)):
        return False

    try:
        iter(o)
    except TypeError:
        return False
    else:
        return True


def convertAnyCollectionToList(obj):
    list_ = None
    if isinstance(obj, list):
        list_ = obj
    elif isinstance(obj, tuple) or isinstance(obj, set):
        list_ = list(obj)
    elif isinstance(obj, dict):
        list_ = list(obj.values())
    elif isinstance(obj, CatList):
        list_ = list(obj)
    if not list_:
        return obj
    return list_


def convertAnythingToList(obj):
    list_ = None
    if isinstance(obj, list):
        list_ = obj
    elif isinstance(obj, tuple) or isinstance(obj, set):
        list_ = list(obj)
    elif isinstance(obj, dict):
        list_ = list(obj.values())
    elif isinstance(obj, CatList):
        list_ = []
        for item in obj.lists():
            list_.append(item)
    if not list_:
        return [obj]
    return list_



class CatList(object):
    """ Given a list of lists, yield the combined elements one by one."""

    def __init__(self, lists):
        """ List of elements to cat together """

        self._elements = []
        for attribute in lists:
            self._elements.extend(convertAnythingToList(attribute))

    def __len__(self):
        return len(self._elements)

    def __iter__(self):
        for item in self._elements:
            yield item

    def __str__(self):
        """
        The result of asking for the string of a CatList is the list of
        items and so this is just the concatenated list of both items.
        This is destructive in that
        the iterator cursors have moved to the end after printing.
        """
        return ''.join(str(item) for item in self)

    __repr__ = __str__
