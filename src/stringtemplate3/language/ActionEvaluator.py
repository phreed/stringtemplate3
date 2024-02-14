# ## $ANTLR 2.7.7 (2006-11-01): "eval.g" -> "ActionEvaluator.py"$
# ## import antlr and other modules ..

from builtins import str
from builtins import object
from stringtemplate3 import antlr

# ## header action >>> 
from stringtemplate3.language.CatIterator import CatList

from io import StringIO


class NameValuePair(object):

    def __init__(self):
        self._name = None
        self._value = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


# ## header action <<<

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


# ## user code>>>

# ## user code<<<

class Walker(antlr.TreeParser):

    # ctor ..
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tokenNames = _tokenNames
        # ## __init__ header action >>>
        self._this = None
        self._out = None
        self._chunk = None
        # ## __init__ header action <<<

    # ## user action >>>
    def initialize(self, this, chunk, out):
        self._this = this
        self._chunk = chunk
        self._out = out

    def reportError(self, e):
        self._this.error("eval tree parse error", e)

    # ## user action <<<
    def action(self, _t):
        numCharsWritten = 0

        action_AST_in = None
        if _t != antlr.ASTNULL:
            action_AST_in = _t
        e = None
        try:  # # for error handling
            pass
            e = self.expr(_t)
            _t = self._retTree
            numCharsWritten = self._chunk.writeAttribute(self._this, e, self._out)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t
        return numCharsWritten

    def expr(self, _t):
        value = None

        expr_AST_in = None
        if _t != antlr.ASTNULL:
            expr_AST_in = _t
        a = None
        b = None
        e = None
        try:  # # for error handling
            if not _t:
                _t = antlr.ASTNULL
            la1 = _t.getType()
            if False:
                pass
            elif la1 and la1 in [PLUS]:
                pass
                _t3 = _t
                tmp1_AST_in = _t
                self.match(_t, PLUS)
                _t = _t.firstChild
                a = self.expr(_t)
                _t = self._retTree
                b = self.expr(_t)
                _t = self._retTree
                value = self._chunk.add(a, b)
                _t = _t3
                _t = _t.getNextSibling()
            elif la1 and la1 in [APPLY, MULTI_APPLY]:
                pass
                value = self.templateApplication(_t)
                _t = self._retTree
            elif la1 and la1 in [ID, DOT, ANONYMOUS_TEMPLATE, STRING, INT]:
                pass
                value = self.attribute(_t)
                _t = self._retTree
            elif la1 and la1 in [INCLUDE]:
                pass
                value = self.templateInclude(_t)
                _t = self._retTree
            elif la1 and la1 in [FUNCTION]:
                pass
                value = self.function(_t)
                _t = self._retTree
            elif la1 and la1 in [LIST]:
                pass
                value = self.list(_t)
                _t = self._retTree
            elif la1 and la1 in [VALUE]:
                pass
                _t4 = _t
                tmp2_AST_in = _t
                self.match(_t, VALUE)
                _t = _t.firstChild
                e = self.expr(_t)
                _t = self._retTree
                _t = _t4
                _t = _t.getNextSibling()
                buf = StringIO(u'')
                sw = self._this.group.getStringTemplateWriter(buf)
                n = self._chunk.writeAttribute(self._this, e, sw)
                if n > 0:
                    value = buf.getvalue()
            else:
                raise antlr.NoViableAltException(_t)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t
        return value

    def templateApplication(self, _t):
        """ Apply template(s) to an attribute; can be applied to another apply result."""
        value = None

        templateApplication_AST_in = None
        if _t != antlr.ASTNULL:
            templateApplication_AST_in = _t
        anon = None
        a = None
        templatesToApply = []
        attributes = []
        try:  # # for error handling
            if not _t:
                _t = antlr.ASTNULL
            la1 = _t.getType()
            if False:
                pass
            elif la1 and la1 in [APPLY]:
                pass
                _t14 = _t
                tmp3_AST_in = _t
                self.match(_t, APPLY)
                _t = _t.firstChild
                a = self.expr(_t)
                _t = self._retTree
                _cnt16 = 0
                while True:
                    if not _t:
                        _t = antlr.ASTNULL
                    if _t.type == TEMPLATE:
                        pass
                        self.template(_t, templatesToApply)
                        _t = self._retTree
                    else:
                        break

                    _cnt16 += 1
                if _cnt16 < 1:
                    raise antlr.NoViableAltException(_t)
                value = self._chunk.applyListOfAlternatingTemplates(self._this, a, templatesToApply)
                _t = _t14
                _t = _t.getNextSibling()
            elif la1 and la1 in [MULTI_APPLY]:
                pass
                _t17 = _t
                tmp4_AST_in = _t
                self.match(_t, MULTI_APPLY)
                _t = _t.firstChild
                _cnt19 = 0
                while True:
                    if not _t:
                        _t = antlr.ASTNULL
                    if _tokenSet_0.member(_t.type):
                        pass
                        a = self.expr(_t)
                        _t = self._retTree
                        attributes.append(a)
                    else:
                        break

                    _cnt19 += 1
                if _cnt19 < 1:
                    raise antlr.NoViableAltException(_t)
                tmp5_AST_in = _t
                self.match(_t, COLON)
                _t = _t.getNextSibling()
                anon = _t
                self.match(_t, ANONYMOUS_TEMPLATE)
                _t = _t.getNextSibling()
                anonymous = anon.getStringTemplate()
                templatesToApply.append(anonymous)
                value = self._chunk.applyTemplateToListOfAttributes(
                    self._this,
                    attributes, anon.getStringTemplate())
                _t = _t17
                _t = _t.getNextSibling()
            else:
                raise antlr.NoViableAltException(_t)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t
        return value

    def attribute(self, _t):
        value = None

        attribute_AST_in = None
        if _t != antlr.ASTNULL:
            attribute_AST_in = _t
        prop = None
        i3 = None
        i = None
        s = None
        at = None
        obj = None
        propName = None
        e = None
        try:  # # for error handling
            if not _t:
                _t = antlr.ASTNULL
            la1 = _t.getType()
            if False:
                pass
            elif la1 and la1 in [DOT]:
                pass
                _t33 = _t
                tmp6_AST_in = _t
                self.match(_t, DOT)
                _t = _t.firstChild
                obj = self.expr(_t)
                _t = self._retTree
                if not _t:
                    _t = antlr.ASTNULL
                la1 = _t.getType()
                if False:
                    pass
                elif la1 and la1 in [ID]:
                    pass
                    prop = _t
                    self.match(_t, ID)
                    _t = _t.getNextSibling()
                    propName = prop.text
                elif la1 and la1 in [VALUE]:
                    pass
                    _t35 = _t
                    tmp7_AST_in = _t
                    self.match(_t, VALUE)
                    _t = _t.firstChild
                    e = self.expr(_t)
                    _t = self._retTree
                    _t = _t35
                    _t = _t.getNextSibling()
                    if e is not None:
                        propName = str(e)
                else:
                    raise antlr.NoViableAltException(_t)

                _t = _t33
                _t = _t.getNextSibling()
                value = self._chunk.getObjectProperty(self._this, obj, propName)
            elif la1 and la1 in [ID]:
                pass
                i3 = _t
                self.match(_t, ID)
                _t = _t.getNextSibling()
                value = self._this.getAttribute(i3.text)
            elif la1 and la1 in [INT]:
                pass
                i = _t
                self.match(_t, INT)
                _t = _t.getNextSibling()
                value = int(i.text)
            elif la1 and la1 in [STRING]:
                pass
                s = _t
                self.match(_t, STRING)
                _t = _t.getNextSibling()
                value = s.text
            elif la1 and la1 in [ANONYMOUS_TEMPLATE]:
                pass
                at = _t
                self.match(_t, ANONYMOUS_TEMPLATE)
                _t = _t.getNextSibling()
                value = at.text
                if at.text:
                    from stringtemplate3.templates import StringTemplate
                    valueST = StringTemplate(
                        group=self._this.group,
                        template=at.text
                    )
                    valueST.enclosingInstance = self._this
                    valueST._name = "<anonymous template argument>"
                    value = valueST
            else:
                raise antlr.NoViableAltException(_t)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t
        return value

    def templateInclude(self, _t):
        value = None

        templateInclude_AST_in = None
        if _t != antlr.ASTNULL:
            templateInclude_AST_in = _t
        ident = None
        a1 = None
        a2 = None
        args = None
        name = ""
        n = None
        try:  # # for error handling
            pass
            _t10 = _t
            tmp8_AST_in = _t
            self.match(_t, INCLUDE)
            _t = _t.firstChild
            if not _t:
                _t = antlr.ASTNULL
            la1 = _t.getType()
            if False:
                pass
            elif la1 and la1 in [ID]:
                pass
                ident = _t
                self.match(_t, ID)
                _t = _t.getNextSibling()
                a1 = _t
                if not _t:
                    raise antlr.MismatchedTokenException()
                _t = _t.getNextSibling()
                name = ident.text
                args = a1
            elif la1 and la1 in [VALUE]:
                pass
                _t12 = _t
                tmp9_AST_in = _t
                self.match(_t, VALUE)
                _t = _t.firstChild
                n = self.expr(_t)
                _t = self._retTree
                a2 = _t
                if not _t:
                    raise antlr.MismatchedTokenException()
                _t = _t.getNextSibling()
                _t = _t12
                _t = _t.getNextSibling()
                if n:
                    name = str(n)
                    args = a2
            else:
                raise antlr.NoViableAltException(_t)

            _t = _t10
            _t = _t.getNextSibling()
            if name:
                value = self._chunk.getTemplateInclude(self._this, name, args)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t
        return value

    def function(self, _t):
        value = None

        function_AST_in = None
        if _t != antlr.ASTNULL:
            function_AST_in = _t
        a = None
        try:  # # for error handling
            pass
            _t21 = _t
            tmp10_AST_in = _t
            self.match(_t, FUNCTION)
            _t = _t.firstChild
            if not _t:
                _t = antlr.ASTNULL
            la1 = _t.getType()
            if False:
                pass
            elif la1 and la1 in [LITERAL_first]:
                pass
                tmp11_AST_in = _t
                self.match(_t, LITERAL_first)
                _t = _t.getNextSibling()
                a = self.singleFunctionArg(_t)
                _t = self._retTree
                value = self._chunk.first(a)
            elif la1 and la1 in [LITERAL_rest]:
                pass
                tmp12_AST_in = _t
                self.match(_t, LITERAL_rest)
                _t = _t.getNextSibling()
                a = self.singleFunctionArg(_t)
                _t = self._retTree
                value = self._chunk.rest(a)
            elif la1 and la1 in [LITERAL_last]:
                pass
                tmp13_AST_in = _t
                self.match(_t, LITERAL_last)
                _t = _t.getNextSibling()
                a = self.singleFunctionArg(_t)
                _t = self._retTree
                value = self._chunk.last(a)
            elif la1 and la1 in [LITERAL_length]:
                pass
                tmp14_AST_in = _t
                self.match(_t, LITERAL_length)
                _t = _t.getNextSibling()
                a = self.singleFunctionArg(_t)
                _t = self._retTree
                value = self._chunk.length(a)
            elif la1 and la1 in [LITERAL_strip]:
                pass
                tmp15_AST_in = _t
                self.match(_t, LITERAL_strip)
                _t = _t.getNextSibling()
                a = self.singleFunctionArg(_t)
                _t = self._retTree
                value = self._chunk.strip(a)
            elif la1 and la1 in [LITERAL_trunc]:
                pass
                tmp16_AST_in = _t
                self.match(_t, LITERAL_trunc)
                _t = _t.getNextSibling()
                a = self.singleFunctionArg(_t)
                _t = self._retTree
                value = self._chunk.trunc(a)
            else:
                raise antlr.NoViableAltException(_t)

            _t = _t21
            _t = _t.getNextSibling()

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t
        return value

    def list(self, _t):
        """ create a new list of expressions as a new multi-value attribute """
        value = None

        list_AST_in = None
        if _t != antlr.ASTNULL:
            list_AST_in = _t
        e = None
        elements = []
        # TODO: verify against v3.2
        value = CatList(elements)
        try:  # # for error handling
            if not _t:
                _t = antlr.ASTNULL
            la1 = _t.getType()
            if False:
                pass
            elif la1 and la1 in [LIST]:
                pass
                _t6 = _t
                tmp17_AST_in = _t
                self.match(_t, LIST)
                _t = _t.firstChild
                _cnt8 = 0
                while True:
                    if not _t:
                        _t = antlr.ASTNULL
                    if _tokenSet_0.member(_t.type):
                        pass
                        e = self.expr(_t)
                        _t = self._retTree
                        if e:
                            from stringtemplate3.language.ASTExpr import convertAnythingToList
                            e = convertAnythingToList(e)
                            elements.append(e)
                    else:
                        break

                    _cnt8 += 1
                if _cnt8 < 1:
                    raise antlr.NoViableAltException(_t)
                _t = _t6
                _t = _t.getNextSibling()
            elif la1 and la1 in [NOTHING]:
                pass
                tmp18_AST_in = _t
                self.match(_t, NOTHING)
                _t = _t.getNextSibling()
                nullSingleton = [None]
                elements.append(nullSingleton)
            else:
                raise antlr.NoViableAltException(_t)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t
        return value

    def template(self, _t, templatesToApply):

        template_AST_in = None
        if _t != antlr.ASTNULL:
            template_AST_in = _t
        t = None
        args = None
        anon = None
        args2 = None
        argumentContext = {}
        n = None
        try:  # # for error handling
            pass
            _t26 = _t
            tmp19_AST_in = _t
            self.match(_t, TEMPLATE)
            _t = _t.firstChild
            if not _t:
                _t = antlr.ASTNULL
            la1 = _t.getType()
            if False:
                pass
            elif la1 and la1 in [ID]:
                pass
                t = _t
                self.match(_t, ID)
                _t = _t.getNextSibling()
                args = _t
                if not _t:
                    raise antlr.MismatchedTokenException()
                _t = _t.getNextSibling()
                templateName = t.text
                group = self._this.group
                embedded = group.getEmbeddedInstanceOf(
                    templateName,
                    self._this
                )
                if embedded:
                    embedded._argumentsAST = args
                    templatesToApply.append(embedded)
            elif la1 and la1 in [ANONYMOUS_TEMPLATE]:
                pass
                anon = _t
                self.match(_t, ANONYMOUS_TEMPLATE)
                _t = _t.getNextSibling()
                anonymous = anon.getStringTemplate()
                # to properly see overridden templates, always set
                # anonymous' group to be self's group
                anonymous._group = self._this.group
                templatesToApply.append(anonymous)
            elif la1 and la1 in [VALUE]:
                pass
                _t28 = _t
                tmp20_AST_in = _t
                self.match(_t, VALUE)
                _t = _t.firstChild
                n = self.expr(_t)
                _t = self._retTree
                args2 = _t
                if not _t:
                    raise antlr.MismatchedTokenException()
                _t = _t.getNextSibling()
                embedded = None
                if n:
                    templateName = str(n)
                    group = self._this.group
                    embedded = group.getEmbeddedInstanceOf(
                        templateName,
                        self._this
                    )
                    if embedded:
                        embedded._argumentsAST = args2
                        templatesToApply.append(embedded)
                _t = _t28
                _t = _t.getNextSibling()
            else:
                raise antlr.NoViableAltException(_t)

            _t = _t26
            _t = _t.getNextSibling()

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t

    def singleFunctionArg(self, _t):
        value = None

        singleFunctionArg_AST_in = None
        if _t != antlr.ASTNULL:
            singleFunctionArg_AST_in = _t
        try:  # # for error handling
            pass
            _t24 = _t
            tmp21_AST_in = _t
            self.match(_t, SINGLEVALUEARG)
            _t = _t.firstChild
            value = self.expr(_t)
            _t = self._retTree
            _t = _t24
            _t = _t.getNextSibling()

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t
        return value

    def ifCondition(self, _t):
        value = False

        ifCondition_AST_in = None
        if _t != antlr.ASTNULL:
            ifCondition_AST_in = _t
        a = None
        try:  # # for error handling
            if not _t:
                _t = antlr.ASTNULL
            la1 = _t.getType()
            if False:
                pass
            elif la1 and la1 in [APPLY, MULTI_APPLY, INCLUDE, VALUE,
                                 FUNCTION, LIST, NOTHING, ID, PLUS, DOT,
                                 ANONYMOUS_TEMPLATE, STRING, INT]:
                pass
                a = self.ifAtom(_t)
                _t = self._retTree
                value = self._chunk.testAttributeTrue(a)
            elif la1 and la1 in [NOT]:
                pass
                _t30 = _t
                tmp22_AST_in = _t
                self.match(_t, NOT)
                _t = _t.firstChild
                a = self.ifAtom(_t)
                _t = self._retTree
                _t = _t30
                _t = _t.getNextSibling()
                value = not self._chunk.testAttributeTrue(a)
            else:
                raise antlr.NoViableAltException(_t)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t
        return value

    def ifAtom(self, _t):
        value = None

        ifAtom_AST_in = None
        if _t != antlr.ASTNULL:
            ifAtom_AST_in = _t
        try:  # # for error handling
            pass
            value = self.expr(_t)
            _t = self._retTree

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t
        return value

    def argList(self, _t, embedded, initialContext):
        """ self is assumed to be the enclosing context as foo(x=y) must find y in
        the template that encloses the ref to foo(x=y).
        We must pass in the embedded template (the one invoked)
        so we can check formal args in rawSetArgumentAttribute."""
        argumentContext = None

        argList_AST_in = None
        if _t != antlr.ASTNULL:
            argList_AST_in = _t
        argumentContext = initialContext
        if not argumentContext:
            argumentContext = {}
        try:  # # for error handling
            if not _t:
                _t = antlr.ASTNULL
            la1 = _t.getType()
            if False:
                pass
            elif la1 and la1 in [ARGS]:
                pass
                _t37 = _t
                tmp23_AST_in = _t
                self.match(_t, ARGS)
                _t = _t.firstChild
                while True:
                    if not _t:
                        _t = antlr.ASTNULL
                    if _t.type == ASSIGN or _t.type == DOTDOTDOT:
                        pass
                        self.argumentAssignment(_t, embedded, argumentContext)
                        _t = self._retTree
                    else:
                        break

                _t = _t37
                _t = _t.getNextSibling()
            elif la1 and la1 in [SINGLEVALUEARG]:
                pass
                self.singleTemplateArg(_t, embedded, argumentContext)
                _t = self._retTree
            else:
                raise antlr.NoViableAltException(_t)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t
        return argumentContext

    def argumentAssignment(self, _t, embedded, argumentContext):

        argumentAssignment_AST_in = None
        if _t != antlr.ASTNULL:
            argumentAssignment_AST_in = _t
        arg = None
        e = None
        try:  # # for error handling
            if not _t:
                _t = antlr.ASTNULL
            la1 = _t.getType()
            if False:
                pass
            elif la1 and la1 in [ASSIGN]:
                pass
                _t43 = _t
                tmp24_AST_in = _t
                self.match(_t, ASSIGN)
                _t = _t.firstChild
                arg = _t
                self.match(_t, ID)
                _t = _t.getNextSibling()
                e = self.expr(_t)
                _t = self._retTree
                _t = _t43
                _t = _t.getNextSibling()
                if e:
                    self._this.rawSetArgumentAttribute(
                        embedded, argumentContext,
                        arg.text, e)
            elif la1 and la1 in [DOTDOTDOT]:
                pass
                tmp25_AST_in = _t
                self.match(_t, DOTDOTDOT)
                _t = _t.getNextSibling()
                embedded._passThroughAttributes = True
            else:
                raise antlr.NoViableAltException(_t)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.getNextSibling()

        self._retTree = _t

    def singleTemplateArg(self, _t, embedded, argumentContext):
        soleArgName = None
        singleTemplateArg_AST_in = None
        if _t != antlr.ASTNULL:
            singleTemplateArg_AST_in = _t
        e = None
        try:  # # for error handling
            pass
            _t41 = _t
            tmp26_AST_in = _t
            self.match(_t, SINGLEVALUEARG)
            _t = _t.firstChild
            e = self.expr(_t)
            _t = self._retTree
            _t = _t41
            _t = _t.getNextSibling()
            if e:
                soleArgName = None
                # find the sole defined formal argument for embedded
                error = False
                formalArgs = embedded.formalArguments
                if formalArgs:
                    argNames = list(formalArgs.keys())
                    if len(argNames) == 1:
                        soleArgName = argNames[0]
                        # sys.stderr.write("sole formal arg of " +
                        #                 embedded.getName() + " is " +
                        #                 soleArgName)
                    else:
                        error = True
            else:
                error = True
            if error:
                self._this.error("template " + embedded.name +
                                 " must have exactly one formal arg in" +
                                 " template context " +
                                 self._this.enclosingInstanceStackString)
            else:
                self._this.rawSetArgumentAttribute(embedded, argumentContext, soleArgName, e)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            if _t:
                _t = _t.nextSibling

        self._retTree = _t


