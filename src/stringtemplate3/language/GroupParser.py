# ## $ANTLR 2.7.7 (2006-11-01): "group.g" -> "GroupParser.py"$
# ## import antlr and other modules ..
import sys

# ## header action >>>
from .ASTExpr import *
import stringtemplate3
import traceback
# ## header action <<< 
# ## preamble action>>>

# ## preamble action <<<

# ## import antlr.Token

# ## >>>The Known Token Types <<<
SKIP = antlr.SKIP
INVALID_TYPE = antlr.INVALID_TYPE
EOF_TYPE = antlr.EOF_TYPE
EOF = antlr.EOF
NULL_TREE_LOOKAHEAD = antlr.NULL_TREE_LOOKAHEAD
MIN_USER_TYPE = antlr.MIN_USER_TYPE
LITERAL_group = 4
ID = 5
COLON = 6
LITERAL_implements = 7
COMMA = 8
SEMI = 9
AT = 10
DOT = 11
LPAREN = 12
RPAREN = 13
DEFINED_TO_BE = 14
STRING = 15
BIGSTRING = 16
ASSIGN = 17
ANONYMOUS_TEMPLATE = 18
LBRACK = 19
RBRACK = 20
LITERAL_default = 21
STAR = 22
PLUS = 23
OPTIONAL = 24
SL_COMMENT = 25
ML_COMMENT = 26
NL = 27
WS = 28


