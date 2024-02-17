from stringtemplate3 import antlr


class StringTemplateAST(antlr.CommonAST):

    def __init__(self, a_type=None, text=None):
        super(StringTemplateAST, self).__init__()

        if a_type is not None:
            self._type = a_type

        if text is not None:
            self._text = text

        # track template for ANONYMOUS blocks
        self._st = None

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def stringTemplate(self):
        return self._st

    @stringTemplate.setter
    def stringTemplate(self, st):
        self._st = st