_tokenNames = [
    "<0>",
    "EOF",
    "<2>",
    "NULL_TREE_LOOKAHEAD",
    "APPLY",
    "MULTI_APPLY",
    "ARGS",
    "INCLUDE",
    "\"if\"",
    "VALUE",
    "TEMPLATE",
    "FUNCTION",
    "SINGLEVALUEARG",
    "LIST",
    "NOTHING",
    "SEMI",
    "LPAREN",
    "RPAREN",
    "\"elseif\"",
    "COMMA",
    "ID",
    "ASSIGN",
    "COLON",
    "NOT",
    "PLUS",
    "DOT",
    "\"first\"",
    "\"rest\"",
    "\"last\"",
    "\"length\"",
    "\"strip\"",
    "\"trunc\"",
    "\"super\"",
    "ANONYMOUS_TEMPLATE",
    "STRING",
    "INT",
    "LBRACK",
    "RBRACK",
    "DOTDOTDOT",
    "TEMPLATE_ARGS",
    "NESTED_ANONYMOUS_TEMPLATE",
    "ESC_CHAR",
    "WS",
    "WS_CHAR"
]


def mk_tokenSet_0():
    """ generate bit set """
    data = [60180933296, 0]
    return data


_tokenSet_0 = antlr.BitSet(mk_tokenSet_0())
