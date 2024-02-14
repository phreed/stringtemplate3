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

    def getStringTemplate(self):
        return self._st

    def setStringTemplate(self, st):
        self._st = st
