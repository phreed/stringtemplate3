# ## $ANTLR 2.7.7 (2006-11-01): "action.g" -> "ActionLexer.py"$
# ## import antlr and other modules ..
from builtins import str
from builtins import range

from stringtemplate3 import antlr

# ## header action >>> 
from stringtemplate3.language.StringTemplateToken import StringTemplateToken

# ## header action <<<
# ## preamble action >>> 

# ## preamble action <<< 
# ## >>>The Literals<<<
literals = {
    u"super": 32,
    u"if": 8,
    u"first": 26,
    u"last": 28,
    u"rest": 27,
    u"trunc": 31,
    u"strip": 30,
    u"length": 29,
    u"elseif": 18}

# ## import antlr.Token

# ## >>>The Known Token Types <<<
SKIP = antlr.SKIP
INVALID_TYPE = antlr.INVALID_TYPE
EOF_TYPE = antlr.EOF_TYPE
EOF = antlr.EOF
NULL_TREE_LOOKAHEAD = antlr.NULL_TREE_LOOKAHEAD
MIN_USER_TYPE = antlr.MIN_USER_TYPE
APPLY = 4
MULTI_APPLY = 5
ARGS = 6
INCLUDE = 7
CONDITIONAL = 8
VALUE = 9
TEMPLATE = 10
FUNCTION = 11
SINGLEVALUEARG = 12
LIST = 13
NOTHING = 14
SEMI = 15
LPAREN = 16
RPAREN = 17
LITERAL_elseif = 18
COMMA = 19
ID = 20
ASSIGN = 21
COLON = 22
NOT = 23
PLUS = 24
DOT = 25
LITERAL_first = 26
LITERAL_rest = 27
LITERAL_last = 28
LITERAL_length = 29
LITERAL_strip = 30
LITERAL_trunc = 31
LITERAL_super = 32
ANONYMOUS_TEMPLATE = 33
STRING = 34
INT = 35
LBRACK = 36
RBRACK = 37
DOTDOTDOT = 38
TEMPLATE_ARGS = 39
NESTED_ANONYMOUS_TEMPLATE = 40
ESC_CHAR = 41
WS = 42
WS_CHAR = 43


