# This file is part of PyANTLR. See LICENSE.txt for license
# details..........Copyright (C) Wolfgang Haefelinger, 2004.
import collections
# get sys module
from builtins import hex
from builtins import str
from builtins import range
from builtins import object
from collections import abc
# import curses.ascii
import sys
from io import IOBase
import logging

logger = logging.getLogger(__name__)

# ##xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx###
# ##                     global symbols                            # ##
# ##xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx###

# ANTLR Standard Tokens
SKIP = -1
INVALID_TYPE = 0
EOF_TYPE = 1
EOF = 1
NULL_TREE_LOOKAHEAD = 3
MIN_USER_TYPE = 4

# ANTLR's EOF Symbol
EOF_CHAR = ''


# <version>
def version():
    """ Version should be automatically derived from configure.in.
    For now, we need to bump it ourselves.
    Don't remove the <version> tags.
    <version>
    """
    return {
        'major': '2',
        'minor': '7',
        'micro': '5',
        'patch': '',
        'version': '2.7.5'
    }
# </version>


def error(fmt, *args):
    if fmt:
        print(("error: ", fmt % tuple(args)))


def if_else(cond, _then, _else):
    if cond:
        r = _then
    else:
        r = _else
    return r


def is_string_type(x):
    """all strings in python3 are unicode
    We also consider bytes to be string_type
    """
    return isinstance(x, str) or isinstance(x, bytes)


def assert_string_type(x):
    assert is_string_type(x)


# ##xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx###
# ##                     ANTLR Exceptions                          # ##
# ##xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx###

class ANTLRException(Exception):
    """AntLRException base class"""

    def __init__(self, *args):
        super().__init__(*args)


class RecognitionException(ANTLRException):
    """ RecognitionException base """

    def __init__(self, *args):
        super().__init__(*args)
        self._fileName = None
        self._line = -1
        self._column = -1

        if len(args) >= 2:
            self._fileName = args[1]
        if len(args) >= 3:
            self._line = args[2]
        if len(args) >= 4:
            self._column = args[3]

    def __str__(self):
        buf = ['']
        if self._fileName:
            buf.append(f"{self._fileName}:")
        if self._line != -1:
            if not self._fileName:
                buf.append("line ")
            buf.append(str(self._line))
            if self._column != -1:
                buf.append(":" + str(self._column))
            buf.append(":")
        buf.append(" ")
        return str('').join(buf)

    __repr__ = __str__


class NoViableAltException(RecognitionException):
    """ NoViableAltException base """

    def __init__(self, *args):
        super().__init__(*args)
        self._token = None
        self._node = None
        if isinstance(args[0], AST):
            self._node = args[0]
        elif isinstance(args[0], Token):
            self._token = args[0]
        else:
            raise TypeError("NoViableAltException requires Token or AST argument")

    def __str__(self):
        if self._token:
            a_token = self._token
            if isinstance(a_token, AST):
                line = a_token.line
                col = a_token.column
                text = a_token.text
                return "unexpected symbol at line %s (column %s): \"%s\"" % (line, col, text)
            else:
                return f"unexpected token: \"{a_token}\""
        if self._node == ASTNULL:
            return "unexpected end of subtree"
        assert self._node
        # hackish, we assume that an AST contains property 'text'
        if hasattr(self._node, "text"):
            return "unexpected node: %s" % self._node.text
        else:
            return f"unexpected node: {self._node}"

    __repr__ = __str__


class NoViableAltForCharException(RecognitionException):
    """ Raised when ... """

    def __init__(self, *args):
        self._foundChar = None
        if len(args) == 2:
            self._foundChar = args[0]
            scanner = args[1]
            if isinstance(scanner, CharScanner):
                super().__init__("NoViableAlt",
                                 scanner.filename,
                                 scanner.line,
                                 scanner.column)
            else:
                super().__init__("NoViableAlt", '', -1, -1)
        elif len(args) == 4:
            self._foundChar = args[0]
            fileName = args[1]
            line = args[2]
            column = args[3]
            super().__init__("NoViableAlt", fileName, line, column)
        else:
            super().__init__("NoViableAlt", '', -1, -1)

    def __str__(self):
        """
        If a graphical character (from x20 'space' to x8f '~' inclusive) is found;
        then, add it to the message.
        otherwise, if the found character is 'truthy';
        then, add it to the message as upper case hexadecimal.
        otherwise, represent any 'falsey' values as None.
        """
        if not self._foundChar:
            return "unexpected char: <None>"
        if isinstance(self._foundChar, str):
            if self._foundChar.isprintable():
                return f"unexpected char: '{self._foundChar}'"
            else:
                return f"unexpected char: '{hex(ord(self._foundChar)).upper()[2:]}'"
        if isinstance(self._foundChar, bytes):
            return f"unexpected char: {self._foundChar}"
            # if curses.ascii.isgraph(self.foundChar[0]):
            #     return f"unexpected char: '{self.foundChar}'"
            # else:
            #     return f"unexpected char: '{hex(ord(self.foundChar)).upper()[2:]}'"
        return f"unexpected char: {self._foundChar}"

    __repr__ = __str__


class SemanticException(RecognitionException):
    """ Raised when a semantic error occurs"""

    def __init__(self, *args):
        super().__init__(*args)


class MismatchedCharException(RecognitionException):
    """ Raised when a character is mismatched"""
    NONE = 0
    CHAR = 1
    NOT_CHAR = 2
    RANGE = 3
    NOT_RANGE = 4
    SET = 5
    NOT_SET = 6

    def __init__(self, *args):
        self._args = args
        if len(args) == 5:
            # Expected range / not range
            if args[3]:
                self._mismatchType = MismatchedCharException.NOT_RANGE
            else:
                self._mismatchType = MismatchedCharException.RANGE
            self._foundChar = args[0]
            self._expecting = args[1]
            self._upper = args[2]
            scanner = args[4]
            self._scanner = scanner
            if isinstance(scanner, CharScanner):
                super().__init__("Mismatched char range",
                                 scanner.filename, scanner.line, scanner.column)
            else:
                super().__init__("NoViableAlt", '', -1, -1)
        elif len(args) == 4 and is_string_type(args[1]):
            # Expected char / not char
            if args[2]:
                self._mismatchType = MismatchedCharException.NOT_CHAR
            else:
                self._mismatchType = MismatchedCharException.CHAR
            self._foundChar = args[0]
            self._expecting = args[1]
            scanner = args[3]
            self._scanner = scanner
            if isinstance(scanner, CharScanner):
                super().__init__("Mismatched char",
                                 scanner.filename, scanner.line, scanner.column)
            else:
                super().__init__("NoViableAlt", '', -1, -1)
        elif len(args) == 4 and isinstance(args[1], BitSet):
            # Expected BitSet / not BitSet
            if args[2]:
                self._mismatchType = MismatchedCharException.NOT_SET
            else:
                self._mismatchType = MismatchedCharException.SET
            self._foundChar = args[0]
            self._set = args[1]
            scanner = args[3]
            self._scanner = scanner
            if isinstance(scanner, CharScanner):
                super().__init__("Mismatched char set",
                                 scanner.filename, scanner.line, scanner.column)
            else:
                super().__init__("NoViableAlt", '', -1, -1)
        else:
            self._mismatchType = MismatchedCharException.NONE
            super().__init__("Mismatched char")

    def appendCharName(self, sb, c):
        """ Append a char to the msg buffer.
        If special, then show escaped version
        """
        if not c or c == 65535:
            # 65535 = (char) -1 = EOF
            sb.append("'<EOF>'")
        elif c == '\n':
            sb.append("'\\n'")
        elif c == '\r':
            sb.append("'\\r'")
        elif c == '\t':
            sb.append("'\\t'")
        else:
            sb.append('\'' + c + '\'')

    def __str__(self):
        """ Returns an error message with line number/column information """
        sb = [u'', RecognitionException.__str__(self)]

        if self._mismatchType == MismatchedCharException.CHAR:
            sb.append("expecting ")
            self.appendCharName(sb, self._expecting)
            sb.append(", found ")
            self.appendCharName(sb, self._foundChar)
        elif self._mismatchType == MismatchedCharException.NOT_CHAR:
            sb.append("expecting anything but '")
            self.appendCharName(sb, self._expecting)
            sb.append("'; got it anyway")
        elif self._mismatchType in [MismatchedCharException.RANGE, MismatchedCharException.NOT_RANGE]:
            sb.append("expecting char ")
            if self._mismatchType == MismatchedCharException.NOT_RANGE:
                sb.append("NOT ")
            sb.append("in range: ")
            self.appendCharName(sb, self._expecting)
            sb.append("..")
            self.appendCharName(sb, self._upper)
            sb.append(", found ")
            self.appendCharName(sb, self._foundChar)
        elif self._mismatchType in [MismatchedCharException.SET, MismatchedCharException.NOT_SET]:
            sb.append("expecting ")
            if self._mismatchType == MismatchedCharException.NOT_SET:
                sb.append("NOT ")
            sb.append("one of (")
            if isinstance(self._set, abc.Sized) and isinstance(self._set, abc.Sequence):
                for ix in range(len(self._set)):
                    self.appendCharName(sb, self._set[ix])
            sb.append("), found ")
            self.appendCharName(sb, self._foundChar)

        return str().join(sb).strip()

    __repr__ = __str__


