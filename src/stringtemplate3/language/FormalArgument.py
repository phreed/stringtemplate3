# the following represent bit positions emulating a cardinality bitset.
from builtins import str
from builtins import object

OPTIONAL = 1  # a?
REQUIRED = 2  # a
ZERO_OR_MORE = 4  # a*
ONE_OR_MORE = 8  # a+

suffixes = [
    None,
    "?",
    "",
    None,
    "*",
    None,
    None,
    None,
    "+"
]

# When template arguments are not available such as when the user
#  uses "new StringTemplate(...)", then the list of formal arguments
#  must be distinguished from the case where a template can specify
#  args and there just aren't any such as the t() template above.
UNKNOWN_ARGS = {'<unknown>': -1}


def getCardinalityName(cardinality):
    return {
        OPTIONAL: 'optional',
        REQUIRED: 'exactly one',
        ZERO_OR_MORE: 'zero-or-more',
        ONE_OR_MORE: 'one-or-more'
    }.get(cardinality, 'unknown')


class FormalArgument(object):
    """
    Represents the name of a formal argument
    defined in a template:

    group test;
    test(a,b) : "$a$ $b$"
    t() : "blort"

    Each template has a set of these formal arguments or uses
    a placeholder object: UNKNOWN (indicating that no arguments
    were specified such as when a template is loaded from a file.st).

    Note: originally, I tracked cardinality as well as the name of an
    attribute.  I'm leaving the code here as I suspect something may come
    of it later.  Currently, though, cardinality is not used.
    """

    def __init__(self, name, defaultValueST=None):
        self._name = name
        # self._cardinality = REQUIRED
        # # If they specified name="value", store the template here
        #
        self._defaultValueST = defaultValueST

    def __eq__(self, other):
        if not isinstance(other, FormalArgument):
            return False

        if self._name != other._name:
            return False

        # only check if there is a default value; that's all
        if ((self._defaultValueST is not None
             and other._defaultValueST is None) or
                (self._defaultValueST is None
                 and other._defaultValueST is not None)):
            return False

        return True

    def __neq__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        if self._defaultValueST:
            return self._name + '=' + str(self._defaultValueST)
        return self._name

    __repr__ = __str__

    @property
    def defaultValueST(self):
        return self._defaultValueST