class Parser(antlr.LLkParser):
    """
    Match a group of template definitions beginning with a group name declaration.
    Templates are enclosed in double-quotes or <<...>> quotes for multi-line templates.
    Template names have arg lists that indicate the cardinality of the attribute:
    present, optional, zero-or-more, one-or-more.

    Here is a sample group file:
         group nfa;
         // an NFA has edges and states
         nfa(states,edges) ::= <<
            digraph NFA {
               rankdir=LR;
               <states; separator="\\n">
               <edges; separator="\\n">
            }
        >>
        state(name) ::= "node [shape = circle]; <name>;"
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tokenNames = _tokenNames
        # ## __init__ header action >>>
        self._group = None
        # ## __init__ header action <<<

    # user action >>>
    def reportError(self, e):
        if self._group:
            self._group.error("template group parse error", e)
        else:
            sys.stderr.write("template group parse error: " + str(e) + '\n')
            traceback.print_exc()
    # user action <<<

    def group(self, g):

        name = None
        s = None
        i = None
        i2 = None
        self._group = g
        try:  # # for error handling
            pass
            self.match(LITERAL_group)
            name = self.LT(1)
            self.match(ID)
            g._name = name.text
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [COLON]:
                pass
                self.match(COLON)
                s = self.LT(1)
                self.match(ID)
                g._superGroup = s.text
            elif la1 and la1 in [LITERAL_implements, SEMI]:
                pass
            else:
                raise antlr.NoViableAltException(self.LT(1), self.filename)

            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [LITERAL_implements]:
                pass
                self.match(LITERAL_implements)
                i = self.LT(1)
                self.match(ID)
                g.implementInterface(i.text)
                while True:
                    if self.LA(1) == COMMA:
                        pass
                        self.match(COMMA)
                        i2 = self.LT(1)
                        self.match(ID)
                        g.implementInterface(i2.text)
                    else:
                        break

            elif la1 and la1 in [SEMI]:
                pass
            else:
                raise antlr.NoViableAltException(self.LT(1), self.filename)

            self.match(SEMI)
            while True:
                if (self.LA(1) == ID or self.LA(1) == AT) and (
                        self.LA(2) == ID or self.LA(2) == LPAREN or self.LA(2) == DEFINED_TO_BE) and (
                        self.LA(3) == ID or self.LA(3) == DOT or self.LA(3) == RPAREN):
                    pass
                    self.template(g)
                elif (self.LA(1) == ID) and (self.LA(2) == DEFINED_TO_BE) and (self.LA(3) == LBRACK):
                    pass
                    self.mapdef(g)
                else:
                    break

            self.match(EOF_TYPE)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)

    def template(self, g):

        scope = None
        region = None
        name = None
        t = None
        bt = None
        alias = None
        target = None
        formalArgs = {}
        st = None
        ignore = False
        templateName = None
        line = self.LT(1).line
        try:  # # for error handling
            if (self.LA(1) == ID or self.LA(1) == AT) and (self.LA(2) == ID or self.LA(2) == LPAREN):
                pass
                la1 = self.LA(1)
                if False:
                    pass
                elif la1 and la1 in [AT]:
                    pass
                    self.match(AT)
                    scope = self.LT(1)
                    self.match(ID)
                    self.match(DOT)
                    region = self.LT(1)
                    self.match(ID)
                    templateName = g.getMangledRegionName(scope.text, region.text)
                    if g.isDefinedInThisGroup(templateName):
                        g.error("group " + g.name + " line " + str(line) + ": redefinition of template region: @" +
                                scope.text + "." + region.text)
                        st = stringtemplate3.StringTemplate()  # create bogus template to fill in

                    else:
                        err = False
                        # @template.region() ::= "..."
                        scopeST = g.lookupTemplate(scope.text)
                        if scopeST is None:
                            g.error("group " + g.name + " line " + str(
                                line) + ": reference to region within undefined template: " +
                                    scope.text)
                            err = True

                        if not scopeST.containsRegionName(region.text):
                            g.error("group " + g.name + " line " + str(
                                line) + ": template " + scope.text + " has no region called " +
                                    region.text)
                            err = True

                        if err:
                            st = stringtemplate3.StringTemplate()

                        else:
                            st = g.defineRegionTemplate(
                                scope.text,
                                region.text,
                                None,
                                stringtemplate3.REGION_EXPLICIT
                            )
                elif la1 and la1 in [ID]:
                    pass
                    name = self.LT(1)
                    self.match(ID)
                    templateName = name.text
                    if g.isDefinedInThisGroup(templateName):
                        g.error("redefinition of template: " + templateName)
                        # create bogus template to fill in
                        st = stringtemplate3.StringTemplate()
                    else:
                        st = g.defineTemplate(templateName, None)
                else:
                    raise antlr.NoViableAltException(self.LT(1), self.filename)

                if st is not None:
                    st.groupFileLine = line
                self.match(LPAREN)
                la1 = self.LA(1)
                if False:
                    pass
                elif la1 and la1 in [ID]:
                    pass
                    self.args(st)
                elif la1 and la1 in [RPAREN]:
                    pass
                    st.defineEmptyFormalArgumentList()
                else:
                    raise antlr.NoViableAltException(self.LT(1), self.filename)

                self.match(RPAREN)
                self.match(DEFINED_TO_BE)
                la1 = self.LA(1)
                if False:
                    pass
                elif la1 and la1 in [STRING]:
                    pass
                    t = self.LT(1)
                    self.match(STRING)
                    st.template = t.text
                elif la1 and la1 in [BIGSTRING]:
                    pass
                    bt = self.LT(1)
                    self.match(BIGSTRING)
                    st.template = bt.text
                else:
                    raise antlr.NoViableAltException(self.LT(1), self.filename)

            elif (self.LA(1) == ID) and (self.LA(2) == DEFINED_TO_BE):
                pass
                alias = self.LT(1)
                self.match(ID)
                self.match(DEFINED_TO_BE)
                target = self.LT(1)
                self.match(ID)
                g.defineTemplateAlias(alias.text, target.text)
            else:
                raise antlr.NoViableAltException(self.LT(1), self.filename)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_1)

    def mapdef(self, g):

        name = None
        m = None
        try:  # # for error handling
            pass
            name = self.LT(1)
            self.match(ID)
            self.match(DEFINED_TO_BE)
            m = self.map()
            if g.getMap(name.text):
                g.error("redefinition of map: " + name.text)
            elif g.isDefinedInThisGroup(name.text):
                g.error("redefinition of template as map: " + name.text)
            else:
                g.defineMap(name.text, m)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_1)

    def args(self, st):

        try:  # # for error handling
            pass
            self.arg(st)
            while True:
                if self.LA(1) == COMMA:
                    pass
                    self.match(COMMA)
                    self.arg(st)
                else:
                    break

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_2)

    def arg(self, st):

        name = None
        s = None
        bs = None
        defaultValue = None
        try:  # # for error handling
            pass
            name = self.LT(1)
            self.match(ID)
            if (self.LA(1) == ASSIGN) and (self.LA(2) == STRING):
                pass
                self.match(ASSIGN)
                s = self.LT(1)
                self.match(STRING)
                defaultValue = stringtemplate3.StringTemplate(
                    template="$_val_$"
                )
                defaultValue["_val_"] = s.text
                defaultValue.defineFormalArgument("_val_")
                defaultValue._name = ("<" + st.name + "'s arg " +
                                      name.text +
                                      " default value subtemplate>")
            elif (self.LA(1) == ASSIGN) and (self.LA(2) == ANONYMOUS_TEMPLATE):
                pass
                self.match(ASSIGN)
                bs = self.LT(1)
                self.match(ANONYMOUS_TEMPLATE)
                defaultValue = stringtemplate3.StringTemplate(
                    group=st.group,
                    template=bs.text
                )
                defaultValue._name = ("<" + st.name + "'s arg " +
                                      name.text +
                                      " default value subtemplate>")
            elif self.LA(1) == COMMA or self.LA(1) == RPAREN:
                pass
            else:
                raise antlr.NoViableAltException(self.LT(1), self.filename)

            st.defineFormalArgument(name.text, defaultValue)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_3)

    def map(self):
        mapping = {}

        try:  # # for error handling
            pass
            self.match(LBRACK)
            self.mapPairs(mapping)
            self.match(RBRACK)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_1)

        return mapping

    def mapPairs(self, mapping):

        try:  # # for error handling
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [STRING]:
                pass
                self.keyValuePair(mapping)
                while True:
                    if (self.LA(1) == COMMA) and (self.LA(2) == STRING):
                        pass
                        self.match(COMMA)
                        self.keyValuePair(mapping)
                    else:
                        break

                la1 = self.LA(1)
                if False:
                    pass
                elif la1 and la1 in [COMMA]:
                    pass
                    self.match(COMMA)
                    self.defaultValuePair(mapping)
                elif la1 and la1 in [RBRACK]:
                    pass
                else:
                    raise antlr.NoViableAltException(self.LT(1), self.filename)

            elif la1 and la1 in [LITERAL_default]:
                pass
                self.defaultValuePair(mapping)
            else:
                raise antlr.NoViableAltException(self.LT(1), self.filename)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_4)

    def keyValuePair(self, mapping):

        key = None
        try:  # # for error handling
            pass
            key = self.LT(1)
            self.match(STRING)
            self.match(COLON)
            v = self.keyValue()
            mapping[key.text] = v

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_5)

    def defaultValuePair(self, mapping):

        try:  # # for error handling
            pass
            self.match(LITERAL_default)
            self.match(COLON)
            v = self.keyValue()
            mapping[stringtemplate3.language.ASTExpr.DEFAULT_MAP_VALUE_NAME] = v

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_4)

    def keyValue(self):
        value = None

        s1 = None
        s2 = None
        k = None
        try:  # # for error handling
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [STRING]:
                pass
                s1 = self.LT(1)
                self.match(STRING)
                value = stringtemplate3.StringTemplate(
                    group=self._group, template=s1.text
                )
            elif la1 and la1 in [BIGSTRING]:
                pass
                s2 = self.LT(1)
                self.match(BIGSTRING)
                value = stringtemplate3.StringTemplate(
                    group=self._group,
                    template=s2.text
                )
            elif la1 and la1 in [ID]:
                pass
                k = self.LT(1)
                self.match(ID)
                if not k.text == "key":
                    raise antlr.SemanticException(" k.text == \"key\" ")
                value = stringtemplate3.language.ASTExpr.MAP_KEY_VALUE
            elif la1 and la1 in [COMMA, RBRACK]:
                pass
            else:
                raise antlr.NoViableAltException(self.LT(1), self.filename)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_5)

        return value


_tokenNames = [
    "<0>",
    "EOF",
    "<2>",
    "NULL_TREE_LOOKAHEAD",
    "\"group\"",
    "ID",
    "COLON",
    "\"implements\"",
    "COMMA",
    "SEMI",
    "AT",
    "DOT",
    "LPAREN",
    "RPAREN",
    "DEFINED_TO_BE",
    "STRING",
    "BIGSTRING",
    "ASSIGN",
    "ANONYMOUS_TEMPLATE",
    "LBRACK",
    "RBRACK",
    "\"default\"",
    "STAR",
    "PLUS",
    "OPTIONAL",
    "SL_COMMENT",
    "ML_COMMENT",
    "NL",
    "WS"
]


def mk_tokenSet_0():
    """ generate bit set """
    data = [2, 0]
    return data


_tokenSet_0 = antlr.BitSet(mk_tokenSet_0())


def mk_tokenSet_1():
    """ generate bit set """
    data = [1058, 0]
    return data


_tokenSet_1 = antlr.BitSet(mk_tokenSet_1())


def mk_tokenSet_2():
    """ generate bit set """
    data = [8192, 0]
    return data


_tokenSet_2 = antlr.BitSet(mk_tokenSet_2())


def mk_tokenSet_3():
    """ generate bit set """
    data = [8448, 0]
    return data


_tokenSet_3 = antlr.BitSet(mk_tokenSet_3())


def mk_tokenSet_4():
    """ generate bit set """
    data = [1048576, 0]
    return data


_tokenSet_4 = antlr.BitSet(mk_tokenSet_4())


def mk_tokenSet_5():
    """ generate bit set """
    data = [1048832, 0]
    return data


_tokenSet_5 = antlr.BitSet(mk_tokenSet_5())