class MismatchedTokenException(RecognitionException):
    """ Raised when a token is mismatched"""
    NONE = 0
    TOKEN = 1
    NOT_TOKEN = 2
    RANGE = 3
    NOT_RANGE = 4
    SET = 5
    NOT_SET = 6

    @property
    def tokenNames(self):
        return self._tokenNames

    @tokenNames.setter
    def tokenNames(self, tokenNames):
        if isinstance(tokenNames, abc.Sequence):
            self._tokenNames = tokenNames
        else:
            logger.error("Invalid token names type")

    @property
    def set(self):
        return self._set

    @set.setter
    def set(self, a_set):
        if isinstance(a_set, abc.Sequence):
            self._set = a_set
        else:
            logger.error("Invalid token names type")

    @property
    def expecting(self):
        return self._expecting

    @expecting.setter
    def expecting(self, expecting):
        if not hasattr(expecting, "__lt__"):
            logger.error("Invalid token names type")
            return
        if not hasattr(expecting, "__ge__"):
            logger.error("Invalid token names type")
            return
        self._expecting = expecting

    @property
    def upper(self):
        return self._upper

    @upper.setter
    def upper(self, upper):
        if not hasattr(upper, "__lt__"):
            logger.error("Invalid token names type")
            return
        if not hasattr(upper, "__ge__"):
            logger.error("Invalid token names type")
            return
        self._upper = upper

    def __init__(self, *args):
        self._args = args
        self._tokenNames = []
        self._token = None
        self._tokenText = ''
        self._node = None
        if len(args) == 6:
            # Expected range / not range
            if args[3]:
                self._mismatchType = MismatchedTokenException.NOT_RANGE
            else:
                self._mismatchType = MismatchedTokenException.RANGE
            self.tokenNames = args[0]
            self.expecting = args[2]
            self.upper = args[3]
            self._fileName = args[5]

        elif len(args) == 4 and isinstance(args[2], int):
            # Expected token / not token
            if args[3]:
                self._mismatchType = MismatchedTokenException.NOT_TOKEN
            else:
                self._mismatchType = MismatchedTokenException.TOKEN
            self.tokenNames = args[0]
            self.expecting = args[2]

        elif len(args) == 4 and isinstance(args[2], BitSet):
            # Expected BitSet / not BitSet
            if args[3]:
                self._mismatchType = MismatchedTokenException.NOT_SET
            else:
                self._mismatchType = MismatchedTokenException.SET
            self.tokenNames = args[0]
            self.set = args[2]

        else:
            self._mismatchType = MismatchedTokenException.NONE
            super().__init__("Mismatched Token: expecting any AST node", "<AST>", -1, -1)

        if len(args) >= 2:
            a1 = args[1]
            if isinstance(a1, Token):
                self._token = a1
                self._tokenText = a1.text
                super().__init__("Mismatched Token",
                                 self._fileName, a1.line, a1.column)
            elif isinstance(a1, AST):
                self._node = a1
                self._tokenText = str(self._node)
                super().__init__("Mismatched Token",
                                 "<AST>", self._node.line, self._node.column)
            else:
                self._tokenText = "<empty tree>"
                super().__init__("Mismatched Token", "<AST>", -1, -1)

    def appendTokenName(self, sb, tokenType):
        if tokenType == INVALID_TYPE:
            sb.append("<Set of tokens>")
        elif tokenType < 0:
            sb.append("<" + str(tokenType) + ">")
        elif tokenType >= len(self._tokenNames):
            sb.append("<" + str(tokenType) + ">")
        else:
            sb.append(self._tokenNames[tokenType])

    def __str__(self):
        """ Returns an error message with line number/column information """
        sb = ['', RecognitionException.__str__(self)]

        if self._mismatchType == MismatchedTokenException.TOKEN:
            sb.append("expecting ")
            self.appendTokenName(sb, self._expecting)
            sb.append(", found " + self._tokenText)
        elif self._mismatchType == MismatchedTokenException.NOT_TOKEN:
            sb.append("expecting anything but '")
            self.appendTokenName(sb, self._expecting)
            sb.append("'; got it anyway")
        elif self._mismatchType in [MismatchedTokenException.RANGE, MismatchedTokenException.NOT_RANGE]:
            sb.append("expecting token ")
            if self._mismatchType == MismatchedTokenException.NOT_RANGE:
                sb.append("NOT ")
            sb.append("in range: ")
            self.appendTokenName(sb, self._expecting)
            sb.append("..")
            self.appendTokenName(sb, self._upper)
            sb.append(", found " + self._tokenText)
        elif self._mismatchType in [MismatchedTokenException.SET, MismatchedTokenException.NOT_SET]:
            sb.append("expecting ")
            if self._mismatchType == MismatchedTokenException.NOT_SET:
                sb.append("NOT ")
            sb.append("one of (")
            for i in range(len(self._set)):
                self.appendTokenName(sb, self._set[i])
            sb.append("), found " + self._tokenText)

        return str().join(sb).strip()

    __repr__ = __str__


class TokenStreamException(ANTLRException):
    """ Raised when there is a problem with the token stream. """

    def __init__(self, *args):
        super().__init__(*args)


class TokenStreamIOException(TokenStreamException):
    """ Wraps an Exception in a TokenStreamException """

    def __init__(self, *args):
        if args and isinstance(args[0], Exception):
            io = args[0]
            super().__init__(str(io))
            self._io = io
        else:
            super().__init__(*args)
            self._io = self


class TokenStreamRecognitionException(TokenStreamException):
    """ Wraps a RecognitionException in a TokenStreamException """
    def __init__(self, *args):
        if args and isinstance(args[0], RecognitionException):
            recog = args[0]
            super().__init__(str(recog))
            self._recog = recog
        else:
            raise TypeError("TokenStreamRecognitionException requires RecognitionException argument")

    def __str__(self):
        return str(self._recog)

    __repr__ = __str__


class TokenStreamRetryException(TokenStreamException):
    """ Raised when an attempt is made to retry a token. """

    def __init__(self, *args):
        super().__init__(*args)


class CharStreamException(ANTLRException):
    """ Raised when an error occurs on a character stream. """

    def __init__(self, *args):
        super().__init__(*args)


class CharStreamIOException(CharStreamException):
    """ Wraps an Exception in a CharStreamException """

    def __init__(self, *args):
        if args and isinstance(args[0], Exception):
            io = args[0]
            super().__init__(str(io))
            self._io = io
        else:
            super().__init__(*args)
            self._io = self

    @property
    def io(self):
        return self._io


class TryAgain(Exception):
    pass


class Token(object):
    """ Token """
    SKIP = -1
    INVALID_TYPE = 0
    EOF_TYPE = 1
    EOF = 1
    NULL_TREE_LOOKAHEAD = 3
    MIN_USER_TYPE = 4

    def __init__(self, **argv):
        try:
            self._type = argv['type']
        except:
            self._type = INVALID_TYPE
        try:
            self._text = argv['text']
        except:
            self._text = "<no text>"

    @property
    def isEOF(self):
        return self._type == EOF_TYPE

    @property
    def column(self):
        return 0

    @column.setter
    def column(self, column):
        pass

    @property
    def line(self):
        return 0

    @line.setter
    def line(self, line):
        pass

    @property
    def filename(self):
        return None

    @filename.setter
    def filename(self, name):
        pass

    @property
    def text(self):
        return "<no text>"

    @text.setter
    def text(self, text):
        if is_string_type(text):
            pass
        else:
            raise TypeError("Token.setText requires string argument")

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, a_type):
        if isinstance(a_type, int):
            self._type = a_type
        else:
            raise TypeError("Token.setType requires integer argument")

    def toString(self):
        # not optimal
        type_ = self._type
        if type_ == 3:
            tval = 'NULL_TREE_LOOKAHEAD'
        elif type_ == 1:
            tval = 'EOF_TYPE'
        elif type_ == 0:
            tval = 'INVALID_TYPE'
        elif type_ == -1:
            tval = 'SKIP'
        else:
            tval = type_
        return '["%s",<%s>]' % (self._text, tval)

    __str__ = toString
    __repr__ = toString


# ## static attribute ..
Token.badToken = Token(type=INVALID_TYPE, text="<no text>")

if __name__ == "__main__":
    print("testing ..")
    T = Token.badToken
    print(T)


