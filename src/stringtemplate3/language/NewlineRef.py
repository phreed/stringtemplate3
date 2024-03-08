from stringtemplate3.language.StringRef import StringRef


class NewlineRef(StringRef):
    """
    Represents a newline.
    Separated so I can do smart things like not spitting out newlines
    when the only thing on a line is an attr expr.
    """

    def __init__(self, enclosingTemplate, a_str):
        super(NewlineRef, self).__init__(enclosingTemplate, a_str)
