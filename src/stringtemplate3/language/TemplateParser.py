# ## $ANTLR 2.7.7 (2006-11-01): "template.g" -> "TemplateParser.py"$
# ## import antlr and other modules ..
from builtins import str

from stringtemplate3 import antlr

# ## header action >>> 
import stringtemplate3
from stringtemplate3.language.StringRef import StringRef
from stringtemplate3.language.NewlineRef import NewlineRef
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
LITERAL = 4
NEWLINE = 5
ACTION = 6
IF = 7
ELSEIF = 8
ELSE = 9
ENDIF = 10
REGION_REF = 11
REGION_DEF = 12
NL = 13
EXPR = 14
TEMPLATE = 15
IF_EXPR = 16
ESC_CHAR = 17
ESC = 18
HEX = 19
SUBTEMPLATE = 20
NESTED_PARENS = 21
INDENT = 22
COMMENT = 23


# ##/** A parser used to break up a single template into chunks, text literals
# ## *  and attribute expressions.
# ## */
class Parser(antlr.LLkParser):
    # ## user action >>>
    def reportError(self, e):
        group = self._this.group
        if group == stringtemplate3.DEFAULT_GROUP_NAME:
            self._this.error("template parse error; template context is " + self._this.enclosingInstanceStackString, e)

        else:
            self._this.error("template parse error in group " + self._this.group.name + " line " + str(
                self._this.groupFileLine) + "; template context is " + self._this.enclosingInstanceStackString, e)

    # ## user action <<<

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tokenNames = _tokenNames
        # ## __init__ header action >>>
        self._this = None
        # ## __init__ header action <<<

    def template(self, this):

        s = None
        nl = None
        try:  # # for error handling
            pass
            while True:
                la1 = self.LA(1)
                if False:
                    pass
                elif la1 and la1 in [LITERAL]:
                    pass
                    s = self.LT(1)
                    self.match(LITERAL)
                    this.addChunk(StringRef(this, s.text))
                elif la1 and la1 in [NEWLINE]:
                    pass
                    nl = self.LT(1)
                    self.match(NEWLINE)
                    if self.LA(1) != ELSE and self.LA(1) != ENDIF:
                        this.addChunk(NewlineRef(this, nl.text))
                elif la1 and la1 in [ACTION, IF, REGION_REF, REGION_DEF]:
                    pass
                    self.action(this)
                else:
                    break

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_0)

    def action(self, this):

        a = None
        i = None
        ei = None
        rr = None
        rd = None
        try:  # # for error handling
            la1 = self.LA(1)
            if False:
                pass
            elif la1 and la1 in [ACTION]:
                pass
                a = self.LT(1)
                self.match(ACTION)
                indent = a.indentation
                c = this.parseAction(a.text)
                c.indentation = indent
                this.addChunk(c)
            elif la1 and la1 in [IF]:
                pass
                i = self.LT(1)
                self.match(IF)
                c = this.parseAction(i.text)
                # create and precompile the subtemplate
                subtemplate = stringtemplate3.StringTemplate(group=this.group)
                subtemplate.enclosingInstance = this
                subtemplate._name = i.text + "_subtemplate"
                this.addChunk(c)
                self.template(subtemplate)
                if c:
                    c.subtemplate = subtemplate
                while True:
                    if self.LA(1) == ELSEIF:
                        pass
                        ei = self.LT(1)
                        self.match(ELSEIF)
                        ec = this.parseAction(ei.text)
                        # create and precompile the subtemplate
                        elseIfSubtemplate = stringtemplate3.StringTemplate(group=this.group)
                        elseIfSubtemplate.enclosingInstance = this
                        elseIfSubtemplate.name = ei.text + "_subtemplate"
                        self.template(elseIfSubtemplate)
                        if c is not None:
                            c.addElseIfSubtemplate(ec, elseIfSubtemplate)
                    else:
                        break

                la1 = self.LA(1)
                if False:
                    pass
                elif la1 and la1 in [ELSE]:
                    pass
                    self.match(ELSE)
                    # create and precompile the subtemplate
                    elseSubtemplate = stringtemplate3.StringTemplate(group=this.group)
                    elseSubtemplate.enclosingInstance = this
                    elseSubtemplate._name = "else_subtemplate"
                    self.template(elseSubtemplate)
                    if c:
                        c.elseSubtemplate = elseSubtemplate
                elif la1 and la1 in [ENDIF]:
                    pass
                else:
                    raise antlr.NoViableAltException(self.LT(1), self.filename)

                self.match(ENDIF)
            elif la1 and la1 in [REGION_REF]:
                pass
                rr = self.LT(1)
                self.match(REGION_REF)
                # define implicit template and
                # convert <@r()> to <region__enclosingTemplate__r()>
                regionName = rr.text
                mangledRef = None
                err = False
                # watch out for <@super.r()>; that does NOT def implicit region
                # convert to <super.region__enclosingTemplate__r()>
                if regionName.startswith("super."):
                    # System.out.println("super region ref "+regionName);
                    regionRef = regionName[len("super."):len(regionName)]
                    templateScope = this.group.getUnMangledTemplateName(this.name)
                    scopeST = this.group.lookupTemplate(templateScope)
                    if scopeST is None:
                        this.group.error("reference to region within undefined template: " + templateScope)
                        err = True

                    if not scopeST.containsRegionName(regionRef):
                        this.group.error("template " + templateScope + " has no region called " + regionRef)
                        err = True

                    else:
                        mangledRef = this.group.getMangledRegionName(templateScope, regionRef)
                        mangledRef = "super." + mangledRef

                else:
                    regionST = this.group.defineImplicitRegionTemplate(this, regionName)
                    mangledRef = regionST.name

                if not err:
                    # treat as regular action: mangled template include
                    indent = rr.indentation
                    c = this.parseAction(mangledRef + "()")
                    c.indentation = indent
                    this.addChunk(c)
            elif la1 and la1 in [REGION_DEF]:
                pass
                rd = self.LT(1)
                self.match(REGION_DEF)
                combinedNameTemplateStr = rd.text
                indexOfDefSymbol = combinedNameTemplateStr.find("::=")
                if indexOfDefSymbol >= 1:
                    regionName = combinedNameTemplateStr[0:indexOfDefSymbol]
                    template = combinedNameTemplateStr[indexOfDefSymbol + 3:len(combinedNameTemplateStr)]
                    regionST = this.group.defineRegionTemplate(
                        this,
                        regionName,
                        template,
                        stringtemplate3.REGION_EMBEDDED
                    )
                    # treat as regular action: mangled template include
                    indent = rd.indentation
                    c = this.parseAction(regionST.name + "()")
                    c.indentation = indent
                    this.addChunk(c)

                else:
                    this.error("embedded region definition screwed up")
            else:
                raise antlr.NoViableAltException(self.LT(1), self.filename)

        except antlr.RecognitionException as ex:
            self.reportError(ex)
            self.consume()
            self.consumeUntil(_tokenSet_1)


_tokenNames = [
    "<0>",
    "EOF",
    "<2>",
    "NULL_TREE_LOOKAHEAD",
    "LITERAL",
    "NEWLINE",
    "ACTION",
    "IF",
    "ELSEIF",
    "ELSE",
    "ENDIF",
    "REGION_REF",
    "REGION_DEF",
    "NL",
    "EXPR",
    "TEMPLATE",
    "IF_EXPR",
    "ESC_CHAR",
    "ESC",
    "HEX",
    "SUBTEMPLATE",
    "NESTED_PARENS",
    "INDENT",
    "COMMENT"
]


def mk_tokenSet_0():
    """ generate bit set """
    data = [1792, 0]
    return data


_tokenSet_0 = antlr.BitSet(mk_tokenSet_0())


def mk_tokenSet_1():
    """ generate bit set """
    data = [8176, 0]
    return data


_tokenSet_1 = antlr.BitSet(mk_tokenSet_1())