class CommonToken(Token):
    """ CommonToken """
    def __init__(self, **argv):
        super().__init__(**argv)
        self._line = 0
        self._col = 0
        try:
            self._line = argv['line']
        except:
            pass
        try:
            self._col = argv['col']
        except:
            pass

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, line):
        self._line = line

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text

    @property
    def column(self):
        return self._col

    @column.setter
    def column(self, col):
        self._col = col

    def toString(self):
        # not optimal
        type_ = self.type
        if type_ == 3:
            tval = 'NULL_TREE_LOOKAHEAD'
        elif type_ == 1:
            tval = 'EOF_TYPE'
        elif type_ == 0:
            tval = 'INVALID_TYPE'
        elif type_ == -1:
            tval = 'SKIP'
        else:
            tval = type_
        d = {
            'text': self.text,
            'type': tval,
            'line': self.line,
            'colm': self.column
        }

        fmt = '["%(text)s",<%(type)s>,line=%(line)s,col=%(colm)s]'
        return fmt % d

    __str__ = toString
    __repr__ = toString


if __name__ == '__main__':
    T = CommonToken()
    print(T)
    T = CommonToken(col=15, line=1, text="some text", type=5)
    print(T)
    T = CommonToken()
    T.line = 1
    T.column = 15
    T.text = "some text"
    T.type = 5
    print(T)
    print(T.line)
    print(T.column)
    print(T.text)
    print(T.type)


class CommonHiddenStreamToken(CommonToken):
    """ CommonHiddenStreamToken """
    def __init__(self, *args):
        super().__init__(*args)
        self._hiddenBefore = None
        self._hiddenAfter = None

    @property
    def hiddenAfter(self):
        return self._hiddenAfter

    @hiddenAfter.setter
    def hiddenAfter(self, t):
        self._hiddenAfter = t

    @property
    def hiddenBefore(self):
        return self._hiddenBefore

    @hiddenBefore.setter
    def hiddenBefore(self, t):
        self._hiddenBefore = t


class Queue(object):
    """ Queue: Shall be a circular buffer on tokens ... """

    def __init__(self):
        self._buffer = []  # empty list

    def append(self, item):
        self._buffer.append(item)

    def elementAt(self, index):
        return self._buffer[index]

    def reset(self):
        self._buffer = []

    def removeFirst(self):
        self._buffer.pop(0)

    def length(self):
        return len(self._buffer)

    def __str__(self):
        return str(self._buffer)


class InputBuffer(object):
    """ InputBuffer """
    def __init__(self):
        self._nMarkers = 0
        self._markerOffset = 0
        self._numToConsume = 0
        self._queue = Queue()

    def __str__(self):
        return "(%s,%s,%s,%s)" % (
            self._nMarkers,
            self._markerOffset,
            self._numToConsume,
            self._queue)

    def __repr__(self):
        return str(self)

    def commit(self):
        self._nMarkers -= 1

    def consume(self):
        self._numToConsume += 1

    @property
    def LAChars(self):
        """ probably better to return a list of items because of unicode.
        Or return a unicode string ...
        """
        i = self._markerOffset
        n = self._queue.length()
        s = ''
        while i < n:
            s += self._queue.elementAt(i)
        return s

    @property
    def markedChars(self):
        """ probably better to return a list of items because of unicode chars """
        s = ''
        i = 0
        n = self._markerOffset
        while i < n:
            s += self._queue.elementAt(i)
        return s

    @property
    def isMarked(self):
        return self._nMarkers != 0

    def fill(self, k):
        """ abstract method """
        raise NotImplementedError()

    def LA(self, k):
        self.fill(k)
        return self._queue.elementAt(self._markerOffset + k - 1)

    def mark(self):
        self.syncConsume()
        self._nMarkers += 1
        return self._markerOffset

    def rewind(self, mark):
        self.syncConsume()
        self._markerOffset = mark
        self._nMarkers -= 1

    def reset(self):
        self._nMarkers = 0
        self._markerOffset = 0
        self._numToConsume = 0
        self._queue.reset()

    def syncConsume(self):
        while self._numToConsume > 0:
            if self._nMarkers > 0:
                # guess mode -- leave leading characters and bump offset.
                self._markerOffset += 1
            else:
                # normal mode -- remove first character
                self._queue.removeFirst()
            self._numToConsume -= 1


class CharBuffer(InputBuffer):
    """  CharBuffer """
    def __init__(self, reader):
        """ a reader is supposed to be anything that has a method 'read(int)'. """
        # #assert isinstance(reader,file)
        super(CharBuffer, self).__init__()
        self._input = reader

    def __str__(self):
        base = super(CharBuffer, self).__str__()
        return "CharBuffer{%s,%s" % (base, str(input))

    def fill(self, amount):
        try:
            self.syncConsume()
            while self._queue.length() < (amount + self._markerOffset):
                # retrieve just one char - what happened at end of input?
                c = self._input.read(1)
                # python's behaviour is to return the empty string  on EOF,
                # i.e. no exception whatsoever is thrown.
                # An empty python string has the nice feature that it is of
                # type 'str' and  "not ''" would return true.
                # Contrary, one can't do this: '' in 'abc'.
                # This should return false, but all we get is then a TypeError as an
                # empty string is not a character.

                # Let's assure then that we have either seen a
                # character or an empty string (EOF).
                assert len(c) == 0 or len(c) == 1

                # And it shall be of type string (ASCII or UNICODE).
                assert is_string_type(c)

                # Just append EOF char to buffer.
                # Note that buffer may contain then just more than one EOF char ...

                # use unicode chars instead of ASCII ...
                self._queue.append(c)
        except Exception as e:
            raise CharStreamIOException(e)
        # except: # (mk) Cannot happen ...
        # error ("unexpected exception caught ..")
        # assert 0


class LexerSharedInputState(object):
    """ LexerSharedInputState """
    def __init__(self, in_buf):
        assert isinstance(in_buf, InputBuffer)
        self._input = in_buf
        self._column = 1
        self._line = 1
        self._tokenStartColumn = 1
        self._tokenStartLine = 1
        self._guessing = 0
        self._filename = None

    def reset(self):
        self._column = 1
        self._line = 1
        self._tokenStartColumn = 1
        self._tokenStartLine = 1
        self._guessing = 0
        self._filename = None
        self._input.reset()

    def LA(self, k):
        return self._input.LA(k)

    @property
    def input(self):
        return self._input

    @property
    def column(self):
        return self._column

    @column.setter
    def column(self, col):
        self._column = col

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, line):
        self._line = line

    @property
    def tokenStartColumn(self):
        return self._tokenStartColumn

    @tokenStartColumn.setter
    def tokenStartColumn(self, column):
        self._tokenStartColumn = column

    @property
    def tokenStartLine(self):
        return self._tokenStartLine

    @tokenStartLine.setter
    def tokenStartLine(self, line):
        self._tokenStartLine = line

    @property
    def guessing(self):
        return self._guessing

    @property
    def filename(self):
        return self._filename


class TokenStream(object):
    """ TokenStream """
    def nextToken(self):
        return None

    def __iter__(self):
        return TokenStreamIterator(self)


class TokenStreamIterator(object):
    """ TokenStreamIterator """
    def __init__(self, inst):
        if isinstance(inst, TokenStream):
            self._inst = inst
            return
        raise TypeError("TokenStreamIterator requires TokenStream object")

    def __next__(self):
        assert self._inst
        item = self._inst.nextToken()
        if not item:
            raise StopIteration()
        if isinstance(item, Token) or (hasattr(item, "isEOF") and item.isEOF):
            raise StopIteration()
        return item


class TokenStreamSelector(TokenStream):
    """ TokenStreamSelector """

    def __init__(self):
        self._input = None
        self._stmap = {}
        self._stack = []

    def addInputStream(self, stream, key):
        self._stmap[key] = stream

    @property
    def currentStream(self):
        return self._input

    def getStream(self, sname):
        try:
            stream = self._stmap[sname]
        except:
            raise ValueError("TokenStream " + sname + " not found")
        return stream

    def nextToken(self):
        while 1:
            try:
                return self._input.nextToken()
            except TokenStreamRetryException as rx:
                # just retry "forever"
                pass

    def pop(self):
        stream = self._stack.pop()
        self.select(stream)
        return stream

    def push(self, arg):
        self._stack.append(self._input)
        self.select(arg)

    def retry(self):
        raise TokenStreamRetryException()

    def select(self, arg):
        if isinstance(arg, TokenStream):
            self._input = arg
            return
        if is_string_type(arg):
            self._input = self.getStream(arg)
            return
        raise TypeError("TokenStreamSelector.select requires " +
                        "TokenStream or string argument")


class TokenStreamBasicFilter(TokenStream):
    """ TokenStreamBasicFilter """

    def __init__(self, an_input):

        self._discardMark = None
        self._input = an_input
        self._discardMask = BitSet()

    def discard(self, arg):
        if isinstance(arg, int):
            self._discardMask.add(arg)
            return
        if isinstance(arg, BitSet):
            self._discardMark = arg
            return
        raise TypeError("TokenStreamBasicFilter.discard requires" +
                        "integer or BitSet argument")

    def nextToken(self):
        tok = self._input.nextToken()
        while tok and self._discardMask.member(tok.type):
            tok = self._input.nextToken()
        return tok


