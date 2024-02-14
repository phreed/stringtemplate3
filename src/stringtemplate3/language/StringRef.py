from stringtemplate3.language.Expr import Expr


class StringRef(Expr):
    """
    Represents a chunk of just simple text to spit out; nothing to "evaluate"
    """

    def __init__(self, enclosingTemplate, text):
        super(StringRef, self).__init__(enclosingTemplate)
        self._str = text

    def write(self, this, out):
        """
        Just print out the string; no reference to self because this
        is a literal -- not sensitive to attribute values. These strings
        never wrap because they are not part of an <...> expression.
        <"foo"; wrap="\n"> should wrap though if necessary.
        """

        if self._str is not None:
            return out.write(self._str)

        return 0

    def __str__(self):
        if self._str:
            return self._str
        return ''