class Lexer(antlr.CharScanner):
    # ## user action >>>
    # ## user action <<<
    def __init__(self, *argv, **kwargs):
        super().__init__(*argv, **kwargs)
        self._caseSensitiveLiterals = True
        self._caseSensitive = True
        self._literals = literals

    @property
    def nextToken(self):
        while True:
            try:  # ## try again ..
                while True:
                    _token = None
                    _ttype = INVALID_TYPE
                    self.resetText()
                    try:  # # for char stream error handling
                        try:  # #for lexical error handling
                            la1 = self.LA(1)
                            if False:
                                pass
                            elif la1 and la1 in u'ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz':
                                pass
                                self.mID(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'0123456789':
                                pass
                                self.mINT(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'"':
                                pass
                                self.mSTRING(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'{':
                                pass
                                self.mANONYMOUS_TEMPLATE(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'[':
                                pass
                                self.mLBRACK(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u']':
                                pass
                                self.mRBRACK(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'(':
                                pass
                                self.mLPAREN(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u')':
                                pass
                                self.mRPAREN(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u',':
                                pass
                                self.mCOMMA(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'=':
                                pass
                                self.mASSIGN(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u':':
                                pass
                                self.mCOLON(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'+':
                                pass
                                self.mPLUS(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u';':
                                pass
                                self.mSEMI(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'!':
                                pass
                                self.mNOT(True)
                                theRetToken = self._returnToken
                            elif la1 and la1 in u'\t\n\r ':
                                pass
                                self.mWS(True)
                                theRetToken = self._returnToken
                            else:
                                if (self.LA(1) == u'.') and (self.LA(2) == u'.'):
                                    pass
                                    self.mDOTDOTDOT(True)
                                    theRetToken = self._returnToken
                                elif (self.LA(1) == u'.') and True:
                                    pass
                                    self.mDOT(True)
                                    theRetToken = self._returnToken
                                else:
                                    self.default(self.LA(1))

                            if not self._returnToken:
                                raise antlr.TryAgain  # ## found SKIP token
                            # ## return token to caller
                            return self._returnToken
                        # ## handle lexical errors ....
                        except antlr.RecognitionException as re:
                            raise antlr.TokenStreamRecognitionException(re)
                    # ## handle char stream errors ...
                    except antlr.CharStreamException as cse:
                        if isinstance(cse, antlr.CharStreamIOException):
                            raise antlr.TokenStreamIOException(cse.io)
                        else:
                            raise antlr.TokenStreamException(str(cse))
            except antlr.TryAgain:
                pass

    def mID(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = ID
        _saveIndex = 0
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in u'abcdefghijklmnopqrstuvwxyz':
            pass
            self.matchRange(u'a', u'z')
        elif la1 and la1 in u'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            pass
            self.matchRange(u'A', u'Z')
        elif la1 and la1 in u'_':
            pass
            self.match('_')
        else:
            self.raise_NoViableAlt(self.LA(1))

        while True:
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in u'abcdefghijklmnopqrstuvwxyz':
                pass
                self.matchRange(u'a', u'z')
            elif la1 and la1 in u'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                pass
                self.matchRange(u'A', u'Z')
            elif la1 and la1 in u'0123456789':
                pass
                self.matchRange(u'0', u'9')
            elif la1 and la1 in u'_':
                pass
                self.match('_')
            elif la1 and la1 in u'/':
                pass
                self.match('/')
            else:
                break

        # ## option { testLiterals=true }
        _ttype = self.testLiteralsTable(_ttype)
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mINT(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = INT
        _saveIndex = 0
        pass
        _cnt63 = 0
        while True:
            if u'0' <= self.LA(1) <= u'9':
                pass
                self.matchRange(u'0', u'9')
            else:
                break

            _cnt63 += 1
        if _cnt63 < 1:
            self.raise_NoViableAlt(self.LA(1))
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mSTRING(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = STRING
        _saveIndex = 0
        pass
        _saveIndex = self._text.length()
        self.match('"')
        self._text.setLength(_saveIndex)
        while True:
            if self.LA(1) == u'\\':
                pass
                self.mESC_CHAR(False, True)
            elif _tokenSet_0.member(self.LA(1)):
                pass
                self.matchNot('"')
            else:
                break

        _saveIndex = self._text.length()
        self.match('"')
        self._text.setLength(_saveIndex)
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mESC_CHAR(self, _createToken, doEscape):
        """ Match escape sequences
        optionally translating them for strings,
        but not for templates.
        Do '}' only when in {...} templates.
        """
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = ESC_CHAR
        _saveIndex = 0
        c = '\0'
        pass
        self.match('\\')
        if (self.LA(1) == u'n') and (u'\u0003' <= self.LA(2) <= u'\ufffe'):
            pass
            self.match('n')
            if not self._inputState.guessing:
                if doEscape:
                    self._text.setLength(_begin)
                    self._text.append("\n")
        elif (self.LA(1) == u'r') and (u'\u0003' <= self.LA(2) <= u'\ufffe'):
            pass
            self.match('r')
            if not self._inputState.guessing:
                if doEscape:
                    self._text.setLength(_begin)
                    self._text.append("\r")
        elif (self.LA(1) == u't') and (u'\u0003' <= self.LA(2) <= u'\ufffe'):
            pass
            self.match('t')
            if not self._inputState.guessing:
                if doEscape:
                    self._text.setLength(_begin)
                    self._text.append("\t")
        elif (self.LA(1) == u'b') and (u'\u0003' <= self.LA(2) <= u'\ufffe'):
            pass
            self.match('b')
            if not self._inputState.guessing:
                if doEscape:
                    self._text.setLength(_begin)
                    self._text.append("\b")
        elif (self.LA(1) == u'f') and (u'\u0003' <= self.LA(2) <= u'\ufffe'):
            pass
            self.match('f')
            if not self._inputState.guessing:
                if doEscape:
                    self._text.setLength(_begin)
                    self._text.append("\f")
        elif (u'\u0003' <= self.LA(1) <= u'\ufffe') and (u'\u0003' <= self.LA(2) <= u'\ufffe'):
            pass
            c = self.LA(1)
            self.matchNot(antlr.EOF_CHAR)
            if not self._inputState.guessing:
                if doEscape:
                    self._text.setLength(_begin)
                    self._text.append(str(c))
        else:
            self.raise_NoViableAlt(self.LA(1))

        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mANONYMOUS_TEMPLATE(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = ANONYMOUS_TEMPLATE
        _saveIndex = 0
        args = None
        t = None
        pass
        _saveIndex = self._text.length()
        self.match('{')
        self._text.setLength(_saveIndex)
        synPredMatched70 = False
        if (_tokenSet_1.member(self.LA(1))) and (_tokenSet_2.member(self.LA(2))):
            _m70 = self.mark()
            synPredMatched70 = True
            self._inputState.guessing += 1
            try:
                pass
                self.mTEMPLATE_ARGS(False)
            except antlr.RecognitionException as pe:
                synPredMatched70 = False
            self.rewind(_m70)
            self._inputState.guessing -= 1
        if synPredMatched70:
            pass
            args = self.mTEMPLATE_ARGS(False)
            if (_tokenSet_3.member(self.LA(1))) and (u'\u0003' <= self.LA(2) <= u'\ufffe'):
                pass
                _saveIndex = self._text.length()
                self.mWS_CHAR(False)
                self._text.setLength(_saveIndex)
            elif (u'\u0003' <= self.LA(1) <= u'\ufffe') and True:
                pass
            else:
                self.raise_NoViableAlt(self.LA(1))

            if not self._inputState.guessing:
                # create a special token to track args
                t = StringTemplateToken(ANONYMOUS_TEMPLATE, self._text.getString(_begin), args)
                _token = t
        elif (u'\u0003' <= self.LA(1) <= u'\ufffe') and True:
            pass
        else:
            self.raise_NoViableAlt(self.LA(1))

        while True:
            if (self.LA(1) == u'\\') and (self.LA(2) == u'{'):
                pass
                _saveIndex = self._text.length()
                self.match('\\')
                self._text.setLength(_saveIndex)
                self.match('{')
            elif (self.LA(1) == u'\\') and (self.LA(2) == u'}'):
                pass
                _saveIndex = self._text.length()
                self.match('\\')
                self._text.setLength(_saveIndex)
                self.match('}')
            elif (self.LA(1) == u'\\') and (u'\u0003' <= self.LA(2) <= u'\ufffe'):
                pass
                self.mESC_CHAR(False, False)
            elif self.LA(1) == u'{':
                pass
                self.mNESTED_ANONYMOUS_TEMPLATE(False)
            elif _tokenSet_4.member(self.LA(1)):
                pass
                self.matchNot('}')
            else:
                break

        if not self._inputState.guessing:
            if t:
                t.text = self._text.getString(_begin)
        _saveIndex = self._text.length()
        self.match('}')
        self._text.setLength(_saveIndex)
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mTEMPLATE_ARGS(self, _createToken):
        args = []
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = TEMPLATE_ARGS
        _saveIndex = 0
        a = None
        a2 = None
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in u'\t\n\r ':
            pass
            _saveIndex = self._text.length()
            self.mWS_CHAR(False)
            self._text.setLength(_saveIndex)
        elif la1 and la1 in u'ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz':
            pass
        else:
            self.raise_NoViableAlt(self.LA(1))

        _saveIndex = self._text.length()
        self.mID(True)
        self._text.setLength(_saveIndex)
        a = self._returnToken
        if not self._inputState.guessing:
            args.append(a.text)
        while True:
            if (_tokenSet_5.member(self.LA(1))) and (_tokenSet_6.member(self.LA(2))):
                pass
                la1 = self.LA(1)
                if False:
                    pass
                elif la1 and la1 in u'\t\n\r ':
                    pass
                    _saveIndex = self._text.length()
                    self.mWS_CHAR(False)
                    self._text.setLength(_saveIndex)
                elif la1 and la1 in u',':
                    pass
                else:
                    self.raise_NoViableAlt(self.LA(1))

                _saveIndex = self._text.length()
                self.match(',')
                self._text.setLength(_saveIndex)
                la1 = self.LA(1)
                if False:
                    pass
                elif la1 and la1 in u'\t\n\r ':
                    pass
                    _saveIndex = self._text.length()
                    self.mWS_CHAR(False)
                    self._text.setLength(_saveIndex)
                elif la1 and la1 in u'ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz':
                    pass
                else:
                    self.raise_NoViableAlt(self.LA(1))

                _saveIndex = self._text.length()
                self.mID(True)
                self._text.setLength(_saveIndex)
                a2 = self._returnToken
                if not self._inputState.guessing:
                    args.append(a2.text)
            else:
                break

        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in u'\t\n\r ':
            pass
            _saveIndex = self._text.length()
            self.mWS_CHAR(False)
            self._text.setLength(_saveIndex)
        elif la1 and la1 in u'|':
            pass
        else:
            self.raise_NoViableAlt(self.LA(1))

        _saveIndex = self._text.length()
        self.match('|')
        self._text.setLength(_saveIndex)
        self.set_return_token(_createToken, _token, _ttype, _begin)
        return args

    def mWS_CHAR(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = WS_CHAR
        _saveIndex = 0
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in u' ':
            pass
            self.match(' ')
        elif la1 and la1 in u'\t':
            pass
            self.match('\t')
        elif la1 and la1 in u'\n\r':
            pass
            if (self.LA(1) == u'\r') and (u'\u0003' <= self.LA(2) <= u'\ufffe'):
                pass
                self.match('\r')
            elif (self.LA(1) == u'\r') and (self.LA(2) == u'\n'):
                pass
                self.match('\r')
                self.match('\n')
            elif self.LA(1) == u'\n':
                pass
                self.match('\n')
            else:
                self.raise_NoViableAlt(self.LA(1))

            if not self._inputState.guessing:
                self.newline()
        else:
            self.raise_NoViableAlt(self.LA(1))

        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mNESTED_ANONYMOUS_TEMPLATE(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = NESTED_ANONYMOUS_TEMPLATE
        _saveIndex = 0
        pass
        self.match('{')
        while True:
            if (self.LA(1) == u'\\') and (self.LA(2) == u'{'):
                pass
                _saveIndex = self._text.length()
                self.match('\\')
                self._text.setLength(_saveIndex)
                self.match('{')
            elif (self.LA(1) == u'\\') and (self.LA(2) == u'}'):
                pass
                _saveIndex = self._text.length()
                self.match('\\')
                self._text.setLength(_saveIndex)
                self.match('}')
            elif (self.LA(1) == u'\\') and (u'\u0003' <= self.LA(2) <= u'\ufffe'):
                pass
                self.mESC_CHAR(False, False)
            elif self.LA(1) == u'{':
                pass
                self.mNESTED_ANONYMOUS_TEMPLATE(False)
            elif _tokenSet_4.member(self.LA(1)):
                pass
                self.matchNot('}')
            else:
                break

        self.match('}')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mLBRACK(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = LBRACK
        _saveIndex = 0
        pass
        self.match('[')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mRBRACK(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = RBRACK
        _saveIndex = 0
        pass
        self.match(']')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mLPAREN(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = LPAREN
        _saveIndex = 0
        pass
        self.match('(')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mRPAREN(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = RPAREN
        _saveIndex = 0
        pass
        self.match(')')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mCOMMA(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = COMMA
        _saveIndex = 0
        pass
        self.match(',')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mDOT(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = DOT
        _saveIndex = 0
        pass
        self.match('.')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mASSIGN(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = ASSIGN
        _saveIndex = 0
        pass
        self.match('=')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mCOLON(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = COLON
        _saveIndex = 0
        pass
        self.match(':')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mPLUS(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = PLUS
        _saveIndex = 0
        pass
        self.match('+')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mSEMI(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = SEMI
        _saveIndex = 0
        pass
        self.match(';')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mNOT(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = NOT
        _saveIndex = 0
        pass
        self.match('!')
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mDOTDOTDOT(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = DOTDOTDOT
        _saveIndex = 0
        pass
        self.match("...")
        self.set_return_token(_createToken, _token, _ttype, _begin)

    def mWS(self, _createToken):
        _ttype = 0
        _token = None
        _begin = self._text.length()
        _ttype = WS
        _saveIndex = 0
        pass
        la1 = self.LA(1)
        if False:
            pass
        elif la1 and la1 in u' ':
            pass
            self.match(' ')
        elif la1 and la1 in u'\t':
            pass
            self.match('\t')
        elif la1 and la1 in u'\n\r':
            pass
            if (self.LA(1) == u'\r') and (self.LA(2) == u'\n'):
                pass
                self.match('\r')
                self.match('\n')
            elif (self.LA(1) == u'\r') and True:
                pass
                self.match('\r')
            elif self.LA(1) == u'\n':
                pass
                self.match('\n')
            else:
                self.raise_NoViableAlt(self.LA(1))

            if not self._inputState.guessing:
                self.newline()
        else:
            self.raise_NoViableAlt(self.LA(1))

        if not self._inputState.guessing:
            _ttype = SKIP
        self.set_return_token(_createToken, _token, _ttype, _begin)


def mk_tokenSet_0():
    """ generate bit set """
    data = [0] * 2048 
    data[0] = -17179869192
    data[1] = -268435457
    for x in range(2, 1023):
        data[x] = -1
    data[1023] = 9223372036854775807
    return data


_tokenSet_0 = antlr.BitSet(mk_tokenSet_0())


def mk_tokenSet_1():
    """ generate bit set """
    data = [0] * 1025
    data[0] = 4294977024
    data[1] = 576460745995190270
    return data


_tokenSet_1 = antlr.BitSet(mk_tokenSet_1())


def mk_tokenSet_2():
    """ generate bit set """
    data = [0] * 1025
    data[0] = 288107235144377856
    data[1] = 1729382250602037246
    return data


_tokenSet_2 = antlr.BitSet(mk_tokenSet_2())


def mk_tokenSet_3():
    """ generate bit set """
    data = [0] * 1025
    data[0] = 4294977024
    return data


_tokenSet_3 = antlr.BitSet(mk_tokenSet_3())


def mk_tokenSet_4():
    """ generate bit set """
    data = [0] * 2048
    data[0] = -8
    data[1] = -2882303761785552897
    for x in range(2, 1023):
        data[x] = -1
    data[1023] = 9223372036854775807
    return data


_tokenSet_4 = antlr.BitSet(mk_tokenSet_4())


def mk_tokenSet_5():
    """ generate bit set """
    data = [0] * 1025
    data[0] = 17596481021440
    return data


_tokenSet_5 = antlr.BitSet(mk_tokenSet_5())


def mk_tokenSet_6():
    """ generate bit set """
    data = [0] * 1025
    data[0] = 17596481021440
    data[1] = 576460745995190270
    return data


_tokenSet_6 = antlr.BitSet(mk_tokenSet_6())


if __name__ == '__main__':
    """ __main__ header action """
    from stringtemplate3 import antlr
    from . import ActionLexer

    # ## create lexer - shall read from stdin
    try:
        for token in ActionLexer.Lexer():
            print(token)

    except antlr.TokenStreamException as e:
        print("error: exception caught while lexing: ", e)
# ## __main__ header action <<<