class TokenStreamHiddenTokenFilter(TokenStreamBasicFilter):
    """ TokenStreamHiddenTokenFilter """

    def __init__(self, an_input):
        super().__init__(an_input)
        self._hideMask = BitSet()
        self._nextMonitoredToken = None
        self._lastHiddenToken = None
        self._firstHidden = None

    def consume(self):
        self._nextMonitoredToken = self._input.nextToken()

    def consumeFirst(self):
        self.consume()

        p = None
        while self._hideMask.member(self.LA(1).type) or \
                self.discardMask.member(self.LA(1).type):
            if self._hideMask.member(self.LA(1).type):
                if not p:
                    p = self.LA(1)
                else:
                    p.setHiddenAfter(self.LA(1))
                    self.LA(1).setHiddenBefore(p)
                    p = self.LA(1)
                self._lastHiddenToken = p
                if not self._firstHidden:
                    self._firstHidden = p
            self.consume()

    @property
    def discardMask(self):
        return self.discardMask

    def getHiddenAfter(self, t):
        return t.hiddenAfter

    def getHiddenBefore(self, t):
        return t.hiddenBefore

    @property
    def hideMask(self):
        return self._hideMask

    @property
    def initialHiddenToken(self):
        return self._firstHidden

    def hide(self, m):
        if isinstance(m, int):
            self._hideMask.add(m)
            return
        if isinstance(m, BitSet):
            self._hideMask = m
            return

    def LA(self, i):
        return self._nextMonitoredToken

    def nextToken(self):
        if not self.LA(1):
            self.consumeFirst()

        monitored = self.LA(1)

        monitored.setHiddenBefore(self._lastHiddenToken)
        self._lastHiddenToken = None

        self.consume()
        p = monitored

        while self._hideMask.member(self.LA(1).type) or \
                self.discardMask.member(self.LA(1).type):
            if self._hideMask.member(self.LA(1).type):
                p.setHiddenAfter(self.LA(1))
                if p != monitored:
                    self.LA(1).setHiddenBefore(p)
                p = self._lastHiddenToken = self.LA(1)
            self.consume()
        return monitored


class StringBuffer(object):
    """ StringBuffer """
    def __init__(self, a_string=None):
        if a_string:
            self._text = list(a_string)
        else:
            self._text = []

    def setLength(self, sz):
        if not sz:
            self._text = []
            return
        assert sz > 0
        if sz >= self.length():
            return
        # just reset to empty buffer
        self._text = self._text[0:sz]

    def length(self):
        return len(self._text)

    def append(self, c):
        self._text.append(c)

    def getString(self, a=None, length=None):
        """ return buffer as string.
        Arg 'a' is used as index into the buffer
        and 2nd argument shall be the length.
        If 2nd args is absent,
        we return chars till end of buffer starting with 'a'.
        """
        if not a:
            a = 0
        assert a >= 0
        if a >= len(self._text):
            return ""

        if not length:
            # no second argument
            L = self._text[a:]
        else:
            assert (a + length) <= len(self._text)
            b = a + length
            L = self._text[a:b]
        s = ""
        for x in L:
            s += x
        return s

    toString = getString   # alias

    def __str__(self):
        return str(self._text)


class Reader(object):
    """ Reader class
    When reading Japanese chars, it happens that a stream returns a 'char' of length 2.
    This looks like a bug in the appropriate codecs - but I'm  rather  unsure about this.
    Anyway, if this is the case,
    I'm going to split this string into a list of chars and put them  on  hold, i.e. on a  buffer.
    Next time when called we read from buffer until buffer is empty.
    """
    def __init__(self, stream):
        self._cin = stream
        self._buf = []

    def read(self, num):
        assert num == 1

        if len(self._buf):
            return self._buf.pop()

        c = self._cin.read(1)

        if not c or len(c) == 1:
            return c

        L = list(c)
        L.reverse()
        for x in L:
            self._buf.append(x)

        # read one character
        return self.read(1)


class CharScanner(TokenStream):
    """ CharScanner
    class members
    """
    NO_CHAR = 0
    EOF_CHAR = ''  # ## EOF shall be the empty string.

    def __init__(self, *argv, **kwargs):
        super().__init__()
        self._inputState = None
        self._saveConsumedInput = True
        self._tokenClass = None
        self._caseSensitive = True
        self._caseSensitiveLiterals = True
        self._literals = None
        self._tabsize = 8
        self._returnToken = None
        self._commitToPath = False
        self._traceDepth = 0
        self._text = StringBuffer()
        self._hashString = hash(self)
        self.setTokenObjectClass(CommonToken)
        self.setInput(*argv)

    def __iter__(self):
        return CharScannerIterator(self)

    def setInput(self, *argv):
        # case 1:
        # if there's no arg
        # we default to read from standard input
        if not argv:
            import sys
            self.setInput(sys.stdin)
            return

        # get 1st argument
        arg1 = argv[0]

        # case 2:
        # if arg1 is a string,
        # we assume it's a file name and  open  a  stream  using 2nd argument as open
        # mode. If there's no 2nd argument we fall back to
        # mode '+rb'.
        if is_string_type(arg1):
            f = open(arg1, "r")
            self.setInput(f)
            self.filename = arg1
            return

        # case 3:
        # if arg1 is a file we wrap it by a char buffer (
        # some additional checks?? No, can't do this in
        # general).
        if isinstance(arg1, IOBase):
            self.setInput(CharBuffer(arg1))
            return

        # case 4:
        # if arg1 is of type SharedLexerInputState we use
        # argument as is.
        if isinstance(arg1, LexerSharedInputState):
            self._inputState = arg1
            return

        # case 5:
        # check whether argument type is of type input
        # buffer. If so create a SharedLexerInputState and
        # go ahead.
        if isinstance(arg1, InputBuffer):
            self.setInput(LexerSharedInputState(arg1))
            return

        # case 6:
        # check whether argument type has a method read(int)
        # If so create CharBuffer ...
        try:
            if arg1.read:
                rd = Reader(arg1)
                cb = CharBuffer(rd)
                ss = LexerSharedInputState(cb)
                self._inputState = ss
            return
        except:
            pass

        # case 7:
        # raise wrong argument exception
        raise TypeError(argv)

    @property
    def tabSize(self):
        return self._tabsize

    @tabSize.setter
    def tabSize(self, size):
        self._tabsize = size

    @property
    def caseSensitive(self):
        return self._caseSensitive

    @caseSensitive.setter
    def caseSensitive(self, t):
        self._caseSensitive = t

    @property
    def caseSensitiveLiterals(self):
        return self._caseSensitiveLiterals

    @caseSensitiveLiterals.setter
    def caseSensitiveLiterals(self, literals):
        self._caseSensitiveLiterals = literals

    @property
    def column(self):
        return self._inputState.column

    @column.setter
    def column(self, c):
        self._inputState.column = c

    @property
    def commitToPath(self):
        return self._commitToPath

    @commitToPath.setter
    def commitToPath(self, commit):
        self._commitToPath = commit

    @property
    def filename(self):
        return self._inputState.filename

    @filename.setter
    def filename(self, f):
        self._inputState._filename = f

    @property
    def inputBuffer(self):
        return self._inputState.input

    @property
    def inputState(self):
        return self._inputState

    @inputState.setter
    def inputState(self, state):
        assert isinstance(state, LexerSharedInputState)
        self._inputState = state

    @property
    def line(self):
        return self._inputState.line

    @line.setter
    def line(self, line):
        self._inputState._line = line

    @property
    def text(self):
        return str(self._text)

    @text.setter
    def text(self, s):
        self.resetText()
        self._text.append(s)

    @property
    def tokenObject(self):
        return self._returnToken

    def LA(self, i):
        c = self._inputState.input.LA(i)
        if not self._caseSensitive:
            # E0006
            c = c.__class__.lower(c)
        return c

    def makeToken(self, a_type):
        try:
            # dynamically load a class
            assert self._tokenClass
            tok = self._tokenClass()
            tok._type = a_type
            tok._column = self._inputState.tokenStartColumn
            tok._line = self._inputState.tokenStartLine
            return tok
        except:
            self.panic("unable to create new token")
        return Token.badToken

    def mark(self):
        return self._inputState.input.mark()

    def _match_bitset(self, b):
        if b.member(self.LA(1)):
            self.consume()
        else:
            raise MismatchedCharException(self.LA(1), b, False, self)

    def _match_string(self, s):
        for c in s:
            if self.LA(1) == c:
                self.consume()
            else:
                raise MismatchedCharException(self.LA(1), c, False, self)

    def match(self, item):
        if is_string_type(item):
            return self._match_string(item)
        else:
            return self._match_bitset(item)

    def matchNot(self, c):
        if self.LA(1) != c:
            self.consume()
        else:
            raise MismatchedCharException(self.LA(1), c, True, self)

    def matchRange(self, c1, c2):
        if self.LA(1) < c1 or self.LA(1) > c2:
            raise MismatchedCharException(self.LA(1), c1, c2, False, self)
        else:
            self.consume()

    def newline(self):
        self._inputState.line += 1
        self._inputState.column = 1

    def tab(self):
        c = self.column
        nc = (((c - 1) // self._tabsize) + 1) * self._tabsize + 1
        self.column = nc

    def panic(self, s=''):
        print("CharScanner: panic: " + s)
        sys.exit(1)

    def reportError(self, s):
        if isinstance(s, Exception):
            print(f"{s}")
        if not self.filename:
            print(f"error: {s}")
        else:
            print(self.filename + ": error: " + str(s))

    def reportWarning(self, s):
        if not self.filename:
            print("warning: " + str(s))
        else:
            print(self.filename + ": warning: " + str(s))

    def resetText(self):
        self._text.setLength(0)
        self._inputState.tokenStartColumn = self._inputState.column
        self._inputState.tokenStartLine = self._inputState.line

    def rewind(self, pos):
        self._inputState.input.rewind(pos)

    def setTokenObjectClass(self, cl):
        self._tokenClass = cl

    def testForLiteral(self, token):
        if not token:
            return
        assert isinstance(token, Token)

        _type = token._type

        # special tokens can't be literals
        if _type in [SKIP, INVALID_TYPE, EOF_TYPE, NULL_TREE_LOOKAHEAD]:
            return

        _text = token._text
        if not _text:
            return

        assert is_string_type(_text)
        _type = self.testLiteralsTable(_text, _type)
        token._type = _type
        return _type

    def testLiteralsTable(self, *args):
        if is_string_type(args[0]):
            s = args[0]
            i = args[1]
        else:
            s = self._text.getString()
            i = args[0]

        # check whether integer has been given
        if not isinstance(i, int):
            assert isinstance(i, int)

        # check whether we have a dict
        assert isinstance(self._literals, dict)
        try:
            # E0010
            if not self._caseSensitiveLiterals:
                s = s.__class__.lower(s)
            i = self._literals[s]
        except:
            pass
        return i

    def toLower(self, c):
        return c.__class__.lower()

    def traceIndent(self):
        print(' ' * self._traceDepth)

    def traceIn(self, rname):
        self._traceDepth += 1
        self.traceIndent()
        print("> lexer %s c== %s" % (rname, self.LA(1)))

    def traceOut(self, rname):
        self.traceIndent()
        print("< lexer %s c== %s" % (rname, self.LA(1)))
        self._traceDepth -= 1

    def uponEOF(self):
        pass

    def append(self, c):
        if self._saveConsumedInput:
            self._text.append(c)

    def commit(self):
        self._inputState.input.commit()

    def consume(self):
        if not self._inputState.guessing:
            c = self.LA(1)
            if self._caseSensitive:
                self.append(c)
            else:
                # use input.LA(), not LA(), to get original case
                # CharScanner.LA() would toLower it.
                c = self._inputState.input.LA(1)
                self.append(c)

            if c and c in "\t":
                self.tab()
            else:
                self._inputState.column += 1
        self._inputState.input.consume()

    def consumeUntil_char(self, c):
        """ Consume chars until one matches the given char"""
        while self.LA(1) != EOF_CHAR and self.LA(1) != c:
            self.consume()

    def consumeUntil_bitset(self, bitset):
        """ Consume chars until one matches the given bitset
        Questionable implementation (not used).
        see https://pypi.org/project/bitsets/ for details """
        while self.LA(1) != EOF_CHAR:
            if bitset.member(self.LA(1)):
                continue
            self.consume()

    #
    def default(self, la1):
        """ If symbol seen is EOF then generate and set token,
        otherwise throw exception.
        """
        if not la1:
            self.uponEOF()
            self._returnToken = self.makeToken(EOF_TYPE)
        else:
            self.raise_NoViableAlt(la1)

    def filter_default(self, la1, *args):
        if not la1:
            self.uponEOF()
            self._returnToken = self.makeToken(EOF_TYPE)
            return

        if not args:
            self.consume()
            raise TryAgain()
        else:
            # apply filter object
            self.commit()
            try:
                func = args[0]
                args = args[1:]
                func(*args)
            except RecognitionException as ex:
                # catastrophic failure
                self.reportError(ex)
                self.consume()
            raise TryAgain()

    def raise_NoViableAlt(self, la1=None):
        if not la1:
            la1 = self.LA(1)
        fname = self.filename
        line = self.line
        col = self.column
        raise NoViableAltForCharException(la1, fname, line, col)

    def set_return_token(self, _create, _token, _ttype, _offset):
        if _create and not _token and (not _ttype == SKIP):
            a_string = self._text.getString(_offset)
            _token = self.makeToken(_ttype)
            _token.text = a_string
        self._returnToken = _token
        return _token


class CharScannerIterator(object):
    """ CharScannerIterator """

    def __init__(self, inst):
        if isinstance(inst, CharScanner):
            self._inst = inst
            return
        raise TypeError("CharScannerIterator requires CharScanner object")

    def __next__(self):
        assert self._inst
        item = self._inst.nextToken
        if not item or (hasattr(item, "isEOF") and item.isEOF):
            raise StopIteration()
        return item


class BitSet(object):
    """ BitSet
    I'm assuming here that a long is 64bits.
    It appears however, that a long is of any size.
    That means we can use a single long as the bitset (!),
    i.e. Python would do almost all the work (TBD).
    """
    BITS = 64
    NIBBLE = 4
    LOG_BITS = 6
    MOD_MASK = BITS - 1

    def __init__(self, data=None):
        if not data:
            BitSet.__init__(self, [int(0)])
            return
        if isinstance(data, int):
            BitSet.__init__(self, [int(data)])
            return
        if isinstance(data, int):
            BitSet.__init__(self, [data])
            return
        if not isinstance(data, list):
            raise TypeError("BitSet requires integer, long, or " +
                            "list argument")
        for x in data:
            if not isinstance(x, int):
                raise TypeError(self, "List argument item is " +
                                "not a long: %s" % x)
        self._data = data

    def __str__(self):
        bits = len(self._data) * BitSet.BITS
        s = ""
        for i in range(0, bits):
            if self.at(i):
                s += "1"
            else:
                s += "o"
            if not ((i + 1) % 10):
                s += '|%s|' % (i + 1)
        return s

    def __repr__(self):
        return str(self)

    def member(self, item):
        if not item:
            return False

        if isinstance(item, int):
            return self.at(item)

        if not is_string_type(item):
            raise TypeError(self, "char or unichar expected: %s" % item)

        # char is a (unicode) string with at most length 1, i.e. a char.

        if len(item) != 1:
            raise TypeError(self, "char expected: %s" % item)

        # handle ASCII/UNICODE char
        num = ord(item)

        # check whether position num is in bitset
        return self.at(num)

    def wordNumber(self, bit):
        return bit >> BitSet.LOG_BITS

    def bitMask(self, bit):
        pos = bit & BitSet.MOD_MASK  # bit mod BITS
        return 1 << pos

    def set(self, bit, on=True):
        # grow bitset as required (use with care!)
        i = self.wordNumber(bit)
        mask = self.bitMask(bit)
        if i >= len(self._data):
            d = i - len(self._data) + 1
            for x in range(0, d):
                self._data.append(0)
            assert len(self._data) == i + 1
        if on:
            self._data[i] |= mask
        else:
            self._data[i] &= (~mask)

    # make add an alias for set
    add = set

    def off(self, bit, off=True):
        self.set(bit, not off)

    def at(self, bit):
        i = self.wordNumber(bit)
        v = self._data[i]
        m = self.bitMask(bit)
        return v & m


def illegal_arg_ex(func):
    raise ValueError(
        "%s is only valid if parser is built for debugging" %
        (func.__name__))


class RuntimeException(Exception):
    """A custom exception"""
    pass


def runtime_ex(func):
    raise RuntimeException(
        "%s is only valid if parser is built for debugging" %
        (func.__name__))


class TokenBuffer(object):
    """ TokenBuffer """
    def __init__(self, stream):
        self._input = stream
        self._nMarkers = 0
        self._markerOffset = 0
        self._numToConsume = 0
        self._queue = Queue()

    def reset(self):
        self._nMarkers = 0
        self._markerOffset = 0
        self._numToConsume = 0
        self._queue.reset()

    def consume(self):
        self._numToConsume += 1

    def fill(self, amount):
        self.syncConsume()
        while self._queue.length() < (amount + self._markerOffset):
            self._queue.append(self._input.nextToken())

    @property
    def input(self):
        return self._input

    def LA(self, k):
        self.fill(k)
        return self._queue.elementAt(self._markerOffset + k - 1).type

    def LT(self, k):
        self.fill(k)
        return self._queue.elementAt(self._markerOffset + k - 1)

    def mark(self):
        self.syncConsume()
        self._nMarkers += 1
        return self._markerOffset

    def rewind(self, mark):
        self.syncConsume()
        self._markerOffset = mark
        self._nMarkers -= 1

    def syncConsume(self):
        while self._numToConsume > 0:
            if self._nMarkers > 0:
                # guess mode -- leave leading characters and bump offset.
                self._markerOffset += 1
            else:
                # normal mode -- remove first character
                self._queue.removeFirst()
            self._numToConsume -= 1

    def __str__(self):
        return "(%s,%s,%s,%s,%s)" % (
            self._input,
            self._nMarkers,
            self._markerOffset,
            self._numToConsume,
            self._queue)

    def __repr__(self):
        return str(self)


class ParserSharedInputState(object):
    """ ParserSharedInputState """

    def __init__(self):
        self._input = None
        self._guessing = 0
        self._filename = None
        self.reset()

    def reset(self):
        self._guessing = 0
        self._filename = None
        if self._input:
            self._input.reset()

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, value):
        self._input = value

    @property
    def guessing(self):
        return self._guessing

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value


class Parser(object):
    """ Parser """

    def __init__(self, *args, **kwargs):
        self._debugMode = False
        self._tokenNames = None
        self._returnAST = None
        self._astFactory = None
        self._tokenTypeToASTClassMap = {}
        self._ignoreInvalidDebugCalls = False
        self._traceDepth = 0
        if not args:
            self._inputState = ParserSharedInputState()
            return
        arg0 = args[0]
        assert isinstance(arg0, ParserSharedInputState)
        self._inputState = arg0
        return

    def addMessageListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            illegal_arg_ex(self.addMessageListener)

    def addParserListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            illegal_arg_ex(self.addParserListener)

    def addParserMatchListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            illegal_arg_ex(self.addParserMatchListener)

    def addParserTokenListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            illegal_arg_ex(self.addParserTokenListener)

    def addSemanticPredicateListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            illegal_arg_ex(self.addSemanticPredicateListener)

    def addSyntacticPredicateListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            illegal_arg_ex(self.addSyntacticPredicateListener)

    def addTraceListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            illegal_arg_ex(self.addTraceListener)

    def consume(self):
        raise NotImplementedError()

    def consumeUntil_type(self, tokenType):
        while self.LA(1) != EOF_TYPE and self.LA(1) != tokenType:
            self.consume()

    def consumeUntil_bitset(self, a_set):
        while self.LA(1) != EOF_TYPE and not a_set.member(self.LA(1)):
            self.consume()

    def consumeUntil(self, arg):
        if isinstance(arg, int):
            self.consumeUntil_type(arg)
        else:
            self.consumeUntil_bitset(arg)

    def defaultDebuggingSetup(self):
        pass

    @property
    def tokenTypeToASTClassMap(self):
        return self._tokenTypeToASTClassMap

    @property
    def AST(self):
        return self._returnAST

    @property
    def ASTFactory(self):
        return self._astFactory

    @ASTFactory.setter
    def ASTFactory(self, f):
        self._astFactory = f

    @property
    def filename(self):
        if hasattr(self._inputState, 'filename'):
            return self._inputState.filename
        return None

    @filename.setter
    def filename(self, f):
        self._inputState.filename = f

    def setASTNodeClass(self, cl):
        self._astFactory.setASTNodeType(cl)

    def setASTNodeType(self, nodeType):
        self.setASTNodeClass(nodeType)

    @property
    def inputState(self):
        return self._inputState

    @inputState.setter
    def inputState(self, state):
        self._inputState = state

    def getTokenName(self, num):
        return self._tokenNames[num]

    @property
    def tokenNames(self):
        return self._tokenNames

    @tokenNames.setter
    def tokenNames(self, tokenNames):
        self._tokenNames = tokenNames

    @property
    def isDebugMode(self):
        return self._debugMode

    def setDebugMode(self, debugMode):
        if not self._ignoreInvalidDebugCalls:
            runtime_ex(self.setDebugMode)

    def setIgnoreInvalidDebugCalls(self, value):
        self._ignoreInvalidDebugCalls = value

    def setTokenBuffer(self, t):
        self._inputState.input = t

    def LA(self, i):
        raise NotImplementedError()

    def LT(self, i):
        raise NotImplementedError()

    def mark(self):
        return self._inputState.input.mark()

    def _match_int(self, t):
        if self.LA(1) != t:
            raise MismatchedTokenException(
                self._tokenNames, self.LT(1), t, False, self.filename)
        else:
            self.consume()

    def _match_set(self, b):
        if not b.member(self.LA(1)):
            raise MismatchedTokenException(
                self._tokenNames, self.LT(1), b, False, self.filename)
        else:
            self.consume()

    def match(self, a_set):
        if isinstance(a_set, int):
            self._match_int(a_set)
            return
        if isinstance(a_set, BitSet):
            self._match_set(a_set)
            return
        raise TypeError("Parser.match requires integer ot BitSet argument")

    def matchNot(self, t):
        if self.LA(1) == t:
            raise MismatchedTokenException(
                self._tokenNames, self.LT(1), t, True, self.filename)
        else:
            self.consume()

    def removeMessageListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            runtime_ex(self.removeMessageListener)

    def removeParserListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            runtime_ex(self.removeParserListener)

    def removeParserMatchListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            runtime_ex(self.removeParserMatchListener)

    def removeParserTokenListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            runtime_ex(self.removeParserTokenListener)

    def removeSemanticPredicateListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            runtime_ex(self.removeSemanticPredicateListener)

    def removeSyntacticPredicateListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            runtime_ex(self.removeSyntacticPredicateListener)

    def removeTraceListener(self, listener):
        if not self._ignoreInvalidDebugCalls:
            runtime_ex(self.removeTraceListener)

    def reportError(self, x):
        fmt = "syntax error:"
        f = self.filename
        if f:
            fmt = ("%s:" % f) + fmt
        if isinstance(x, Token):
            line = x.column
            col = x.line
            text = x.text
            fmt = fmt + 'unexpected symbol at line %s (column %s) : "%s"'
            print((sys.stderr, fmt % (line, col, text)))
        else:
            print((sys.stderr, fmt, str(x)))

    def reportWarning(self, x):
        f = self.filename
        if f:
            print("%s:warning: %s" % (f, str(x)))
        else:
            print("warning: %s" % (str(x)))

    def rewind(self, pos):
        self._inputState.input.rewind(pos)

    def traceIndent(self):
        print(" " * self._traceDepth)

    def traceIn(self, rname):
        self._traceDepth += 1
        self.trace("> ", rname)

    def traceOut(self, rname):
        self.trace("< ", rname)
        self._traceDepth -= 1

    def addASTChild(self, currentAST, child):
        if not child:
            return
        if not currentAST.root:
            currentAST.root = child
        elif not currentAST._child:
            currentAST.root.setFirstChild(child)
        else:
            currentAST._child.setNextSibling(child)
        currentAST._child = child
        currentAST.advanceChildToEnd()

    def makeASTRoot(self, currentAST, root):
        if not root:
            return
        # Add the current root as a child of new root
        root.addChild(currentAST.root)
        # The new current child is the last sibling of the old root
        currentAST._child = currentAST.root
        currentAST.advanceChildToEnd()
        # Set the new root
        currentAST.root = root

    def trace(self, param, rname):
        pass


class LLkParser(Parser):
    """ LLkParser """

    def __init__(self, *args, **kwargs):
        try:
            arg1 = args[0]
        except:
            arg1 = 1

        if isinstance(arg1, int):
            super(LLkParser, self).__init__()
            self._k = arg1
            return

        if isinstance(arg1, ParserSharedInputState):
            super(LLkParser, self).__init__(arg1)
            self.set_k(1, *args)
            return

        if isinstance(arg1, TokenBuffer):
            super(LLkParser, self).__init__()
            self.setTokenBuffer(arg1)
            self.set_k(1, *args)
            return

        if isinstance(arg1, TokenStream):
            super(LLkParser, self).__init__()
            tokenBuf = TokenBuffer(arg1)
            self.setTokenBuffer(tokenBuf)
            self.set_k(1, *args)
            return

        # unknown argument
        raise TypeError("LLkParser requires integer, " +
                        "ParserSharedInputStream or TokenStream argument")

    def consume(self):
        self._inputState.input.consume()

    def LA(self, i):
        return self._inputState.input.LA(i)

    def LT(self, i):
        return self._inputState.input.LT(i)

    def set_k(self, index, *args):
        try:
            self._k = args[index]
        except:
            self._k = 1

    def trace(self, ee, rname):
        print(type(self))
        self.traceIndent()
        guess = ""
        if self._inputState.guessing > 0:
            guess = " [guessing]"
        print(ee + rname + guess)
        for i in range(1, self._k + 1):
            if i != 1:
                print(", ")
            if self.LT(i):
                v = self.LT(i).text
            else:
                v = "null"
            print("LA(%s) == %s" % (i, v))
        print("\n")

    def traceIn(self, rname):
        self._traceDepth += 1
        self.trace("> ", rname)

    def traceOut(self, rname):
        self.trace("< ", rname)
        self._traceDepth -= 1


class TreeParserSharedInputState(object):
    """ TreeParserSharedInputState """
    def __init__(self):
        self._guessing = 0

    @property
    def guessing(self):
        return self._guessing


class TreeParser(object):
    """ TreeParser """

    def __init__(self, *args, **kwargs):
        self._inputState = TreeParserSharedInputState()
        self._retTree = None
        self._tokenNames = []
        self._returnAST = None
        self._astFactory = ASTFactory()
        self._traceDepth = 0

    @property
    def AST(self):
        return self._returnAST

    @property
    def ASTFactory(self):
        return self._astFactory

    def getTokenName(self, num):
        return self._tokenNames[num]

    @property
    def tokenNames(self):
        return self._tokenNames

    def match(self, t, a_set):
        assert isinstance(a_set, int) or isinstance(a_set, BitSet)
        if not t or t == ASTNULL:
            raise MismatchedTokenException(self.tokenNames, t, a_set, False)

        if isinstance(a_set, int) and t.type != a_set:
            raise MismatchedTokenException(self.tokenNames, t, a_set, False)

        if isinstance(a_set, BitSet) and not a_set.member(t.type):
            raise MismatchedTokenException(self.tokenNames, t, a_set, False)

    def matchNot(self, t, ttype):
        if not t or (t == ASTNULL) or (t.type == ttype):
            raise MismatchedTokenException(self.tokenNames, t, ttype, True)

    def reportError(self, ex):
        print((sys.stderr, "error:", ex))

    def reportWarning(self, s):
        print("warning:", s)

    def setASTFactory(self, f):
        self._astFactory = f

    def setASTNodeType(self, nodeType):
        self.setASTNodeClass(nodeType)

    def setASTNodeClass(self, nodeType):
        self._astFactory.setASTNodeType(nodeType)

    def traceIndent(self):
        print(" " * self._traceDepth)

    def traceIn(self, rname, t):
        self._traceDepth += 1
        self.traceIndent()
        print("> " + rname + "(" +
              if_else(t, str(t), "null") + ")" +
              if_else(self._inputState.guessing > 0, "[guessing]", ""))

    def traceOut(self, rname, t):
        self.traceIndent()
        print("< " + rname + "(" +
              if_else(t, str(t), "null") + ")" +
              if_else(self._inputState.guessing > 0, "[guessing]", ""))
        self._traceDepth -= 1

    def addASTChild(self, currentAST, child):
        if not child:
            return
        if not currentAST.root:
            currentAST.root = child
        elif not currentAST._child:
            currentAST.root.setFirstChild(child)
        else:
            currentAST._child.setNextSibling(child)
        currentAST._child = child
        currentAST.advanceChildToEnd()

    def makeASTRoot(self, currentAST, root):
        if not root:
            return
        # Add the current root as a child of new root
        root.addChild(currentAST.root)
        # The new current child is the last sibling of the old root
        currentAST._child = currentAST.root
        currentAST.advanceChildToEnd()
        # Set the new root
        currentAST.root = root


def rightmost(ast):
    """ return the right most node in the AST """
    if ast:
        while ast.right:
            ast = ast.right
    return ast


def cmptree(s, t, partial):
    """ compare two AST returning if they are similar or not """
    while s and t:
        # as a quick optimization, check roots first.
        if not s.equals(t):
            return False

        # if roots match, do full list match test on children.
        if not cmptree(s.firstChild, t.firstChild, partial):
            return False

        s = s.nextSibling
        t = t.nextSibling

    r = if_else(partial, not t, not s and not t)
    return r


class AST(object):
    """ Abstract syntax tree (AST) """
    def __init__(self):
        pass

    def addChild(self, c):
        pass

    def equals(self, t):
        return False

    def equalsList(self, t):
        return False

    def equalsListPartial(self, t):
        return False

    def equalsTree(self, t):
        return False

    def equalsTreePartial(self, t):
        return False

    def findAll(self, tree):
        return None

    def findAllPartial(self, subtree):
        return None

    @property
    def firstChild(self):
        return self

    @property
    def nextSibling(self):
        return self

    @property
    def text(self):
        return ""

    @text.setter
    def text(self, text):
        pass

    @property
    def type(self):
        return INVALID_TYPE

    @type.setter
    def type(self, ttype):
        pass

    @property
    def line(self):
        return 0

    @property
    def column(self):
        return 0

    @property
    def numberOfChildren(self):
        return 0

    def initialize(self, t, txt=None):
        if txt is None:
            pass
        pass

    def setFirstChild(self, c):
        pass

    def setNextSibling(self, n):
        pass

    def toString(self):
        return self.text

    __str__ = toString

    def toStringList(self):
        return self.text

    def toStringTree(self):
        return self.text


class ASTNULLType(AST):
    """ ASTNULLType : A Null AST
    There is only one instance of this class
    """
    def __init__(self):
        super().__init__()
        pass

    @property
    def text(self):
        return "<ASTNULL>"

    @property
    def type(self):
        return NULL_TREE_LOOKAHEAD


class BaseAST(AST):
    """ BaseAST """
    verboseStringConversion = False
    tokenNames = None

    def __init__(self):
        super().__init__()
        self._down = None   # child
        self._right = None  # sibling

    def addChild(self, node):
        if not node:
            return
        t = rightmost(self._down)
        if t:
            t._right = node
        else:
            assert not self._down
            self._down = node

    @property
    def numberOfChildren(self):
        t = self._down
        n = 0
        while t:
            n += 1
            t = t.right
        return n

    def doWorkForFindAll(self, v, target, partialMatch):
        sibling = self

        while sibling:
            c1 = partialMatch and sibling.equalsTreePartial(target)
            if c1:
                v.append(sibling)
            else:
                c2 = not partialMatch and sibling.equalsTree(target)
                if c2:
                    v.append(sibling)

            # regardless of match or not, check any children for matches
            if sibling.firstChild:
                sibling.firstChild.doWorkForFindAll(v, target, partialMatch)

            sibling = sibling.nextSibling

    def equals(self, t):
        """ Is node t equal to 'self' in terms of token type and text? """
        if not t:
            return False
        return self.text == t.text and self.type == t.type

    def equalsList(self, t):
        """ Is t an exact structural and equals() match of this tree.
        The 'self' reference is considered the start of a sibling list.
        """
        return cmptree(self, t, partial=False)

    def equalsListPartial(self, tr):
        """ Is 'tr' a subtree of this list?
        The siblings of the root are NOT ignored."""
        return cmptree(self, tr, partial=True)

    def equalsTree(self, t):
        """ Is tree rooted at 'self' equal to 't'?
        The siblings of 'self' are ignored."""
        return self.equals(t) and \
            cmptree(self.firstChild, t.firstChild, partial=False)

    def equalsTreePartial(self, tr):
        """ Is 'tr' a subtree of the tree rooted at 'self'?
        The siblings of 'self' are ignored."""
        if not tr:
            return True
        return self.equals(tr) and cmptree(
            self.firstChild, tr.firstChild, partial=True)

    def findAll(self, target):
        """ Walk the tree looking for all exact subtree matches.
        Return an ASTEnumerator that lets the caller walk
        the list of subtree roots found herein."""
        roots = []

        # the empty tree cannot result in an enumeration
        if not target:
            return None
        # find all matches recursively
        self.doWorkForFindAll(roots, target, False)
        return roots

    def findAllPartial(self, sub):
        """ Walk the tree looking for all subtrees.
        Return an ASTEnumerator that lets the caller walk
        the list of subtree roots found herein."""
        roots = []

        # the empty tree cannot result in an enumeration
        if not sub:
            return None

        self.doWorkForFindAll(roots, sub, True) # ## find all matches recursively
        return roots

    @property
    def firstChild(self):
        """ Get the first child of this node None if not children """
        return self._down

    @property
    def nextSibling(self):
        """ Get the next sibling in line after this one """
        return self._right

    @property
    def text(self):
        """ Get the token text for this node """
        return ""

    @text.setter
    def text(self, text):
        """ Set the token text for this node """
        pass

    @property
    def type(self):
        """ Get the token type for this node """
        return 0

    @type.setter
    def type(self, ttype):
        """ Set the token type for this node """
        pass

    @property
    def line(self):
        return 0

    @property
    def column(self):
        return 0

    def removeChildren(self):
        """ Remove all children """
        self._down = None

    def setFirstChild(self, c):
        self._down = c

    def setNextSibling(self, n):
        self._right = n

    @staticmethod
    def setVerboseStringConversion(verbose, names):
        BaseAST.verboseStringConversion = verbose
        BaseAST.tokenNames = names

    setVerboseStringConversion = staticmethod(setVerboseStringConversion)

    @staticmethod
    def getTokenNames():
        """ Return an array of strings that maps token ID to its text. """
        return BaseAST.tokenNames

    def toString(self):
        return self.text

    def toStringList(self):
        """ return tree as lisp string - sibling included """
        ts = self.toStringTree()
        sib = self.nextSibling
        if sib:
            ts += sib.toStringList()
        return ts

    __str__ = toStringList

    def toStringTree(self):
        """ return tree as string - siblings ignored """
        ts = ""
        kid = self.firstChild
        if kid:
            ts += " ("
        ts += " " + self.toString()
        if kid:
            ts += kid.toStringList()
            ts += " )"
        return ts


class CommonAST(BaseAST):
    """ Common AST node implementation : CommonAST """
    def __init__(self, token=None):
        super(CommonAST, self).__init__()
        self._ttype = INVALID_TYPE
        self._text = "<no text>"
        self._line = 0
        self._column = 0
        self.initialize(token)
        # assert self.text

    @property
    def text(self):
        """ Get the token text for this node """
        return self._text

    @text.setter
    def text(self, text_):
        """ Set the token text for this node """
        assert is_string_type(text_)
        self._text = text_

    @property
    def type(self):
        """ Get the token type for this node """
        return self._ttype

    @type.setter
    def type(self, ttype_):
        """ Set the token type for this node """
        assert isinstance(ttype_, int)
        self._ttype = ttype_

    @property
    def line(self):
        """ Get the line for this node """
        return self._line

    @property
    def column(self):
        """ Get the column for this node """
        return self._column

    def initialize(self, *args):
        if not args:
            return

        arg0 = args[0]

        if isinstance(arg0, int):
            arg1 = args[1]
            self.type = arg0
            self.text = arg1
            return

        if isinstance(arg0, AST) or isinstance(arg0, Token):
            self.text = arg0.text
            self.type = arg0.type
            self._line = arg0.line
            self._column = arg0.column
            return


class CommonASTWithHiddenTokens(CommonAST):
    """ CommonASTWithHiddenTokens """

    def __init__(self, *args):
        super().__init__(*args)
        self._hiddenBefore = None
        self._hiddenAfter = None

    @property
    def hiddenAfter(self):
        return self._hiddenAfter

    @property
    def hiddenBefore(self):
        return self._hiddenBefore

    def initialize(self, *args):
        CommonAST.initialize(self, *args)
        if args and isinstance(args[0], Token):
            assert isinstance(args[0], CommonHiddenStreamToken)
            self._hiddenBefore = args[0].hiddenBefore
            self._hiddenAfter = args[0].hiddenAfter


class ASTPair(object):
    """ AST Pair """
    def __init__(self):
        self._root = None    # current root of tree
        self._child = None   # current child to which siblings are added

    def advanceChildToEnd(self):
        """ Make sure that child is the last sibling """
        if self._child:
            while self._child.nextSibling:
                self._child = self._child.nextSibling

    def copy(self):
        """ Copy an ASTPair
        Don't call it clone() because we want type-safety. """
        tmp = ASTPair()
        tmp.root = self._root
        tmp.child = self._child
        return tmp

    def toString(self):
        r = if_else(not self._root, "null", self._root.text)
        c = if_else(not self._child, "null", self._child.text)
        return "[%s,%s]" % (r, c)

    __str__ = toString
    __repr__ = toString

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, value):
        self._root = value


class ASTFactory(object):
    """ ASTFactory """

    def __init__(self, table=None):
        self._class = None
        self._classmap = if_else(table, table, None)

    def create(self, *args):
        if not args:
            return self.create(INVALID_TYPE)

        arg0 = args[0]
        arg1 = None
        arg2 = None

        try:
            arg1 = args[1]
            arg2 = args[2]
        except:
            pass

        # ctor(int)
        if isinstance(arg0, int) and not arg2:
            # get class for 'self' type
            c = self.getASTNodeType(arg0)
            t = self.create(c)
            if t:
                t.initialize(arg0, if_else(arg1, arg1, ""))
            return t

        # ctor(int,something)
        if isinstance(arg0, int) and arg2:
            t = self.create(arg2)
            if t:
                t.initialize(arg0, arg1)
            return t

        # ctor(AST)
        if isinstance(arg0, AST):
            t = self.create(arg0.type)
            if t:
                t.initialize(arg0)
            return t

        # ctor(token)
        if isinstance(arg0, Token) and not arg1:
            ttype = arg0._type
            assert isinstance(ttype, int)
            t = self.create(ttype)
            if t:
                t.initialize(arg0)
            return t

        # ctor(token,class)
        if isinstance(arg0, Token) and arg1:
            assert isinstance(arg1, type)
            assert issubclass(arg1, AST)
            # this creates instance of 'arg1' using 'arg0' as
            # argument. Wow, that's magic!
            t = arg1(arg0)
            assert t and isinstance(t, AST)
            return t

        # ctor(class)
        if isinstance(arg0, type):
            # next statement creates instance of type (!)
            t = arg0()
            assert isinstance(t, AST)
            return t

    def setASTNodeClass(self, className=None):
        if not className:
            return
        assert isinstance(className, type)
        assert issubclass(className, AST)
        self._class = className

    # kind of misnomer - use setASTNodeClass instead.
    setASTNodeType = setASTNodeClass

    @property
    def ASTNodeClass(self):
        return self._class

    @property
    def tokenTypeToASTClassMap(self):
        return self._classmap

    def setTokenTypeToASTClassMap(self, amap):
        self._classmap = amap

    def error(self, e):
        import sys
        print((sys.stderr, e))

    def setTokenTypeASTNodeType(self, tokenType, className):
        """
        Specify a mapping between a token type and a (AST) class.
        """
        if not self._classmap:
            self._classmap = {}

        if not className:
            try:
                del self._classmap[tokenType]
            except:
                pass
        else:
            # here we should also perform actions to ensure that
            # a. class can be loaded
            # b. class is a subclass of AST
            assert isinstance(className, type)
            assert issubclass(className, AST)
            # enter the class
            self._classmap[tokenType] = className

    def getASTNodeType(self, tokenType):
        """
        For a given token type return the AST node type.
        First we look up a mapping table, second we try _class,
        and finally we resolve to "antlr.CommonAST".
        """

        # first
        if self._classmap:
            try:
                c = self._classmap[tokenType]
                if c:
                    return c
            except:
                pass
        # second
        if self._class:
            return self._class

        # default
        return CommonAST

    def dup(self, t):
        """ methods that have been moved to file scope
        - just listed here to be somewhat consistent with original API
        """
        return dup(t, self)

    def dupList(self, t):
        return dupList(t, self)

    def dupTree(self, t):
        return dupTree(t, self)

    # methods moved to other classes
    # 1. makeASTRoot  -> Parser
    # 2. addASTChild  -> Parser

    # non-standard: create alias for longish method name
    maptype = setTokenTypeASTNodeType


class ASTVisitor(object):
    """ ASTVisitor """
    def __init__(self, *args):
        pass

    def visit(self, ast):
        pass


ASTNULL = ASTNULLType()


def make(*nodes):
    if not nodes:
        return None

    for i in range(0, len(nodes)):
        node = nodes[i]
        if node:
            assert isinstance(node, AST)

    root = nodes[0]
    tail = None
    if root:
        root.setFirstChild(None)

    for i in range(1, len(nodes)):
        if not nodes[i]:
            continue
        if not root:
            root = tail = nodes[i]
        elif not tail:
            root.setFirstChild(nodes[i])
            tail = root.firstChild
        else:
            tail.setNextSibling(nodes[i])
            tail = tail.nextSibling

        # Chase tail to last sibling
        while tail.nextSibling:
            tail = tail.nextSibling
    return root


def dup(t, factory):
    if not t:
        return None

    if factory:
        dup_t = factory.create(t.__class__)
    else:
        raise TypeError("dup function requires ASTFactory argument")
    dup_t.initialize(t)
    return dup_t


def dupList(t, factory):
    result = dupTree(t, factory)
    nt = result
    while t:
        # for each sibling of the root
        t = t.nextSibling
        nt.setNextSibling(dupTree(t, factory))
        nt = nt.nextSibling
    return result


def dupTree(t, factory):
    result = dup(t, factory)
    if t:
        result.setFirstChild(dupList(t.firstChild, factory))
    return result

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# $Id: antlr.py,v 1.1.1.1 2005/02/02 10:24:36 geronimo Exp $

# Local Variables:    ***
# mode: python        ***
# py-indent-offset: 4 ***
# End:                ***
