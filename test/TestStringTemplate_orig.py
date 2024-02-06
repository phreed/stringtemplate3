
import calendar
import io
import logging

import temppathlib

import stringtemplate3 as st3
from stringtemplate3 import errors as st3err
from stringtemplate3.grouploaders import PathGroupLoader
from stringtemplate3.groups import StringTemplateGroup as st3g
from stringtemplate3.interfaces import StringTemplateGroupInterface as st3gi
from stringtemplate3.language import (DefaultTemplateLexer,
                                      AngleBracketTemplateLexer)
from stringtemplate3.language.ASTExpr import IllegalStateException
from stringtemplate3.templates import StringTemplate as st3t
from stringtemplate3.writers import AttributeRenderer

import TestStringHelper as tsh
from TestStringHelper import (NoSuchElementException,
                              IllegalArgumentException,
                              sample_day)

"""
 [The "BSD licence"]
 Copyright (c) 2003-2005 Terence Parr
 All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions
 are met:
 1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.
 3. The name of the author may not be used to endorse or promote products
    derived from this software without specific prior written permission.

 THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
 IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
 INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
 NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
 THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

logger = logging.getLogger(__name__)

"""
https://docs.python.org/3/howto/logging.html
https://theantlrguy.atlassian.net/wiki/spaces/ST/pages/1409137/StringTemplate+3.0+Printable+Documentation
"""


def test_interfaceFileFormat():
    groupI = st3t("""
        interface test;
        t();
        bold(item);
        optional duh(a,b,c);
    """)
    ix = st3gi(groupI)

    expecting = """
            interface test;
            t();
            bold(item);
            optional duh(a, b, c);
            """
    assert str(ix) == expecting


def test_AaaNoGroupLoader():
    templates = """
            group testG implements blort;
            t() ::= <<foo>>
            bold(item) ::= <<foo>>
            duh(a,b,c) ::= <<foo>>;
            """
    errors = st3err.DEFAULT_ERROR_LISTENER
    tmp_dir = temppathlib.TemporaryDirectory()
    stg_file = tsh.write_file(tmp_dir.path, "testG.stg", templates)

    with open(stg_file, "rb") as reader:
        group = st3g(reader, errors)
        logger.debug(f"group: {group}")

    expecting = "no group loader registered"
    assert expecting == str(errors)


def test_CannotFindInterfaceFile():
    """ this also tests the group loader """
    errors = st3err.DEFAULT_ERROR_LISTENER
    tmp_dir = temppathlib.TemporaryDirectory()
    st3g.registerGroupLoader(PathGroupLoader(tmp_dir.path, errors))

    templates = """
        group testG implements blort;
        t() ::= <<foo>>
        bold(item) ::= <<foo>>
        duh(a,b,c) ::= <<foo>>;
        """

    stg_file = tsh.write_file(tmp_dir.path, "testG.stg", templates)

    with open(stg_file, "rb") as reader:
        group = st3g(reader, errors)
        logger.debug(f"group: {group}")

    expecting = "no such interface file blort.sti"
    assert expecting == str(errors)


def test_MultiDirGroupLoading():
    """ this also tests the group loader """
    errors = st3err.DEFAULT_ERROR_LISTENER
    tmp_dir = temppathlib.TemporaryDirectory()
    sub_dir = tmp_dir.path / "sub"
    try:
        sub_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as pe:
        logger.exception("can't make subdir in test", pe)
        return

    st3g.registerGroupLoader(PathGroupLoader(tmp_dir.path, sub_dir))

    templates = """
        group testG2;
        t() ::= <<foo>>
        bold(item) ::= <<foo>>
        duh(a,b,c) ::= <<foo>>;
"""
    tsh.write_file(tmp_dir.path / "sub", "testG2.stg", templates)

    group = st3g.loadGroup("testG2")
    expecting = """
    group testG2;
        bold(item) ::= <<foo>>
        duh(a,b,c) ::= <<foo>>
        t() ::= <<foo>>;
        """
    assert expecting == str(group)


def test_GroupSatisfiesSingleInterface():
    """ this also tests the group loader """
    errors = st3err.DEFAULT_ERROR_LISTENER
    tmp_dir = temppathlib.TemporaryDirectory()
    st3g.registerGroupLoader(PathGroupLoader(tmp_dir.path, errors))
    groupI = """
            interface testI;
            t();
            bold(item);
            optional duh(a,b,c);
            """
    tsh.write_file(tmp_dir.path, "testI.sti", groupI)

    templates = """
        group testG implements testI;
        t() ::= <<foo>>
        bold(item) ::= <<foo>>
        duh(a,b,c) ::= <<foo>>;
"""
    stg_file = tsh.write_file(tmp_dir.path, "testG.stg", templates)

    with open(stg_file, "rb") as reader:
        group = st3g(reader, errors=errors)
        logger.debug(f"group: {group}")

    expecting = ""  # should be no errors
    assert expecting == str(errors)


def test_GroupExtendsSuperGroup():
    """ this also tests the group loader """
    errors = st3err.DEFAULT_ERROR_LISTENER
    tmp_dir = temppathlib.TemporaryDirectory()
    st3g.registerGroupLoader(PathGroupLoader(tmp_dir.path, errors=errors))
    superGroup = """
            group superG;
            bold(item) ::= <<*$item$*>>;\n;
    """
    tsh.write_file(tmp_dir.path, "superG.stg", superGroup)

    templates = """
        group testG : superG;
        main(x) ::= <<$bold(x)$>>;
"""

    stg_file = tsh.write_file(tmp_dir.path, "testG.stg", templates)

    with open(stg_file, "rb") as reader:
        group = st3g(reader, DefaultTemplateLexer.Lexer, errors=errors)

    st = group.getInstanceOf("main")
    st["x"] = "foo"

    expecting = "*foo*"
    assert expecting == str(st)


def test_GroupExtendsSuperGroupWithAngleBrackets():
    """ this also tests the group loader """
    errors = st3err.DEFAULT_ERROR_LISTENER
    tmp_dir = temppathlib.TemporaryDirectory()
    st3g.registerGroupLoader(PathGroupLoader(tmp_dir.path, errors=errors))
    superGroup = """
            group superG;
            bold(item) ::= <<*<item>*>>;\n;
    """
    tsh.write_file(tmp_dir.path, "superG.stg", superGroup)

    templates = """
        group testG : superG;
        main(x) ::= \"<bold(x)>\";
    """
    stg_file = tsh.write_file(tmp_dir.path, "testG.stg", templates)

    with open(stg_file, "rb") as reader:
        group = st3g(reader, errors=errors)
    st = group.getInstanceOf("main")
    st["x"] = "foo"

    expecting = "*foo*"
    assert expecting == str(st)


def test_MissingInterfaceTemplate():
    """ this also tests the group loader """
    errors = st3err.DEFAULT_ERROR_LISTENER
    tmp_dir = temppathlib.TemporaryDirectory()
    st3g.registerGroupLoader(PathGroupLoader(tmp_dir.path, errors=errors))
    groupI = """
            interface testI;
            t();
            bold(item);
            optional duh(a,b,c);
    """
    tsh.write_file(tmp_dir.path, "testI.sti", groupI)

    templates = """
        group testG implements testI;
        t() ::= <<foo>>
        duh(a,b,c) ::= <<foo>>
"""
    stg_file = tsh.write_file(tmp_dir.path, "testG.stg", templates)

    with open(stg_file, "rb") as reader:
        group = st3g(reader, errors=errors)
        logger.debug(f"group: {group}")

    expecting = "group testG does not satisfy interface testI: missing templates [bold]"
    assert expecting == str(errors)


def test_MissingOptionalInterfaceTemplate():
    """ this also tests the group loader """
    errors = st3err.DEFAULT_ERROR_LISTENER
    tmp_dir = temppathlib.TemporaryDirectory()
    st3g.registerGroupLoader(PathGroupLoader(tmp_dir.path, errors=errors))
    groupI = """
            interface testI;
            t();
            bold(item);
            optional duh(a,b,c);
    """
    tsh.write_file(tmp_dir.path, "testI.sti", groupI)

    templates = """
        group testG implements testI;
        t() ::= <<foo>>
        "bold(item) ::= <<foo>>";
"""
    stg_file = tsh.write_file(tmp_dir.path, "testG.stg", templates)

    with open(stg_file, "rb") as reader:
        group = st3g(reader, errors=errors)
        logger.debug(f"group: {group}")

    expecting = ""  # should be NO errors
    assert expecting == str(errors)


def test_MismatchedInterfaceTemplate():
    """ this also tests the group loader """
    errors = st3err.DEFAULT_ERROR_LISTENER
    tmp_dir = temppathlib.TemporaryDirectory()
    st3g.registerGroupLoader(PathGroupLoader(tmp_dir.path, errors=errors))
    groupI = """
            interface testI;
            t();
            bold(item);
            optional duh(a,b,c);
    """
    tsh.write_file(tmp_dir.path, "testI.sti", groupI)

    templates = """
        group testG implements testI;
        t() ::= <<foo>>
        bold(item) ::= <<foo>>
        duh(a,c) ::= <<foo>>
"""
    stg_file = tsh.write_file(tmp_dir.path, "testG.stg", templates)

    with open(stg_file, "rb") as reader:
        group = st3g(reader, errors=errors)
        logger.debug(f"group: {group}")

    expecting = "group testG does not satisfy interface testI: " \
                "mismatched arguments on these templates [optional duh(a, b, c)]"
    assert expecting == str(errors)


def test_GroupFileFormat():
    templates = """
            group test;
            t() ::= \"literal template\"
            bold(item) ::= \"<b>$item$</b>\"
            duh() ::= <<+newline+"xx">>
    """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)

    expecting = """
    group test;
    bold(item) ::= <<<b>$item$</b>>>
    duh() ::= <<xx>>
    t() ::= <<literal template>>;
    """
    assert expecting == str(group)

    a = group.getInstanceOf("t")
    expecting = "literal template"
    assert expecting == str(a)

    b = group.getInstanceOf("bold")
    b["item"] = "dork"
    expecting = "<b>dork</b>"
    assert expecting == str(b)


def test_EscapedTemplateDelimiters():
    templates = """
            group test;
            t() ::= <<$\"literal\":{a|$a$\\}}$ template\n>>
            bold(item) ::= <<<b>$item$</b\\>>>
            duh() ::= <<
            "xx">>
    """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)

    expecting = """
    group test;
    bold(item) ::= <<<b>$item$</b>>>
    duh() ::= <<xx>>
    t() ::= <<$\"literal\":{a|$a$\\}}$ template>>
    """
    assert expecting == str(group)

    b = group.getInstanceOf("bold")
    b["item"] = "dork"
    expecting = "<b>dork</b>"
    assert expecting == str(b)

    a = group.getInstanceOf("t")
    expecting = "literal} template"
    assert expecting == str(a)


def test_TemplateParameterDecls():
    """ Check syntax and setAttribute-time errors """
    templates = """
            group test;
            t() ::= \"no args but ref $foo$\"
            t2(item) ::= \"decl but not used is ok\" +
            t3(a,b,c,d) ::= <<$a$ $d$>>
            t4(a,b,c,d) ::= <<$a$ $b$ $c$ $d$>>
"""
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)

    """ check setting unknown arg in empty formal list """
    a = group.getInstanceOf("t")
    error = None
    try:
        a["foo"] = "x"  # want NoSuchElementException

    except NoSuchElementException as ex:
        error = ex.getMessage()

    expecting = "no such attribute: foo in template context [t]"
    assert expecting == error
    """ check setting known arg """
    a = group.getInstanceOf("t2")
    a["item"] = "x"  # shouldn't get exception
    """ check setting unknown arg in nonempty list of formal args """
    a = group.getInstanceOf("t3")
    a["b"] = "x"


def test_TemplateRedef():
    templates = """
            group test;
            a() ::= \"x\"
            b() ::= \"y\"
            a() ::= \"z\"
    """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), errors=errors)
    logger.debug(f"group: {group}")
    expecting = "redefinition of template: a"
    assert expecting == str(errors)


def test_MissingInheritedAttribute():
    templates = """
            group test;
            page(title,font) ::= << +
            <html> +
            <body> +
            $title$<br> +
            $body()$ +
            </body> +
            </html> +
            >> +
            body() ::= \"<font face=$font$>my body</font>\"
    """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)
    t = group.getInstanceOf("page")
    t.setAttribute("title", "my title")
    t["font"] = "Helvetica"  # body() will see it
    str(t)  # should be no problem


def test_FormalArgumentAssignment():
    templates = """
            group test;
            page() ::= <<$body(font=\"Times\")$>> +
            body(font) ::= \"<font face=$font$>my body</font>\"
    """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)
    t = group.getInstanceOf("page")
    expecting = "<font face=Times>my body</font>"
    assert expecting == str(t)


def test_UndefinedArgumentAssignment():
    templates = """
            group test;
            page(x) ::= <<$body(font=x)$>> +
            body() ::= \"<font face=$font$>my body</font>\"
    """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)
    t = group.getInstanceOf("page")
    t["x"] = "Times"
    error = ""
    try:
        str(t)

    except NoSuchElementException as iae:
        error = iae.getMessage()

    expecting = "template body has no such attribute: font in template context [page <invoke body arg context>]"
    assert expecting == error


def test_FormalArgumentAssignmentInApply():
    templates = """
            group test;
            page(name) ::= <<$name:bold(font=\"Times\")$>> +
            bold(font) ::= \"<font face=$font$><b>$it$</b></font>\"
    """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)
    t = group.getInstanceOf("page")
    t["name"] = "Ter"
    expecting = "<font face=Times><b>Ter</b></font>"
    assert expecting == str(t)


def test_UndefinedArgumentAssignmentInApply():
    templates = """
            group test;
            page(name,x) ::= <<$name:bold(font=x)$>> +
            bold() ::= \"<font face=$font$><b>$it$</b></font>\"
    """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)
    t = group.getInstanceOf("page")
    t["x"] = "Times"
    t["name"] = "Ter"
    error = ""
    try:
        str(t)

    except NoSuchElementException as iae:
        error = iae.getMessage()

    expecting = "template bold has no such attribute: font in template context [page <invoke bold arg context>]"
    assert expecting == error


def test_UndefinedAttributeReference():
    templates = """
            group test;
            page() ::= <<$bold()$>> +
            bold() ::= \"$name$\"
    """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)
    t = group.getInstanceOf("page")
    error = ""
    try:
        str(t)

    except NoSuchElementException as iae:
        error = iae.getMessage()

    expecting = "no such attribute: name in template context [page bold]"
    assert expecting == error


def test_UndefinedDefaultAttributeReference():
    templates = """
            group test;
            page() ::= <<$bold()$>> +
            bold() ::= \"$it$\"
    """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)
    t = group.getInstanceOf("page")
    error = ""
    try:
        str(t)

    except NoSuchElementException as nse:
        error = nse.getMessage()

    expecting = "no such attribute: it in template context [page bold]"
    assert expecting == error


def test_AngleBracketsWithGroupFile():
    """ mainly testing to ensure we don't get parse errors of above """
    templates = """
            group test;
            a(s) ::= \"<s:{case <i> : <it> break;}>\" +
            b(t) ::= \"<t; separator=\\\",\\\">\"
            c(t) ::= << <t; separator=\",\"> >>
    """
    group = st3g(io.StringIO(templates))
    t = group.getInstanceOf("a")
    t["s"] = "Test"
    expecting = "case 1 : Test break;"
    assert expecting == str(t)


def test_AngleBracketsNoGroup():
    st = st3t(
        "Tokens : <rules; separator=\"|\"> ;",
        AngleBracketTemplateLexer.Lexer)
    st["rules"] = "A"
    st["rules"] = "B"
    expecting = "Tokens : A|B ;"
    assert expecting == str(st)


def test_RegionRef():
    templates = """
            group test;
            a() ::= \"X$@r()$Y\"
    """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)
    st = group.getInstanceOf("a")
    result = str(st)
    expecting = "XY"
    assert expecting == result


def test_EmbeddedRegionRef():
    templates = """
            group test;
            a() ::= \"X$@r$blort$@end$Y\"
    """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)
    st = group.getInstanceOf("a")
    result = str(st)
    expecting = "XblortY"
    assert expecting == result


def test_RegionRefAngleBrackets():
    templates = """
            group test;
            a() ::= \"X<@r()>Y\"
    """
    group = st3g(io.StringIO(templates))
    st = group.getInstanceOf("a")
    result = str(st)
    expecting = "XY"
    assert expecting == result


def test_EmbeddedRegionRefAngleBrackets():
    """ FIXME: This test fails due to inserted white space... """
    templates = """
            group test;
            a() ::= \"X<@r>blort<@end>Y\"
    """
    group = st3g(io.StringIO(templates))
    st = group.getInstanceOf("a")
    result = str(st)
    expecting = "XblortY"
    assert expecting == result


def test_EmbeddedRegionRefWithNewlinesAngleBrackets():
    templates = """
            group test;
            a() ::= \"X<@r>
            blort
            <@end>
            Y\"
    """
    group = st3g(io.StringIO(templates))
    st = group.getInstanceOf("a")
    result = str(st)
    expecting = "XblortY"
    assert expecting == result


def test_RegionRefWithDefAngleBrackets():
    templates = """
            group test;
            a() ::= \"X<@r()>Y\"
            @a.r() ::= \"foo\"
    """
    group = st3g(io.StringIO(templates))
    st = group.getInstanceOf("a")
    result = str(st)
    expecting = "XfooY"
    assert expecting == result


def test_RegionRefWithDefInConditional():
    templates = """
            group test;
            a(v) ::= \"X<if(v)>A<@r()>B<endif>Y\"
            @a.r() ::= \"foo\"
    """
    group = st3g(io.StringIO(templates))
    st = group.getInstanceOf("a")
    st["v"] = True
    result = str(st)
    expecting = "XAfooBY"
    assert expecting == result


def test_RegionRefWithImplicitDefInConditional():
    templates = """
            group test;
            a(v) ::= \"X<if(v)>A<@r>yo<@end>B<endif>Y\"
            @a.r() ::= \"foo\"
    """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), errors=errors)
    st = group.getInstanceOf("a")
    st["v"] = True
    result = str(st)
    expecting = "XAyoBY"
    assert expecting == result

    err_result = str(errors)
    err_expecting = "group test line 3: redefinition of template region: @a.r"
    assert err_expecting == err_result


def test_RegionOverride():
    templates1 = """
            group super;
            "a() ::= \"X<@r()>Y\"" +
            @a.r() ::= \"foo\"
    """
    group = st3g(io.StringIO(templates1))

    templates2 = """
            group sub;
            @a.r() ::= \"foo\"
    """
    subGroup = st3g(io.StringIO(templates2), AngleBracketTemplateLexer.Lexer, None, group)

    st = subGroup.getInstanceOf("a")
    result = str(st)
    expecting = "XfooY"
    assert expecting == result


def test_RegionOverrideRefSuperRegion():
    templates1 = """
            group super;
            "a() ::= \"X<@r()>Y\"" +
            @a.r() ::= \"foo\"
    """
    group = st3g(io.StringIO(templates1))

    templates2 = """
            group sub;
            @a.r() ::= \"A<@super.r()>B\"
    """
    subGroup = st3g(io.StringIO(templates2), AngleBracketTemplateLexer.Lexer, None, group)

    st = subGroup.getInstanceOf("a")
    result = str(st)
    expecting = "XAfooBY"
    assert expecting == result


def test_RegionOverrideRefSuperRegion3Levels():
    """ Bug: This was causing infinite recursion: """
    """ getInstanceOf(super::a) """
    """ getInstanceOf(sub::a) """
    """ getInstanceOf(subsub::a) """
    """ getInstanceOf(subsub::region__a__r) """
    """ getInstanceOf(subsub::super.region__a__r) """
    """ getInstanceOf(subsub::super.region__a__r) """
    """ getInstanceOf(subsub::super.region__a__r) """
    """ ... """
    """ Somehow, the ref to super in subsub is not moving up the chain """
    """ to the @super.r(); oh, i introduced a bug when i put setGroup """
    """ into STG.getInstanceOf()! """

    templates1 = """
            group super;
            "a() ::= \"X<@r()>Y\"" +
            @a.r() ::= \"foo\"
    """
    group = st3g(io.StringIO(templates1))

    templates2 = """
            group sub;
            @a.r() ::= \"<@super.r()>2\"
    """
    subGroup = st3g(io.StringIO(templates2), AngleBracketTemplateLexer.Lexer, None, group)

    templates3 = """
            group subsub;
            @a.r() ::= \"<@super.r()>3\"
    """
    subSubGroup = st3g(io.StringIO(templates3), AngleBracketTemplateLexer.Lexer, None, subGroup)

    st = subSubGroup.getInstanceOf("a")
    result = str(st)
    expecting = "Xfoo23Y"
    assert expecting == result


def test_RegionOverrideRefSuperImplicitRegion():
    templates1 = """
            group super;
            a() ::= \"X<@r>foo<@end>Y\"
    """
    group = st3g(io.StringIO(templates1))

    templates2 = """
            group sub;
            @a.r() ::= \"A<@super.r()>\"
    """
    subGroup = st3g(io.StringIO(templates2), AngleBracketTemplateLexer.Lexer, None, group)

    st = subGroup.getInstanceOf("a")
    result = str(st)
    expecting = "XAfooY"
    assert expecting == result


def test_EmbeddedRegionRedefError():
    """ cannot define an embedded template within group """
    templates = """
            group test;
            "a() ::= \"X<@r>dork<@end>Y\"" +
            @a.r() ::= \"foo\"
"""
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), errors=errors)
    st = group.getInstanceOf("a")
    str(st)
    result = str(errors)
    expecting = "group test line 2: redefinition of template region: @a.r"
    assert expecting == result


def test_ImplicitRegionRedefError():
    """ cannot define an implicitly-defined template more than once """
    templates = """
            group test;
            a() ::= \"X<@r()>Y\"
            @a.r() ::= \"foo\"
            @a.r() ::= \"bar\"
"""
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), errors=errors)
    st = group.getInstanceOf("a")
    str(st)
    result = str(errors)
    expecting = "group test line 4: redefinition of template region: @a.r"
    assert expecting == result


def test_ImplicitOverriddenRegionRedefError():
    templates1 = """
        group super;
        "a() ::= \"X<@r()>Y\"" +
        @a.r() ::= \"foo\"
    """
    group = st3g(io.StringIO(templates1))

    templates2 = """
        group sub;
        @a.r() ::= \"foo\"
        @a.r() ::= \"bar\"
    """
    errors = st3err.DEFAULT_ERROR_LISTENER
    subGroup = st3g(io.StringIO(templates2), AngleBracketTemplateLexer.Lexer,
                    errors=errors, superGroup=group)

    st = subGroup.getInstanceOf("a")
    logger.debug(f"st: {st}")
    result = str(errors)
    expecting = "group sub line 3: redefinition of template region: @a.r"
    assert expecting == result


def test_UnknownRegionDefError():
    """ cannot define an implicitly-defined template more than once """
    templates = """
            group test;
            a() ::= \"X<@r()>Y\"
            @a.q() ::= \"foo\"
    """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), errors=errors)
    st = group.getInstanceOf("a")
    str(st)
    result = str(errors)
    expecting = "group test line 3: template a has no region called q"
    assert expecting == result


def test_SuperRegionRefError():
    templates1 = """
        group super;
        "a() ::= \"X<@r()>Y\"" +
        @a.r() ::= \"foo\"
    """
    group = st3g(io.StringIO(templates1))

    templates2 = """
        group sub;
        @a.r() ::= \"A<@super.q()>B\"
    """
    errors = st3err.DEFAULT_ERROR_LISTENER
    subGroup = st3g(io.StringIO(templates2), lexer=AngleBracketTemplateLexer.Lexer,
                    errors=errors, superGroup=group)

    st = subGroup.getInstanceOf("a")
    logger.debug(f"st: {st}")
    result = str(errors)
    expecting = "template a has no region called q"
    assert expecting == result


def test_MissingEndRegionError():
    """ cannot define an implicitly-defined template more than once """
    templates = """
            group test;
            a() ::= \"X$@r$foo\"
    """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), lexer=DefaultTemplateLexer.Lexer,
                 errors=errors)
    st = group.getInstanceOf("a")
    str(st)
    result = str(errors)
    expecting = "missing region r $@end$ tag"
    assert expecting == result


def test_MissingEndRegionErrorAngleBrackets():
    """ cannot define an implicitly-defined template more than once """
    templates = """
            group test;
            a() ::= \"X<@r>foo\"
    """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), errors=errors)
    st = group.getInstanceOf("a")
    str(st)
    result = str(errors)
    expecting = "missing region r <@end> tag"
    assert expecting == result


def test_SimpleInheritance():
    """ make a bold template in the super group that you can inherit from sub """
    supergroup = st3g("super")
    subgroup = st3g("sub")
    bold = supergroup.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    subgroup.setSuperGroup(supergroup)
    errors = st3err.DEFAULT_ERROR_LISTENER
    subgroup.setErrorListener(errors)
    supergroup.setErrorListener(errors)
    duh = st3t(subgroup, "$name:bold()$")
    duh["name"] = "Terence"
    expecting = "<b>Terence</b>"
    assert expecting == str(duh)


def test_OverrideInheritance():
    """ make a bold template in the super group and one in subgroup """
    supergroup = st3g("super")
    subgroup = st3g("sub")
    supergroup.defineTemplate("bold", "<b>$it$</b>")
    subgroup.defineTemplate("bold", "<strong>$it$</strong>")
    subgroup.setSuperGroup(supergroup)
    errors = st3err.DEFAULT_ERROR_LISTENER
    subgroup.setErrorListener(errors)
    supergroup.setErrorListener(errors)
    duh = st3t(subgroup, "$name:bold()$")
    duh["name"] = "Terence"
    expecting = "<strong>Terence</strong>"
    assert expecting == str(duh)


def test_MultiLevelInheritance():
    """ must loop up two levels to find bold() """
    rootgroup = st3g("root")
    level1 = st3g("level1")
    level2 = st3g("level2")
    rootgroup.defineTemplate("bold", "<b>$it$</b>")
    level1.setSuperGroup(rootgroup)
    level2.setSuperGroup(level1)
    errors = st3err.DEFAULT_ERROR_LISTENER
    rootgroup.setErrorListener(errors)
    level1.setErrorListener(errors)
    level2.setErrorListener(errors)
    duh = st3t(level2, "$name:bold()$")
    duh["name"] = "Terence"
    expecting = "<b>Terence</b>"
    assert expecting == str(duh)


def test_ComplicatedInheritance():
    """ in super: decls invokes labels """
    """ in sub:   overridden decls which calls super.decls """
    """           overridden labels """
    """ Bug: didn't see the overridden labels.  In other words, """
    """ the overridden decls called super which called labels, but """
    """ didn't get the subgroup overridden labels--it calls the """
    """ one in the superclass.  Ouput was "DL" not "DSL"; didn't """
    """ invoke sub's labels(). """
    basetemplates = """
        group base;
        decls() ::= \"D<labels()>\"
        labels() ::= \"L\"
"""
    base = st3g(io.StringIO(basetemplates))
    subtemplates = """
        group sub;
        decls() ::= \"<super.decls()>\"
        labels() ::= \"SL\"
    """
    sub = st3g(io.StringIO(subtemplates))
    sub.setSuperGroup(base)
    st = sub.getInstanceOf("decls")
    expecting = "DSL"
    result = str(st)
    assert expecting == result


def test_3LevelSuperRef():
    templates1 = """
        group super;
        r() ::= \"foo\"
    """
    group = st3g(io.StringIO(templates1))

    templates2 = """
        group sub;
        r() ::= \"<super.r()>2\"
    """
    subGroup = st3g(io.StringIO(templates2), AngleBracketTemplateLexer.Lexer, None, group)

    templates3 = """
        group subsub;
        r() ::= \"<super.r()>3\"
    """
    subSubGroup = st3g(io.StringIO(templates3), AngleBracketTemplateLexer.Lexer, None, subGroup)

    st = subSubGroup.getInstanceOf("r")
    result = str(st)
    expecting = "foo23"
    assert expecting == result


def test_ExprInParens():
    """ specify a template to apply to an attribute
    Use a template group, so we can specify the start/stop chars
    """
    group = st3g("dummy", ".")
    bold = group.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    duh = st3t(group, "$(\"blort: \"+(list)):bold()$")
    duh["list"] = "a"
    duh["list"] = "b"
    duh["list"] = "c"
    logger.info(duh)
    expecting = "<b>blort: abc</b>"
    assert expecting == str(duh)


def test_MultipleAdditions():
    """ specify a template to apply to an attribute """
    """ Use a template group so we can specify the start/stop chars """
    group = st3g("dummy", ".")
    group.defineTemplate("link", "<a href=\"$url$\"><b>$title$</b></a>")
    duh = st3t(group, "$link(url=\"/member/view?ID=\"+ID+\"&x=y\"+foo, title=\"the title\")$")
    duh["ID"] = "3321"
    duh["foo"] = "fubar"
    expecting = "<a href=\"/member/view?ID=3321&x=yfubar\"><b>the title</b></a>"
    assert expecting == str(duh)


def test_CollectionAttributes():
    group = st3g("test")
    bold = group.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    t = st3t(group, "$data$, $data:bold()$, "
                    "$list:bold():bold()$, $array$, $a2$, $a3$, $a4$")
    v = ["1", "2", "3"]
    alist = ["a", "b", "c"]
    t["data"] = v
    t["list"] = alist
    t.setAttribute("array", ["x", "y"])
    t.setAttribute("a2", [10, 20])
    t.setAttribute("a3", [1.2, 1.3])
    t.setAttribute("a4", [8.7, 9.2])
    logger.info(t)
    expecting = "123, <b>1</b><b>2</b><b>3</b>, " \
                "<b><b>a</b></b><b><b>b</b></b><b><b>c</b></b>, xy, 1020, 1.21.3, 8.79.2"
    assert expecting == str(t)


def test_ParenthesizedExpression():
    group = st3g("test")
    bold = group.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    t = st3t(group, "$(f+l):bold()$")
    t["f"] = "Joe"
    t["l"] = "Schmoe"
    logger.info(t)
    expecting = "<b>JoeSchmoe</b>"
    assert expecting == str(t)


def test_ApplyTemplateNameExpression():
    group = st3g("test")
    bold = group.defineTemplate("foobar", "foo$attr$bar")
    logger.debug(f"bold: {bold}")
    t = st3t(group, "$data:(name+\"bar\")()$")
    t["data"] = "Ter"
    t["data"] = "Tom"
    t["name"] = "foo"
    logger.info(t)
    expecting = "fooTerbarfooTombar"
    assert expecting == str(t)


def test_ApplyTemplateNameTemplateEval():
    group = st3g("test")
    foobar = group.defineTemplate("foobar", "foo$it$bar")
    a = group.defineTemplate("a", "$it$bar")
    logger.debug(f"foobar: {foobar}, a: {a}")
    t = st3t(group, "$data:(\"foo\":a())()$")
    t["data"] = "Ter"
    t["data"] = "Tom"
    logger.info(t)
    expecting = "fooTerbarfooTombar"
    assert expecting == str(t)


def test_TemplateNameExpression():
    group = st3g("test")
    foo = group.defineTemplate("foo", "hi there!")
    logger.debug(f"foo: {foo}")
    t = st3t(group, "$(name)()$")
    t["name"] = "foo"
    logger.info(t)
    expecting = "hi there!"
    assert expecting == str(t)


def test_MissingEndDelimiter():
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    st = st3t(group, "stuff $a then more junk etc...")
    logger.debug(f"st: {st}")
    expectingError = "problem parsing template 'anonymous': line 1:31: expecting '$', found '<EOF>'"
    logger.info("error: '" + errors + "'")
    logger.info("expecting: '" + expectingError + "'")
    assert str(errors).startswith(expectingError)


def test_SetButNotRefd():
    st3.lintMode = True
    group = st3g("test")
    t = st3t(group, "$a$ then $b$ and $c$ refs.")
    t["a"] = "Terence"
    t["b"] = "Terence"
    t["cc"] = "Terence"  # oops...should be 'c'
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener()
    expectingError = "anonymous: set but not used: cc"
    result = str(t)  # result is irrelevant
    logger.info(f"result {result}, error: {errors}")
    logger.info(f"expecting: {expectingError}")
    st3.lintMode = False
    assert expectingError == str(errors)


def test_NullTemplateApplication():
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, "$names:bold(x=it)$")
    t["names"] = "Terence"

    error = None
    try:
        str(t)

    except IllegalArgumentException as iae:
        error = iae.getMessage()

    expecting = "Can't find template bold.st; context is [anonymous]; group hierarchy is [test]"
    assert expecting == error


def test_NullTemplateToMultiValuedApplication():
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, "$names:bold(x=it)$")
    t["names"] = "Terence"
    t["names"] = "Tom"
    logger.info(t)
    error = None
    try:
        str(t)

    except IllegalArgumentException as iae:
        error = iae.getMessage()

    expecting = "Can't find template bold.st; context is [anonymous]; group hierarchy is [test]"
    # bold not found...empty string
    assert expecting == error


def test_ChangingAttrValueTemplateApplicationToVector():
    group = st3g("test")
    bold = group.defineTemplate("bold", "<b>$x$</b>")
    logger.debug(f"bold: {bold}")
    t = st3t(group, "$names:bold(x=it)$")
    t["names"] = "Terence"
    t["names"] = "Tom"
    logger.info("'" + str(t) + "'")
    expecting = "<b>Terence</b><b>Tom</b>"
    assert expecting == str(t)


def test_ChangingAttrValueRepeatedTemplateApplicationToVector():
    group = st3g("dummy", ".")
    bold = group.defineTemplate("bold", "<b>$item$</b>")
    italics = group.defineTemplate("italics", "<i>$it$</i>")
    logger.debug(f"bold: {bold}, italic: {italics}")
    members = st3t(group, "$members:bold(item=it):italics(it=it)$")
    members["members"] = "Jim"
    members["members"] = "Mike"
    members["members"] = "Ashar"
    logger.info(f"members={members}")
    expecting = "<i><b>Jim</b></i><i><b>Mike</b></i><i><b>Ashar</b></i>"
    assert expecting == str(members)


def test_AlternatingTemplateApplication():
    group = st3g("dummy", ".")
    listItem = group.defineTemplate("listItem", "<li>$it$</li>")
    bold = group.defineTemplate("bold", "<b>$it$</b>")
    italics = group.defineTemplate("italics", "<i>$it$</i>")
    logger.debug(f"items: {listItem}, bold: {bold}, italics: {italics}")
    item = st3t(group, "$item:bold(),italics():listItem()$")
    item["item"] = "Jim"
    item["item"] = "Mike"
    item["item"] = "Ashar"
    logger.info("ITEM=" + item)
    expecting = "<li><b>Jim</b></li><li><i>Mike</i></li><li><b>Ashar</b></li>"
    assert str(item) == expecting


def test_ExpressionAsRHSOfAssignment():
    group = st3g("test")
    hostname = group.defineTemplate("hostname", "$machine$.jguru.com")
    bold = group.defineTemplate("bold", "<b>$x$</b>")
    logger.debug(f"host: {hostname}, bold: {bold}")
    t = st3t(group, "$bold(x=hostname(machine=\"www\"))$")
    expecting = "<b>www.jguru.com</b>"
    assert expecting == str(t)


def test_TemplateApplicationAsRHSOfAssignment():
    group = st3g("test")
    hostname = group.defineTemplate("hostname", "$machine$.jguru.com")
    bold = group.defineTemplate("bold", "<b>$x$</b>")
    italics = group.defineTemplate("italics", "<i>$it$</i>")
    logger.debug(f"host: {hostname}, bold: {bold}, italics: {italics}")
    t = st3t(group, "$bold(x=hostname(machine=\"www\"):italics())$")
    expecting = "<b><i>www.jguru.com</i></b>"
    assert expecting == str(t)


def test_ParameterAndAttributeScoping():
    group = st3g("test")
    italics = group.defineTemplate("italics", "<i>$x$</i>")
    bold = group.defineTemplate("bold", "<b>$x$</b>")
    logger.debug(f"bold: {bold}, italics: {italics}")
    t = st3t(group, "$bold(x=italics(x=name))$")
    t["name"] = "Terence"
    logger.info(t)
    expecting = "<b><i>Terence</i></b>"
    assert expecting == str(t)


def test_ComplicatedSeparatorExpr():
    """ make separator a complicated expression with args passed to included template """
    group = st3g("test")
    bold = group.defineTemplate("bulletSeparator", "</li>$foo$<li>")
    logger.debug(f"bold: {bold}")
    t = st3t(group, "<ul>$name; separator=bulletSeparator(foo=\" \")+\"&nbsp;\"$</ul>")
    t["name"] = "Ter"
    t["name"] = "Tom"
    t["name"] = "Mel"
    logger.info(t)
    expecting = "<ul>Ter</li> <li>&nbsp;Tom</li> <li>&nbsp;Mel</ul>"
    assert expecting == str(t)


def test_AttributeRefButtedUpAgainstEndifAndWhitespace():
    group = st3g("test")
    a = st3t(group, "$if (!firstName)$$email$$endif$")
    a["email"] = "parrt@jguru.com"
    expecting = "parrt@jguru.com"
    assert str(a) == expecting


def test_StringConcatenationOnSingleValuedAttributeViaTemplateLiteral():
    group = st3g("test")
    bold = group.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    # a =    ST3(group, "$\" Parr\":bold()$")
    b = st3t(group, "$bold(it={$name$ Parr})$")
    # a["name"] = "Terence"
    b["name"] = "Terence"
    expecting = "<b>Terence Parr</b>"
    # assert str(a) ==  expecting
    assert str(b) == expecting


def test_StringConcatenationOpOnArg():
    group = st3g("test")
    bold = group.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    b = st3t(group, "$bold(it=name+\" Parr\")$")
    # a["name"] = "Terence"
    b["name"] = "Terence"
    expecting = "<b>Terence Parr</b>"
    # assert expecting == str(a)
    assert expecting == str(b)


def test_StringConcatenationOpOnArgWithEqualsInString():
    group = st3g("test")
    bold = group.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    b = st3t(group, "$bold(it=name+\" Parr=\")$")
    # a["name"] = "Terence"
    b["name"] = "Terence"
    expecting = "<b>Terence Parr=</b>"
    # assert expecting == str(a)
    assert expecting == str(b)


def test_ApplyingTemplateFromDiskWithPrecompiledIF():
    """ Create a temporary working directory 
    write the template files first to that directory.
    Specify a template to apply to an attribute
    Use a template group, so we can specify the start/stop chars
    """
    with temppathlib.TemporaryDirectory() as tmp_dir:
        page_file = tmp_dir.path / "page.st"
        with open(page_file, "wb") as writer:
            writer.write(b"""
                <html><head>
                  <title>PeerScope: $title$</title>
                  </head>
                  <body>
                      $if(member)$User: $member:terse()$$endif$
                  </body>
                </head>
                """)

        terse_file = tmp_dir.path / "terse.st"
        with open(terse_file, "wb") as writer:
            writer.write(b"""
            "$it.firstName$ $it.lastName$ (<tt>$it.email$</tt>)"
            """)

        group = st3g("dummy", str(tmp_dir.path))

        a = group.getInstanceOf("page")
        a.setAttribute("member", Connector())
        expecting = """ 
                <html><head>
                </head>
                <body>
                User: Terence Parr (<tt>parrt@jguru.com</tt>)
                </body>
                "</head>"
                """
        logger.info("'" + a + "'")
        assert expecting == str(a)


def test_MultiValuedAttributeWithAnonymousTemplateUsingIndexVariableI():
    tgroup = st3g("dummy", ".")
    t = st3t(tgroup, """
    List:
    
    foo
       
    $names:{<br>$i$. $it$
    }$
    """)
    t["names"] = "Terence"
    t["names"] = "Jim"
    t["names"] = "Sriram"
    logger.info(t)
    expecting = """
             List:
              
            foo
            <br>1. Terence
            <br>2. Jim
            <br>3. Sriram
    """
    assert expecting == str(t)


def test_FindTemplateInCLASSPATH():
    """ Look for templates in CLASSPATH as resources
    "method.st" references body() so "body.st" will be loaded too
    """
    mgroup = st3g("method stuff", AngleBracketTemplateLexer.Lexer)
    m = mgroup.getInstanceOf("org/antlr/stringtemplate/test/method")
    m["visibility"] = "public"
    m["name"] = "foobar"
    m["returnType"] = "void"
    m["statements"] = "i=1;"  # body inherits these from method
    m["statements"] = "x=i;"
    expecting = """
            public void foobar() {
            \t// start of a body
            \ti=1;
            \tx=i;
            \t// end of a body
            "}"
            """
    logger.info(m)
    assert expecting == str(m)


def test_ApplyTemplateToSingleValuedAttribute():
    group = st3g("test")
    bold = group.defineTemplate("bold", "<b>$x$</b>")
    logger.debug(f"bold: {bold}")
    name = st3t(group, "$name:bold(x=name)$")
    name["name"] = "Terence"
    assert "<b>Terence</b>" == str(name)


def test_StringLiteralAsAttribute():
    group = st3g("test")
    bold = group.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    name = st3t(group, "$\"Terence\":bold()$")
    assert "<b>Terence</b>" == str(name)


def test_ApplyTemplateToSingleValuedAttributeWithDefaultAttribute():
    group = st3g("test")
    bold = group.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    name = st3t(group, "$name:bold()$")
    name["name"] = "Terence"
    assert "<b>Terence</b>" == str(name)


def test_ApplyAnonymousTemplateToSingleValuedAttribute():
    """ specify a template to apply to an attribute 
    Use a template group, so we can specify the start/stop chars """
    group = st3g("dummy", ".")
    item = st3t(group, "$item:{<li>$it$</li>}$")
    item["item"] = "Terence"
    assert "<li>Terence</li>" == str(item)


def test_ApplyAnonymousTemplateToMultiValuedAttribute():
    """ specify a template to apply to an attribute
    Use a template group, so we can specify the start/stop chars
    demonstrate setting arg to anonymous subtemplate
    """
    group = st3g("dummy", ".")
    alist = st3t(group, "<ul>$items$</ul>")
    item = st3t(group, "$item:{<li>$it$</li>}; separator=\",\"$")
    item["item"] = "Terence"
    item["item"] = "Jim"
    item["item"] = "John"
    alist["items"] = item  # nested template
    expecting = "<ul><li>Terence</li>,<li>Jim</li>,<li>John</li></ul>"
    assert expecting == str(alist)


def test_ApplyAnonymousTemplateToAggregateAttribute():
    """ also testing wacky spaces in aggregate spec """
    st = st3t("$items:{$it.lastName$, $it.firstName$\n}$")
    st.setAttribute("items.{ firstName ,lastName}", "Ter", "Parr")
    st.setAttribute("items.{firstName, lastName }", "Tom", "Burns")
    expecting = """
            Parr, Ter +
            Burns, Tom
    """
    assert expecting == str(st)


def test_RepeatedApplicationOfTemplateToSingleValuedAttribute():
    group = st3g("dummy", ".")
    bold = group.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    item = st3t(group, "$item:bold():bold()$")
    item["item"] = "Jim"
    assert "<b><b>Jim</b></b>" == str(item)


def test_RepeatedApplicationOfTemplateToMultiValuedAttributeWithSeparator():
    """ first application of template must yield another vector!
    ### NEED A TEST OF obj ASSIGNED TO ARG?
     """
    group = st3g("dummy", ".")
    bold = group.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    item = st3t(group, "$item:bold():bold(); separator=\",\"$")
    item["item"] = "Jim"
    item["item"] = "Mike"
    item["item"] = "Ashar"
    logger.info("ITEM={},", item)
    expecting = "<b><b>Jim</b></b>,<b><b>Mike</b></b>,<b><b>Ashar</b></b>"
    assert str(item) == expecting


def test_MultiValuedAttributeWithSeparator():
    # """ if column can be multi-valued, specify a separator """
    group = st3g("dummy", ".", AngleBracketTemplateLexer.Lexer)
    query = st3t(group, "SELECT <distinct> <column; separator=\", \"> FROM <table>;")
    query["column"] = "name"
    query["column"] = "email"
    query["table"] = "User"
    # """ uncomment next line to make "DISTINCT" appear in output """
    # """ query["distince"] = "DISTINCT" """
    # """ System.out.println(query); """
    assert "SELECT  name == str(email FROM User;" == str(query)


def test_SingleValuedAttributes():
    """ all attributes are single-valued: """
    query = st3t("SELECT $column$ FROM $table$;")
    query["column"] = "name"
    query["table"] = "User"
    """ System.out.println(query); """
    assert "SELECT name FROM User;" == str(query)


def test_IFTemplate():
    group = st3g("dummy", ".", AngleBracketTemplateLexer.Lexer)
    t = st3t(group, "SELECT <column> FROM PERSON "
                    "<if(cond)>WHERE ID=<id><endif>;")
    t["column"] = "name"
    t["cond"] = True
    t["id"] = "231"
    assert "SELECT name FROM PERSON WHERE ID=231;" == str(t)


def test_IFCondWithParensTemplate():
    group = st3g("dummy", ".", AngleBracketTemplateLexer.Lexer)
    t = st3t(group, "<if(map.(type))><type> <prop>=<map.(type)>;<endif>")
    amap = {"int": "0"}
    t["map"] = amap
    t["prop"] = "x"
    t["type"] = "int"
    assert "int x=0;" == str(t)


def test_IFCondWithParensDollarDelimsTemplate():
    group = st3g("dummy", ".")
    t = st3t(group, "$if(map.(type))$$type$ $prop$=$map.(type)$;$endif$")
    amap = dict()
    amap["int"] = "0"
    t["map"] = amap
    t["prop"] = "x"
    t["type"] = "int"
    assert "int x=0;" == str(t)


def test_IFBoolean():
    group = st3g("dummy", ".")
    t = st3t(group, "$if(b)$x$endif$ $if(!b)$y$endif$")
    t["b"] = True
    assert str(t) == "x "

    t = t.getInstanceOf()
    t["b"] = False
    assert " y" == str(t)


def test_NestedIFTemplate():
    group = st3g("dummy", ".", AngleBracketTemplateLexer.Lexer)
    t = st3t(group, """
            ack<if(a)>
            foo
            <if(!b)>stuff<endif>
            <if(b)>no<endif>
            junk
            "<endif>"
            """)
    t["a"] = "blort"
    # """ leave b as None """
    logger.info("t=" + t)
    expecting = """
            ackfoo
            stuff
            "junk"
    """
    assert expecting == str(t)


def test_IFConditionWithTemplateApplication():
    group = st3g("dummy", ".")
    t = st3t(group, "$if(names:{$it$})$Fail!$endif$ $if(!names:{$it$})$Works!$endif$")
    t["b"] = True
    assert str(t) == " Works!"


class Connector:
    def getID(self):
        return 1

    def getFirstName(self):
        return "Terence"

    def getLastName(self):
        return "Parr"

    def getEmail(self):
        return "parrt@jguru.com"

    def getBio(self):
        return "Superhero by night..."

    def getCanEdit(self):
        return False


class Connector2:
    def getID(self):
        return 2

    def getFirstName(self):
        return "Tom"

    def getLastName(self):
        return "Burns"

    def getEmail(self):
        return "tombu@jguru.com"

    def getBio(self):
        return "Superhero by day..."

    def getCanEdit(self):
        return True


def test_ObjectPropertyReference():
    group = st3g("dummy", ".")
    t = st3t(group, """
                    <b>Name: $p.firstName$ $p.lastName$</b><br>
                    <b>Email: $p.email$</b><br>
                    "$p.bio$"
            """)
    t["p"] = Connector()
    logger.info("t is " + str(t))
    expecting = """
            <b>Name: Terence Parr</b><br>
            <b>Email: parrt@jguru.com</b><br>
            "Superhero by night..."
    """
    assert expecting == str(t)


def test_ApplyRepeatedAnonymousTemplateWithForeignTemplateRefToMultiValuedAttribute():
    """ specify a template to apply to an attribute 
    Use a template group, so we can specify the start/stop chars
    """
    group = st3g("dummy", ".")
    group.defineTemplate("link", "<a href=\"$url$\"><b>$title$</b></a>")
    duh = st3t(group, """
    start|$p:{$link(url=\"/member/view?ID=\"+it.ID, title=it.firstName)$ $if(it.canEdit)$canEdit$endif$}:
    {$it$<br>\n}$|end
    """)
    duh["p"] = Connector()
    duh["p"] = Connector2()
    logger.info(duh)
    expecting = """
    start|<a href=\"/member/view?ID=1\"><b>Terence</b></a> <br>
        <a href=\"/member/view?ID=2\"><b>Tom</b></a> canEdit<br>
        "|end"
    """
    assert expecting == str(duh)


class Tree:
    def __init__(self, t):
        self.text = t
        self.children = None

    def getText(self):
        return self.text

    def addChild(self, c):
        self.children.add(c)

    def getFirstChild(self):
        if self.children.size() < 1:
            return None

        return self.children.get(0)

    def getChildren(self):
        return self.children


def test_Recursion():
    group = st3g("dummy", ".", AngleBracketTemplateLexer.Lexer)
    group.defineTemplate("tree", """
    <if(it.firstChild)>
      ( <it.text> <it.children:tree(); separator=\" \"> )
    <else>
      <it.text>
    <endif>
    """)
    tree = group.getInstanceOf("tree")
    """ build ( a b (c d) e ) """
    root = Tree("a")
    root.addChild(Tree("b"))
    subtree = Tree("c")
    subtree.addChild(Tree("d"))
    root.addChild(subtree)
    root.addChild(Tree("e"))
    tree["it"] = root
    expecting = "( a b ( c d ) e )"
    assert expecting == str(tree)


def test_NestedAnonymousTemplates():
    group = st3g("dummy", ".")
    t = st3t(group, """
                        $A:{
                          <i>$it:{
                            <b>$it$</b>
                          }$</i>
                        "}$"
                """)
    t["A"] = "parrt"
    expecting = """
            <i>
            <b>parrt</b>
            </i>
"""
    assert expecting == str(t)


def test_AnonymousTemplateAccessToEnclosingAttributes():
    group = st3g("dummy", ".")
    t = st3t(group, """
                    $A:{
                      <i>$it:{
                        <b>$it$, $B$</b>
                      }$</i>
                    "}$"
            """)
    t["A"] = "parrt"
    t["B"] = "tombu"
    expecting = """
        <i>
        <b>parrt, tombu</b>
        </i>
"""
    assert expecting == str(t)


def test_NestedAnonymousTemplatesAgain():
    group = st3g("dummy", ".")
    logger.debug(f"group: {group}")
    t = st3t("""
                    group,
                    <table> +
                    $names:{<tr>$it:{<td>$it:{<b>$it$</b>}$</td>}$</tr>}$ +
                    </table>
            """)
    t["names"] = "parrt"
    t["names"] = "tombu"
    expecting = """
            <table>
            <tr><td><b>parrt</b></td></tr><tr><td><b>tombu</b></td></tr>
            "</table>" + newline
    """
    assert expecting == str(t)


def test_Escapes():
    group = st3g("dummy", ".")
    group.defineTemplate("foo", "$x$ && $it$")
    t = st3t(group, "$A:foo(x=\"dog\\\"\\\"\")$")
    u = st3t(group, "$A:foo(x=\"dog\\\"g\")$")
    v = st3t(group,
             """ $A:{$attr:foo(x="{dog}\"")$ is cool}$ """
             "$A:{$it:foo(x=\"\\{dog\\}\\\"\")$ is cool}$"
             )
    t["A"] = "ick"
    u["A"] = "ick"
    v["A"] = "ick"
    logger.info("t is '" + str(t) + "'")
    logger.info("u is '" + str(u) + "'")
    logger.info("v is '" + str(v) + "'")
    expecting = "dog\"\" && ick"
    assert expecting == str(t)
    expecting = "dog\"g && ick"
    assert expecting == str(u)
    expecting = "{dog}\" && ick is cool"
    assert expecting == str(v)


def test_EscapesOutsideExpressions():
    b = st3t("It\\'s ok...\\$; $a:{\\'hi\\', $it$}$")
    b["a"] = "Ter"
    expecting = "It\\'s ok...$; \\'hi\\', Ter"
    result = str(b)
    assert expecting == result


def test_ElseClause():
    e = st3t("""
            $if(title)$ +
            foo +
            $else$ +
            bar +
            "$endif$"
        """)
    e["title"] = "sample"
    expecting = "foo"
    assert expecting == str(e)

    e = e.getInstanceOf()
    expecting = "bar"
    assert expecting == str(e)


def test_ElseIfClause():
    e = st3t("""
            $if(x)$ +
            foo +
            $elseif(y)$ +
            bar +
            "$endif$"
        """)
    e["y"] = "yep"
    expecting = "bar"
    assert expecting == str(e)


def test_ElseIfClauseAngleBrackets():
    e = st3t("""
            <if(x)> +
            foo +
            <elseif(y)> +
            bar +
            "<endif>"
            """,
             AngleBracketTemplateLexer.Lexer
             )
    e["y"] = "yep"
    expecting = "bar"
    assert expecting == str(e)


def test_ElseIfClause2():
    e = st3t("""
            $if(x)$ +
            foo +
            $elseif(y)$ +
            bar +
            $elseif(z)$ +
            blort +
            "$endif$"
        """)
    e["z"] = "yep"
    expecting = "blort"
    assert expecting == str(e)


def test_ElseIfClauseAndElse():
    e = st3t("""
            $if(x)$ +
            foo +
            $elseif(y)$ +
            bar +
            $elseif(z)$ +
            z +
            $else$ +
            blort +
            "$endif$"
        """)
    expecting = "blort"
    assert expecting == str(e)


def test_NestedIF():
    e = st3t("""
            $if(title)$ +
            foo +
            $else$ +
            $if(header)$ +
            bar +
            $else$ +
            blort +
            $endif$ +
            "$endif$"
        """)
    e["title"] = "sample"
    expecting = "foo"
    assert expecting == str(e)

    e = e.getInstanceOf()
    e["header"] = "more"
    expecting = "bar"
    assert expecting == str(e)

    e = e.getInstanceOf()
    expecting = "blort"
    assert expecting == str(e)


def test_EmbeddedMultiLineIF():
    group = st3g("test")
    main = st3t(group, "$sub$")
    sub = st3t(group, """
            begin
            $if(foo)$
            $foo$
            $else$ +
            blort
            "$endif$" + newline
        """)
    sub["foo"] = "stuff"
    main["sub"] = sub
    expecting = """
        begin
        "stuff"
        """
    assert expecting == str(main)

    main = st3t(group, "$sub$")
    sub = sub.getInstanceOf()
    main["sub"] = sub
    expecting = """
        begin
        "blort"
        """
    assert expecting == str(main)


def test_SimpleIndentOfAttributeList():
    templates = """
            group test;
            "list(names) ::= <<" +
              $names; separator=\"\n\"$
            >>
    """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer, errors=errors)
    t = group.getInstanceOf("list")
    t["names"] = "Terence"
    t["names"] = "Jim"
    t["names"] = "Sriram"
    expecting = """
              Terence
              Jim
            "  Sriram"
            """
    assert expecting == str(t)


def test_IndentOfMultilineAttributes():
    templates = """
            group test;
            "list(names) ::= <<" +
              $names; separator=\"\n\"$
            >>
    """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer, errors=errors)
    t = group.getInstanceOf("list")
    t["names"] = "Terence\nis\na\nmaniac"
    t["names"] = "Jim"
    t["names"] = "Sriram\nis\ncool"
    expecting = """
              Terence
              is
              a
              maniac
              Jim
              Sriram
              is
            "  cool"
              """
    assert expecting == str(t)


def test_IndentOfMultipleBlankLines():
    """ no indent on blank line """
    templates = """
            group test;
            "list(names) ::= <<" +
              $names$
            >>
    """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer, errors=errors)
    t = group.getInstanceOf("list")
    t.setAttribute("names", "Terence\n\nis a maniac")
    expecting = """
              Terence
            "  is a maniac"
            """
    assert expecting == str(t)


def test_IndentBetweenLeftJustifiedLiterals():
    templates = """
            group test;
            "list(names) ::= <<" +
            Before: +
              $names; separator=\"\\n\"$
            after
            >>
            """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer, errors=errors)
    t = group.getInstanceOf("list")
    t["names"] = "Terence"
    t["names"] = "Jim"
    t["names"] = "Sriram"
    expecting = """
            Before:
              Terence
              Jim
              Sriram
            "after"
            """
    assert expecting == str(t)


def test_NestedIndent():
    templates = """
            group test;
            "method(name,stats) ::= <<" +
            void $name$() { +
            \t$stats; separator=\"\\n\"$

            >>
            ifstat(expr,stats) ::= << +
            if ($expr$) { +
              $stats; separator=\"\\n\"$ +
            "}" +
            >> +
            assign(lhs,expr) ::= <<$lhs$=$expr$;>>
            """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer, errors=errors)
    t = group.getInstanceOf("method")
    t["name"] = "foo"
    s1 = group.getInstanceOf("assign")
    s1["lhs"] = "x"
    s1["expr"] = "0"
    s2 = group.getInstanceOf("ifstat")
    s2["expr"] = "x>0"
    s2a = group.getInstanceOf("assign")
    s2a["lhs"] = "y"
    s2a["expr"] = "x+y"
    s2b = group.getInstanceOf("assign")
    s2b["lhs"] = "z"
    s2b["expr"] = "4"
    s2["stats"] = s2a
    s2["stats"] = s2b
    t["stats"] = s1
    t["stats"] = s2
    expecting = """
            void foo() {
            \tx=0;
            \tif (x>0) {
            \t  y=x+y;
            \t  z=4;
            \t}
            "}"
            """
    assert expecting == str(t)


def test_AlternativeWriter():
    """ Provide an alternative to the default writer
    """

    # w = StringTemplateWriter() {
    #     public void pushIndentation(String indent) {
    #
    #     public String popIndentation() {
    #         return None;
    #
    #     public void pushAnchorPoint() {
    #
    #     public void popAnchorPoint() {
    #
    #     public void setLineWidth(int lineWidth) { }
    #     public int write(String str, String wrap) throws IOException {
    #         return 0;
    #
    #     public int write(String str) throws IOException {
    #         buf.append(str)   # just pass thru
    #         return str.length();
    #
    #     public int writeWrapSeparator(String wrap) throws IOException {
    #         return 0;
    #
    #     public int writeSeparator(String str) throws IOException {
    #         return write(str);
    #
    # };
    # group = ST3G("test")
    # group.defineTemplate("bold", "<b>$x$</b>")
    # name =    ST3(group, "$name:bold(x=name)$")
    # name["name"] = "Terence"
    # name.write(w)
    # assert "<b>Terence</b>" == str(buf)


def test_ApplyAnonymousTemplateToMapAndSet():
    st = st3t("$items:{<li>$it$</li>}$")
    m = dict()
    m["a"] = "1"
    m["b"] = "2"
    m["c"] = "3"
    st["items"] = m
    expecting = "<li>1</li><li>2</li><li>3</li>"
    assert expecting == str(st)

    st = st.getInstanceOf()
    s = {"1", "2", "3"}
    st["items"] = s
    split = str(st).split("(</?li>){1,2}")
    assert "" == split[0]
    assert "1" == split[1]
    assert "2" == split[2]
    assert "3" == split[3]


def test_DumpMapAndSet():
    st = st3t("$items; separator=\",\"$")
    m = dict()
    m["a"] = "1"
    m["b"] = "2"
    m["c"] = "3"
    st["items"] = m
    expecting = "1,2,3"
    assert expecting == str(st)

    st = st.getInstanceOf()
    s = {"1", "2", "3"}
    st["items"] = s
    split = str(st).split(",")
    assert "1" == split[0]
    assert "2" == split[1]
    assert "3" == split[2]


class Connector3:
    def getValues(self):
        return [1, 2, 3]

    def getStuff(self):
        m = dict()
        m["a"] = "1"
        m["b"] = "2"
        return m


def test_ApplyAnonymousTemplateToArrayAndMapProperty():
    st = st3t("$x.values:{<li>$it$</li>}$")
    st.setAttribute("x", Connector3())
    expecting = "<li>1</li><li>2</li><li>3</li>"
    assert expecting == str(st)

    st = st3t("$x.stuff:{<li>$it$</li>}$")
    st.setAttribute("x", Connector3())
    expecting = "<li>1</li><li>2</li>"
    assert expecting == str(st)


def test_SuperTemplateRef():
    """ you can refer to a template defined in a super group via super.t() """
    group = st3g("super")
    subGroup = st3g("sub")
    subGroup.setSuperGroup(group)
    group.defineTemplate("page", "$font()$:text")
    group.defineTemplate("font", "Helvetica")
    subGroup.defineTemplate("font", "$super.font()$ and Times")
    st = subGroup.getInstanceOf("page")
    expecting = "Helvetica and Times:text"
    assert expecting == str(st)


def test_ApplySuperTemplateRef():
    group = st3g("super")
    subGroup = st3g("sub")
    subGroup.setSuperGroup(group)
    group.defineTemplate("bold", "<b>$it$</b>")
    subGroup.defineTemplate("bold", "<strong>$it$</strong>")
    subGroup.defineTemplate("page", "$name:super.bold()$")
    st = subGroup.getInstanceOf("page")
    st["name"] = "Ter"
    expecting = "<b>Ter</b>"
    assert expecting == str(st)


def test_LazyEvalOfSuperInApplySuperTemplateRef():
    """ this is the same as testApplySuperTemplateRef() test 
    except notice that here the supergroup defines page 
    As long as you create the instance via the subgroup, "super." 
    will evaluate lazily (i.e., not statically 
    during template compilation) to the templates 
     getGroup().superGroup value.  If I create instance
     of page in group not subGroup, however, I will get
     an error as superGroup is None for group "group". 
    """
    group = st3g("base")
    subGroup = st3g("sub")
    subGroup.setSuperGroup(group)
    group.defineTemplate("bold", "<b>$it$</b>")
    subGroup.defineTemplate("bold", "<strong>$it$</strong>")
    group.defineTemplate("page", "$name:super.bold()$")
    st = subGroup.getInstanceOf("page")
    st["name"] = "Ter"
    error = None
    try:
        str(st)

    except IllegalArgumentException as iae:
        error = iae.getMessage()

    expectingError = "base has no super group; invalid template: super.bold"
    assert expectingError == error


def test_TemplatePolymorphism():
    """ bold is defined in both super and sub
    if you create an instance of page via the subgroup,
    then bold() should evaluate to the subgroup not the super
    even though page is defined in the super.  Just like polymorphism.
    """
    group = st3g("super")
    subGroup = st3g("sub")
    subGroup.setSuperGroup(group)
    group.defineTemplate("bold", "<b>$it$</b>")
    group.defineTemplate("page", "$name:bold()$")
    subGroup.defineTemplate("bold", "<strong>$it$</strong>")
    st = subGroup.getInstanceOf("page")
    st["name"] = "Ter"
    expecting = "<strong>Ter</strong>"
    assert expecting == str(st)


def test_ListOfEmbeddedTemplateSeesEnclosingAttributes():
    templates = """
            group test;
            output(cond,items) ::= <<page: $items$>>
            my_body() ::= <<$font()$stuff>>
            "font() ::= <<$if(cond)$this$else$that$endif$>>"
            """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer, errors=errors)
    outputST = group.getInstanceOf("output")
    bodyST1 = group.getInstanceOf("my_body")
    bodyST2 = group.getInstanceOf("my_body")
    bodyST3 = group.getInstanceOf("my_body")
    outputST["items"] = bodyST1
    outputST["items"] = bodyST2
    outputST["items"] = bodyST3
    expecting = "page: thatstuffthatstuffthatstuff"
    assert expecting == str(outputST)


def test_InheritArgumentFromRecursiveTemplateApplication():
    """ do not inherit attributes through formal args """
    templates = """
            group test;
            "block(stats) ::= \"<stats>\"" +
            ifstat(stats) ::= \"IF true then <stats>\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("block")
    b["stats"] = group.getInstanceOf("ifstat")
    b["stats"] = group.getInstanceOf("ifstat")
    expecting = "IF True then IF True then "
    result = str(b)
    logger.info("result='{}", result)
    assert expecting == result


def test_DeliberateRecursiveTemplateApplication():
    """ This test will cause infinite loop.  
    block contains a stat which contains the same block.
    Must be in lintMode to detect 
    note that attributes doesn't show up in ifstat() because
    recursion detection traps the problem before it writes out the
    infinitely-recursive template; I set the attributes attribute right
    before I render. 
    """
    templates = """
            group test;
            "block(stats) ::= \"<stats>\"" +
            ifstat(stats) ::= \"IF True then <stats>\"
            """
    st3t.setLintMode(True)
    st3t.resetTemplateCounter()
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("block")
    ifstat = group.getInstanceOf("ifstat")
    b["stats"] = ifstat  # block has if stat
    ifstat["stats"] = b  # but make "if" contain block
    expectingError = """
            infinite recursion to <ifstat([stats])@4> referenced in <block([stats])@3>; stack trace:+
            <ifstat([stats])@4>, attributes=[stats=<block()@3>]>+
            <block([stats])@3>, attributes=[stats=<ifstat()@4>], references=[stats]>+
            <ifstat([stats])@4> (start of recursive cycle)+
            "..."
            """
    errors = ""
    try:
        result = str(b)
        logger.debug(f"result: {result}")

    except IllegalStateException as ise:
        errors = ise.getMessage()

    logger.info("errors=" + errors + "'")
    logger.info("expecting = " + expectingError + "'")
    st3t.setLintMode(False)
    assert expectingError == errors


def test_ImmediateTemplateAsAttributeLoop():
    """ even though block has a stats value that refers to itself, """
    """ there is no recursion because each instance of block hides """
    """ the stats value from above since it's a formal arg. """
    templates = """
            group test;
            "block(stats) ::= \"{<stats>}\""
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("block")
    b["stats"] = group.getInstanceOf("block")
    expecting = "{{}}"
    result = str(b)
    logger.error(result)
    assert expecting == result


def test_TemplateAlias():
    templates = """
            group test;
            "page(name) ::= \"name is <name>\"" +
            other ::= page
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("other")
    b["name"] = "Ter"
    expecting = "name is Ter"
    result = str(b)
    assert expecting == result


def test_TemplateGetPropertyGetsAttribute():
    """ This test will cause infinite loop if missing attribute no """
    """ properly caught in getAttribute """
    templates = """
            group test;
            Cfile(funcs) ::= << +
            #include \\<stdio.h>
            <funcs:{public void <it.name>(<it.args>);}; separator=\"\\n\">
            <funcs; separator=\"\\n\">
            >> +
            func(name,args,body) ::= <<
            public void <name>(<args>) {<body>} +
            >>
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("Cfile")
    f1 = group.getInstanceOf("func")
    f2 = group.getInstanceOf("func")
    f1["name"] = "f"
    f1["args"] = ""
    f1["body"] = "i=1;"
    f2["name"] = "g"
    f2.setAttribute("args", "int arg")
    f2["body"] = "y=1;"
    b["funcs"] = f1
    b["funcs"] = f2
    expecting = """
    #include <stdio.h>
    public void f();
    public void g(int arg);
    public void f() {i=1;}
    "public void g(int arg) {y=1;}"
    """
    assert expecting == str(b)


class Decl:
    def __init__(self, name, atype):
        self.name = name
        self.type = atype

    def getName(self):
        return self.name

    def getType(self):
        return self.type


def test_ComplicatedIndirectTemplateApplication():
    templates = """
            group Java; +
             +
            "file(variables) ::= <<" +
            <variables:{ v | <v.decl:(v.format)()>}; separator=\"\\n\"> +
            >>
            intdecl(decl) ::= \"int <decl.name> = 0;\" +
            intarray(decl) ::= \"int[] <decl.name> = None;\"
            """
    group = st3g(io.StringIO(templates))
    f = group.getInstanceOf("file")
    f.setAttribute("variables.{decl,format}", Decl("i", "int"), "intdecl")
    f.setAttribute("variables.{decl,format}", Decl("a", "int-array"), "intarray")
    logger.info("f='" + f + "'")
    expecting = """
    int i = 0;
    "int[] a = None;"
    """
    assert expecting == str(f)


def test_IndirectTemplateApplication():
    templates = """
            group dork; +
             +
            "test(name) ::= <<" +
            <(name)()> +
            >>
            first() ::= \"the first\" +
            second() ::= \"the second\"
            """
    group = st3g(io.StringIO(templates))
    f = group.getInstanceOf("test")
    f["name"] = "first"
    expecting = "the first"
    assert expecting == str(f)


def test_IndirectTemplateWithArgsApplication():
    templates = """
            group dork; +
             +
            "test(name) ::= <<" +
            <(name)(a=\"foo\")> +
            >>
            first(a) ::= \"the first: <a>\" +
            second(a) ::= \"the second <a>\"
            """
    group = st3g(io.StringIO(templates))
    f = group.getInstanceOf("test")
    f["name"] = "first"
    expecting = "the first: foo"
    assert str(f) == expecting


def test_NullIndirectTemplateApplication():
    templates = """
            group dork; +
             +
            "test(names,t) ::= <<" +
            <names:(t)()> + // t None be must be defined else error: None attr w/o formal def
            >>
            ind() ::= \"[<it>]\";
            """
    group = st3g(io.StringIO(templates))
    f = group.getInstanceOf("test")
    f["names"] = "me"
    f["names"] = "you"
    expecting = ""
    assert expecting == str(f)


def test_NullIndirectTemplate():
    templates = """
            group dork; +
             +
            "test(name) ::= <<" +
            <(name)()> +
            >>
            first() ::= \"the first\" +
            second() ::= \"the second\"
            """
    group = st3g(io.StringIO(templates))
    f = group.getInstanceOf("test")
    # f["name"] = "first"
    expecting = ""
    assert expecting == str(f)


def test_HashMapPropertyFetch():
    a = st3t("$stuff.prop$")
    amap = {"prop": "Terence"}
    a["stuff"] = amap
    results = str(a)
    logger.info(results)
    expecting = "Terence"
    assert expecting == results


def test_HashMapPropertyFetchEmbeddedStringTemplate():
    a = st3t("$stuff.prop$")
    amap = {"prop": st3t("embedded refers to $title$")}
    a["stuff"] = amap
    a.setAttribute("title", "ST rocks")

    results = str(a)
    logger.info(results)
    expecting = "embedded refers to ST rocks"
    assert expecting == results


def test_EmbeddedComments():
    st = st3t("""
            Foo $! ignore !$bar
            """)
    expecting = "Foo bar"
    result = str(st)
    assert expecting == result

    st = st3t("""
            Foo $! ignore
             and a line break!$
            bar
            """)
    expecting = "Foo bar"
    result = str(st)
    assert expecting == result

    st = st3t("""
            $! start of line $ and $! ick
            !$boo
            """)
    expecting = "boo"
    result = str(st)
    assert expecting == result

    st = st3t("""
        $! start of line !$
        $! another to ignore !$
        $! ick
        !$boo
    """)
    expecting = "boo"
    result = str(st)
    assert expecting == result

    st = st3t("""
        $! back !$$! to back !$ // can't detect; leaves \n
        $! ick
        !$boo
    """)
    expecting = ("""
        boo
    """)
    result = str(st)
    assert expecting == result


def test_EmbeddedCommentsAngleBracketed():
    st = st3t("""
            Foo <! ignore !>bar,
            AngleBracketTemplateLexer.Lexer
            """)
    expecting = "Foo bar"
    result = str(st)
    assert expecting == result

    st = st3t("""
            Foo <! ignore
             and a line break!>
            bar""",
              AngleBracketTemplateLexer.Lexer
              )
    expecting = "Foo bar"
    result = str(st)
    assert expecting == result

    st = st3t("""
            <! start of line $ and <! ick
            !>boo""",
              AngleBracketTemplateLexer.Lexer
              )
    expecting = "boo"
    result = str(st)
    assert expecting == result

    st = st3t("""
        "<! start of line !>" +
        "<! another to ignore !>" +
        <! ick
        !>boo""",
              AngleBracketTemplateLexer.Lexer
              )
    expecting = "boo"
    result = str(st)
    logger.info(result)
    assert expecting == result

    st = st3t("""
        <! back !><! to back !> // can't detect; leaves \n
        <! ick
        !>boo""",
              AngleBracketTemplateLexer.Lexer
              )
    expecting = """ 
        boo"""
    result = str(st)
    assert expecting == result


def test_LineBreak():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = st3t("""
            Foo <\\\\>
              \t  bar""",
              AngleBracketTemplateLexer.Lexer
              )
    # sw = StringWriter()
    # st.write(AutoIndentWriter(sw,))
    # result =  str(sw)
    expecting = "Foo bar"
    # assert expecting ==  result


def test_LineBreak2():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = st3t("""
            Foo <\\\\>       
              \t  bar""",
              AngleBracketTemplateLexer.Lexer
              )
    # StringWriter sw = new StringWriter();
    # st.write(new AutoIndentWriter(sw,))   # force \n as newline
    # result =  str(sw);
    expecting = "Foo bar"
    # assert expecting ==  result


def test_LineBreakNoWhiteSpace():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = st3t("""
            Foo <\\\\>
            bar""",
              AngleBracketTemplateLexer.Lexer
              )
    # StringWriter sw = new StringWriter();
    # st.write(new AutoIndentWriter(sw,))   # force \n as newline
    # result =  str(sw);
    expecting = "Foo bar"
    # assert expecting ==  result


def test_LineBreakDollar():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = st3t("""
            Foo $\\\\$
              \t  bar""",
              DefaultTemplateLexer.Lexer
              )
    # StringWriter sw = new StringWriter();
    # st.write(new AutoIndentWriter(sw,))   # force \n as newline
    # result =  str(sw);
    expecting = "Foo bar"
    # assert expecting ==  result


def test_LineBreakDollar2():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = st3t("""
            Foo $\\\\$          
              \t  bar""",
              DefaultTemplateLexer.Lexer
              )
    # StringWriter sw = new StringWriter();
    # st.write(new AutoIndentWriter(sw,))   # force \n as newline
    # result =  str(sw);
    expecting = "Foo bar"
    # assert expecting ==  result


def test_LineBreakNoWhiteSpaceDollar():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = st3t("""
            Foo $\\\\$
            bar""",
              DefaultTemplateLexer.Lexer
              )
    # StringWriter sw = new StringWriter();
    # st.write(new AutoIndentWriter(sw,))   # force \n as newline
    # result =  str(sw);
    expecting = "Foo bar"
    # assert expecting ==  result


def test_CharLiterals():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = st3t("""
            Foo <\\r\\n><\\n><\\t> bar""",
              AngleBracketTemplateLexer.Lexer
              )
    # StringWriter sw = new StringWriter();
    # st.write(new AutoIndentWriter(sw,))   # force \n as newline
    # result =  str(sw);
    expecting = "Foo \n\n\t bar"
    # assert expecting ==  result

    st = st3t("""
            Foo $\\n$$\\t$ bar""")
    # sw = new StringWriter();
    # st.write(new AutoIndentWriter(sw,))   # force \n as newline
    expecting = "Foo \n\t bar"
    # result = str(sw)
    # assert expecting ==  result

    st = st3t("Foo$\\ $bar$\\n$")
    # sw = new StringWriter();
    # st.write(new AutoIndentWriter(sw,))   # force \n as newline
    # result = str(sw);
    # expecting ="Foo bar"
    # assert expecting ==  result


def test_NewlineNormalizationInTemplateString():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = st3t("""
            Foo\r+
            Bar""",
              AngleBracketTemplateLexer.Lexer
              )
    # StringWriter sw = new StringWriter()
    # st.write(new AutoIndentWriter(sw,))
    # result =  str(sw)
    # expecting = "Foo\nBar"
    # assert expecting ==  result


def test_NewlineNormalizationInTemplateStringPC():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = st3t("""
            Foo\r+
            Bar""",
              AngleBracketTemplateLexer.Lexer
              )
    # StringWriter sw = new StringWriter();
    # st.write(new AutoIndentWriter(sw,\r))   # force \r\n as newline
    # result =  str(sw);
    # expecting = Foo\r\nBar\r     // expect \r\n in output
    # assert expecting ==  result


def test_NewlineNormalizationInAttribute():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = st3t("""
            Foo\r+
            <name>""",
              AngleBracketTemplateLexer.Lexer
              )
    st["name"] = "a\nb\r\nc"
    # StringWriter sw = new StringWriter();
    # st.write(new AutoIndentWriter(sw,))
    # result =  str(sw)
    # expecting = "Foo\na\nb\nc"
    # assert expecting ==  result


def test_UnicodeLiterals():
    st = st3t("""Foo <\\uFEA5\\n\\u00C2> bar""", AngleBracketTemplateLexer.Lexer)
    expecting = "Foo \ufea5\u00C2 bar"
    result = str(st)
    assert expecting == result

    st = st3t("""Foo $\\uFEA5\\n\\u00C2$ bar""")
    expecting = "Foo \ufea5\u00C2 bar"
    result = str(st)
    assert expecting == result

    st = st3t("Foo$\\ $bar$\\n$")
    expecting = "Foo bar"
    result = str(st)
    assert expecting == result


def test_EmptyIteratedValueGetsSeparator():
    """ empty values get separator still """
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, "$names; separator=\",\"$")
    t["names"] = "Terence"
    t["names"] = ""
    t["names"] = ""
    t["names"] = "Tom"
    t["names"] = "Frank"
    t["names"] = ""
    expecting = "Terence,,,Tom,Frank,"
    result = str(t)
    assert expecting == result


def test_MissingIteratedConditionalValueGetsNOSeparator():
    """ empty conditional values get no separator """
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, "$users:{$if(it.ok)$$it.name$$endif$}; separator=\",\"$")
    t.setAttribute("users.{name,ok}", "Terence", True)
    t.setAttribute("users.{name,ok}", "Tom", False)
    t.setAttribute("users.{name,ok}", "Frank", True)
    t.setAttribute("users.{name,ok}", "Johnny", False)
    expecting = "Terence,Frank"
    result = str(t)
    assert expecting == result


def test_MissingIteratedConditionalValueGetsNOSeparator2():
    """ empty conditional values get no separator """
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, "$users:{$if(it.ok)$$it.name$$endif$}; separator=\",\"$")
    t.setAttribute("users.{name,ok}", "Terence", True)
    t.setAttribute("users.{name,ok}", "Tom", False)
    t.setAttribute("users.{name,ok}", "Frank", False)
    t.setAttribute("users.{name,ok}", "Johnny", False)
    expecting = "Terence"
    result = str(t)
    assert expecting == result


def test_MissingIteratedDoubleConditionalValueGetsNOSeparator():
    """ empty conditional values get no separator """
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group,
             "$users:{$if(it.ok)$$it.name$$endif$$if(it.ok)$$it.name$$endif$}; separator=\",\"$")
    t.setAttribute("users.{name,ok}", "Terence", False)
    t.setAttribute("users.{name,ok}", "Tom", True)
    t.setAttribute("users.{name,ok}", "Frank", True)
    t.setAttribute("users.{name,ok}", "Johnny", True)
    expecting = "TomTom,FrankFrank,JohnnyJohnny"
    result = str(t)
    assert expecting == result


def test_IteratedConditionalWithEmptyElseValueGetsSeparator():
    """ empty conditional values get no separator """
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group,
             "$users:{$if(it.ok)$$it.name$$else$$endif$}; separator=\",\"$")
    t.setAttribute("users.{name,ok}", "Terence", True)
    t.setAttribute("users.{name,ok}", "Tom", False)
    t.setAttribute("users.{name,ok}", "Frank", True)
    t.setAttribute("users.{name,ok}", "Johnny", False)
    expecting = "Terence,,Frank,"
    result = str(t)
    assert expecting == result


def test_WhiteSpaceAtEndOfTemplate():
    """ users.list references row.st which has a single blank line at the end. 
    I.e., there are 2 \n in a row at the end 
    ST should eat all whitespace at end """
    group = st3g("group")
    pageST = group.getInstanceOf("org/antlr/stringtemplate/test/page")
    listST = group.getInstanceOf("org/antlr/stringtemplate/test/users_list")
    listST.setAttribute("users", Connector())
    listST.setAttribute("users", Connector2())
    pageST.setAttribute("title", "some title")
    pageST["body"] = listST
    expecting = """some title
        "Terence parrt@jguru.comTom tombu@jguru.com"
        """
    result = str(pageST)
    logger.info("'" + result + "'")
    assert expecting == result


class Duh:
    def users(self):
        return []


def test_SizeZeroButNonNullListGetsNoOutput():
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, """
        begin
        $duh.users:{name: $it$}; separator=\", \"$
        end""")
    t.setAttribute("duh", Duh())
    expecting = "beginend"
    result = str(t)
    assert expecting == result


def test_NullListGetsNoOutput():
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, """
        begin
        $users:{name: $it$}; separator=\", \"$
        end""")
    # t.setAttribute("users", Duh())
    expecting = "beginend"
    result = str(t)
    assert expecting == result


def test_EmptyListGetsNoOutput():
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, """
        begin
        $users:{name: $it$}; separator=\", \"$
        end""")
    t.setAttribute("users", list())
    expecting = "beginend"
    result = str(t)
    assert expecting == result


def test_EmptyListNoIteratorGetsNoOutput():
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, """
        begin
        $users; separator=\", \"$
        end""")
    t.setAttribute("users", list())
    expecting = "beginend"
    result = str(t)
    assert expecting == result


def test_EmptyExprAsFirstLineGetsNoOutput():
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    group.defineTemplate("bold", "<b>$it$</b>")
    t = st3t(group, """
        $users$
        end""")
    expecting = "end"
    result = str(t)
    assert expecting == result


def test_SizeZeroOnLineByItselfGetsNoOutput():
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, """
        begin+
        $name$+
        $users:{name: $it$}$+
        $users:{name: $it$}; separator=\", \"$+
        end""")
    expecting = "beginend"
    result = str(t)
    assert expecting == result


def test_SizeZeroOnLineWithIndentGetsNoOutput():
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, """
        begin+
          $name$+
            $users:{name: $it$}$+
            $users:{name: $it$$\\n$}$+
        end""")
    expecting = "beginend"
    result = str(t)
    assert expecting == result


def test_SimpleAutoIndent():
    a = st3t("""
        $title$: {
            $name; separator=\"\n\"$
        }
        """)
    a["title"] = "foo"
    a["name"] = "Terence"
    a["name"] = "Frank"
    results = str(a)
    logger.info(results)
    expecting = """
        foo: {
            Terence
            Frank
        }
        """
    assert results == expecting


def test_ComputedPropertyName():
    group = st3g("test")
    errors = st3err.DEFAULT_ERROR_LISTENER
    group.setErrorListener(errors)
    t = st3t(group, "variable property $propName$=$v.(propName)$")
    t.setAttribute("v", Decl("i", "int"))
    t["propName"] = "type"
    expecting = "variable property type=int"
    result = str(t)
    assert "" == str(errors)
    assert expecting == result


def test_NonNullButEmptyIteratorTestsFalse():
    group = st3g("test")
    t = st3t(group, """
        $if(users)$
        Users: $users:{$it.name$ }$"""
                    "$endif$")
    t.setAttribute("users", list())
    expecting = ""
    result = str(t)
    assert expecting == result


def test_DoNotInheritAttributesThroughFormalArgs():
    """ name is not visible in stat because of the formal arg called name. 
    somehow, it must be set. """
    templates = """
            group test;
            method(name) ::= \"<stat()>\"
            stat(name) ::= \"x=y   # <name>\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    expecting = "x=y   # "
    result = str(b)
    logger.info("result='" + result + "'")
    assert expecting == result


def test_ArgEvaluationContext():
    """ attribute name is not visible in stat because of the formal 
    arg called name in template stat.  However, we can set its value
    with an explicit name=name.  This looks weird, but makes total
    sense as the rhs is evaluated in the context of method and the lhs
    is evaluated in the context of stat's arg list. """
    templates = """
            group test;
            method(name) ::= \"<stat(name=name)>\"
            stat(name) ::= \"x=y   # <name>\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    expecting = "x=y   # foo"
    result = str(b)
    logger.info("result='" + result + "'")
    assert expecting == result


def test_PassThroughAttributes():
    templates = """
            group test;
            method(name) ::= \"<stat(...)>\"
            stat(name) ::= \"x=y   # <name>\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    expecting = "x=y   # foo"
    result = str(b)
    logger.info("result='" + result + "'")
    assert expecting == result


def test_PassThroughAttributes2():
    templates = """
            group test;
            method(name) ::= <<
            <stat(value=\"34\",...)>
            >>
            stat(name,value) ::= \"x=<value>   # <name>\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    expecting = "x=34   # foo"
    result = str(b)
    logger.info("result='" + result + "'")
    assert expecting == result


def test_DefaultArgument():
    templates = """
            group test;
            method(name) ::= <<
            <stat(...)>
            >>
            stat(name,value=\"99\") ::= \"x=<value>   # <name>\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    expecting = "x=99   # foo"
    result = str(b)
    logger.info("result='" + result + "'")
    assert expecting == result


def test_DefaultArgument2():
    templates = """
            group test;
            stat(name,value=\"99\") ::= \"x=<value>   # <name>\"
    """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("stat")
    b["name"] = "foo"
    expecting = "x=99   # foo"
    result = str(b)
    logger.info("result='" + result + "'")
    assert expecting == result


class Field:
    def __init__(self):
        self.name = "parrt"
        self.n = 0

    def str(self):
        return "Field"


def test_DefaultArgumentManuallySet():
    templates = """
            group test;
            method(fields) ::= <<
            <fields:{f | <stat(f=f)>}>
            >>
            stat(f,value={<f.name>}) ::= \"x=<value>   # <f.name>\"
            """
    group = st3g(io.StringIO(templates))
    m = group.getInstanceOf("method")
    m.setAttribute("fields", Field())
    expecting = "x=parrt   # parrt"
    result = str(m)
    assert expecting == result


def test_DefaultArgumentImplicitlySet():
    """ This fails because checkNullAttributeAgainstFormalArguments looks
     *  for a formal argument at the current level not of the original embedded
     *  template. We have defined it all the way in the embedded, but there is
     *  no value, so we try to look upwards ala dynamic scoping. When it reaches
     *  the top, it doesn't find a value, but it will miss the
     *  formal argument down in the embedded.
     *
     *  By definition, though, the formal parameter exists if we have
     *  a default value. look up the value to see if it's None without
     *  checking checkNullAttributeAgainstFormalArguments.
     """
    templates = """
            group test;
            method(fields) ::= <<
            <fields:{f | <stat(...)>}>
            >>
            stat(f,value={<f.name>}) ::= \"x=<value>   # <f.name>\"
            """
    group = st3g(io.StringIO(templates))
    m = group.getInstanceOf("method")
    m.setAttribute("fields", Field())
    expecting = "x=parrt   # parrt"
    result = str(m)
    assert expecting == result


def test_DefaultArgumentImplicitlySet2():
    templates = """
            group test;
            method(fields) ::= <<
            <fields:{f | <f:stat()>}>  // THIS SHOULD BE ERROR; >1 arg?
            >>
            stat(f,value={<f.name>}) ::= \"x=<value>   # <f.name>\"
            """
    group = st3g(io.StringIO(templates))
    m = group.getInstanceOf("method")
    m.setAttribute("fields", Field())
    expecting = "x=parrt   # parrt"
    result = str(m)
    assert expecting == result


def test_DefaultArgumentAsTemplate():
    templates = """
            group test;
            method(name,size) ::= <<
            <stat(...)>
            >>
            stat(name,value={<name>}) ::= \"x=<value>   # <name>\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    b["size"] = "2"
    expecting = "x=foo   # foo"
    result = str(b)
    logger.debug("result='" + result + "'")
    assert expecting == result


def test_DefaultArgumentAsTemplate2():
    templates = """
            group test;
            method(name,size) ::= <<
            <stat(...)>
            >>
            stat(name,value={ [<name>] }) ::= \"x=<value>   # <name>\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    b["size"] = "2"
    expecting = "x= [foo]    # foo"
    result = str(b)
    logger.debug("result='" + result + "'")
    assert expecting == result


def test_DoNotUseDefaultArgument():
    templates = """
            group test;
            method(name) ::= <<
            <stat(value=\"34\",...)>
            >>
            stat(name,value=\"99\") ::= \"x=<value>   # <name>\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    expecting = "x=34   # foo"
    result = str(b)
    assert expecting == result


class Counter:
    def __init__(self):
        self.n = 0

    def str(self):
        self.n += 1
        return f"{self.n}"


def test_DefaultArgumentInParensToEvalEarly():
    templates = """
            group test;
            A(x) ::= \"<B()>\"
            B(y={<(x)>}) ::= \"<y> <x> <x> <y>\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("A")
    b.setAttribute("x", Counter())
    expecting = "0 1 2 0"
    result = str(b)
    logger.debug("result='" + result + "'")
    assert expecting == result


def test_ArgumentsAsTemplates():
    templates = """
            group test;
            method(name,size) ::= <<
            <stat(value={<size>})>
            >>
            stat(value) ::= \"x=<value>;\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    b["size"] = "34"
    expecting = "x=34;"
    result = str(b)
    assert expecting == result


def test_TemplateArgumentEvaluatedInSurroundingContext():
    templates = """
            group test;
            file(m,size) ::= \"<m>\"
            method(name) ::= <<
            <stat(value={<size>.0})>
            >>
            stat(value) ::= \"x=<value>;\"
            """
    group = st3g(io.StringIO(templates))
    f = group.getInstanceOf("file")
    f["size"] = "34"
    m = group.getInstanceOf("method")
    m["name"] = "foo"
    f["m"] = m
    expecting = "x=34.0;"
    result = str(m)
    assert expecting == result


def test_ArgumentsAsTemplatesDefaultDelimiters():
    templates = """
            group test;
            method(name,size) ::= <<
            $stat(value={$size$})$
            >>
            stat(value) ::= \"x=$value$;\"
            """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer)
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    b["size"] = "34"
    expecting = "x=34;"
    result = str(b)
    assert expecting == result


def test_DefaultArgsWhenNotInvoked():
    templates = """
            group test;
            b(name=\"foo\") ::= \".<name>.\"
            """
    group = st3g(io.StringIO(templates))
    b = group.getInstanceOf("b")
    expecting = ".foo."
    result = str(b)
    assert expecting == result


class DateRenderer(AttributeRenderer):
    def __init__(self):
        AttributeRenderer.__init__(self)

    def str(self, obj):
        return obj.strftime("%Y.%M.%D")

    def str(self, obj, format_string):
        return obj.strftime(format_string)


class DateRenderer2(AttributeRenderer):
    def __init__(self):
        AttributeRenderer.__init__(self)

    def str(self, obj):
        return obj.strftime("%M/%D/%Y")

    def str(self, obj, format_string):
        return obj.strftime(format_string)


class DateRenderer3(AttributeRenderer):
    def __init__(self):
        AttributeRenderer.__init__(self)

    def str(self, obj):
        return obj.strftime("%M/%D/%Y")

    def str(self, obj, format_string):
        return str(obj)


class StringRenderer(AttributeRenderer):
    def __init__(self):
        AttributeRenderer.__init__(self)

    def str(self, obj):
        return str(obj)

    def str(self, obj, format_string):
        if format_string == "upper":
            return str(obj).upper()
        return str(obj)


def test_RendererForST():
    st = st3t(
        "date: <created>",
        AngleBracketTemplateLexer.Lexer)
    st.setAttribute("created", sample_day)
    st.registerRenderer(calendar, DateRenderer())
    expecting = "date: 2005.07.05"
    result = str(st)
    assert expecting == result


def test_RendererWithFormat():
    st = st3t(
        "date: <created; format=\"yyyy.MM.dd\">",
        AngleBracketTemplateLexer.Lexer)
    st.setAttribute("created", sample_day)
    st.registerRenderer(calendar, DateRenderer3())
    expecting = "date: 2005.07.05"
    result = str(st)
    assert expecting == result


def test_RendererWithFormatAndList():
    st = st3t(
        "The names: <names; format=\"upper\">",
        AngleBracketTemplateLexer.Lexer)
    st["names"] = "ter"
    st["names"] = "tom"
    st["names"] = "sriram"
    st.registerRenderer(str, StringRenderer())
    expecting = "The names: TERTOMSRIRAM"
    result = str(st)
    assert expecting == result


def test_RendererWithFormatAndSeparator():
    st = st3t(
        "The names: <names; separator=\" and \", format=\"upper\">",
        AngleBracketTemplateLexer.Lexer)
    st["names"] = "ter"
    st["names"] = "tom"
    st["names"] = "sriram"
    st.registerRenderer(str, StringRenderer())
    expecting = "The names: TER and TOM and SRIRAM"
    result = str(st)
    assert expecting == result


def test_RendererWithFormatAndSeparatorAndNull():
    st = st3t(
        "The names: <names; separator=\" and \", None=\"n/a\", format=\"upper\">",
        AngleBracketTemplateLexer.Lexer)
    names = ["ter", None, "sriram"]
    st["names"] = names
    st.registerRenderer(str, StringRenderer())
    expecting = "The names: TER and N/A and SRIRAM"
    result = str(st)
    assert expecting == result


def test_EmbeddedRendererSeesEnclosing():
    """ st is embedded in outer; set renderer on outer, st should still see it. """
    outer = st3t("X: <x>",
                 AngleBracketTemplateLexer.Lexer)
    st = st3t("date: <created>",
              AngleBracketTemplateLexer.Lexer)
    st.setAttribute("created", sample_day)
    outer["x"] = st
    outer.registerRenderer(calendar, DateRenderer())
    expecting = "X: date: 2005.07.05"
    result = str(outer)
    assert expecting == result


def test_RendererForGroup():
    templates = """
            group test;
            dateThing(created) ::= \"date: <created>\"
            """
    group = st3g(io.StringIO(templates))
    st = group.getInstanceOf("dateThing")
    st.setAttribute("created", sample_day)
    group.registerRenderer(calendar, DateRenderer())
    expecting = "date: 2005.07.05"
    result = str(st)
    assert expecting == result


def test_OverriddenRenderer():
    templates = """
            group test;
            dateThing(created) ::= \"date: <created>\"
            """
    group = st3g(io.StringIO(templates))
    st = group.getInstanceOf("dateThing")
    st.setAttribute("created", sample_day)
    group.registerRenderer(calendar, DateRenderer())
    st.registerRenderer(calendar, DateRenderer2())
    expecting = "date: 07/05/2005"
    result = str(st)
    assert expecting == result


def test_Map():
    template = """
            group test;
            typeInit ::= [\"int\":\"0\", \"float\":\"0.0\"]
            var(type,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "int"
    st["name"] = "x"
    expecting = "int x = 0;"
    result = str(st)
    assert expecting == result


def test_MapValuesAreTemplates():
    template = """
            group test;
            typeInit ::= [\"int\":\"0<w>\", \"float\":\"0.0<w>\"]
            var(type,w,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(template))
    st = group.getInstanceOf("var")
    st["w"] = "L"
    st["type"] = "int"
    st["name"] = "x"
    expecting = "int x = 0L;"
    result = str(st)
    assert expecting == result


def test_MapKeyLookupViaTemplate():
    """ ST doesn't do a toString on .(key) values, it just uses the value 
    of key rather than key itself as the key.  But, if you compute a 
    key via a template """
    template = """
            group test;
            typeInit ::= [\"int\":\"0<w>\", \"float\":\"0.0<w>\"]
            var(type,w,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(template))
    st = group.getInstanceOf("var")
    st["w"] = "L"
    st["type"] = st3t("int")
    st["name"] = "x"
    expecting = "int x = 0L;"
    result = str(st)
    assert expecting == result


def test_MapMissingDefaultValueIsEmpty():
    template = """
            group test;
            typeInit ::= [\"int\":\"0\", \"float\":\"0.0\"]
            var(type,w,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(template))
    st = group.getInstanceOf("var")
    st["w"] = "L"
    st["type"] = "double"  # double not in typeInit map
    st["name"] = "x"
    expecting = "double x = ;"  # weird, but tests default value is key
    result = str(st)
    assert expecting == result


def test_MapHiddenByFormalArg():
    template = """
            group test;
            typeInit ::= [\"int\":\"0\", \"float\":\"0.0\"]
            var(typeInit,type,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "int"
    st["name"] = "x"
    expecting = "int x = ;"
    result = str(st)
    assert expecting == result


def test_MapEmptyValueAndAngleBracketStrings():
    template = """
            group test;
            typeInit ::= [\"int\":\"0\", \"float\":, \"double\":<<0.0L>>]
            var(type,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "float"
    st["name"] = "x"
    expecting = "float x = ;"
    result = str(st)
    assert expecting == result


def test_MapDefaultValue():
    template = """
            group test;
            typeInit ::= [\"int\":\"0\", default:\"None\"]
            var(type,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "UserRecord"
    st["name"] = "x"
    expecting = "UserRecord x = None;"
    result = str(st)
    assert expecting == result


def test_MapEmptyDefaultValue():
    template = """
            group test;
            typeInit ::= [\"int\":\"0\", default:]
            var(type,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "UserRecord"
    st["name"] = "x"
    expecting = "UserRecord x = ;"
    result = str(st)
    assert expecting == result


def test_MapDefaultValueIsKey():
    template = """
            group test;
            typeInit ::= [\"int\":\"0\", default:key]
            var(type,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "UserRecord"
    st["name"] = "x"
    expecting = "UserRecord x = UserRecord;"
    result = str(st)
    assert expecting == result


def test_MapDefaultStringAsKey():
    """ 
    Test that a map can have only the default entry.
     * <p>
     * Bug ref: JIRA bug ST-15 (Fixed)
    """
    templates = """
            group test;
            typeInit ::= [\"default\":\"foo\"] 
            var(type,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(templates))
    st = group.getInstanceOf("var")
    st["type"] = "default"
    st["name"] = "x"
    expecting = "default x = foo;"
    result = str(st)
    assert expecting == result


def test_MapDefaultIsDefaultString():
    """  Test that a map can return a <b>string</b> with the word: default.
     * <p>
     * Bug ref: JIRA bug ST-15 (Fixed)
     """
    templates = """
            group test;
            map ::= [default: \"default\"] 
            t1() ::= \"<map.(1)>\" 
            """
    group = st3g(io.StringIO(templates))
    st = group.getInstanceOf("t1")
    expecting = "default"
    result = str(st)
    assert expecting == result


def test_MapViaEnclosingTemplates():
    template = """
            group test;
            typeInit ::= [\"int\":\"0\", \"float\":\"0.0\"]
            intermediate(type,name) ::= \"<var(...)>\"
            var(type,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(template))
    st = group.getInstanceOf("intermediate")
    st["type"] = "int"
    st["name"] = "x"
    expecting = "int x = 0;"
    result = str(st)
    assert expecting == result


def test_MapViaEnclosingTemplates2():
    template = """
            group test;
            typeInit ::= [\"int\":\"0\", \"float\":\"0.0\"]
            intermediate(stuff) ::= \"<stuff>\"
            var(type,name) ::= \"<type> <name> = <typeInit.(type)>;\"
            """
    group = st3g(io.StringIO(template))
    intermediate = group.getInstanceOf("intermediate")
    var = group.getInstanceOf("var")
    var["type"] = "int"
    var["name"] = "x"
    intermediate["stuff"] = var
    expecting = "int x = 0;"
    result = str(intermediate)
    assert expecting == result


def test_EmptyGroupTemplate():
    template = """
            group test;
            foo() ::= \"\"
            """
    group = st3g(io.StringIO(template))
    a = group.getInstanceOf("foo")
    expecting = ""
    result = str(a)
    assert expecting == result


def test_EmptyStringAndEmptyAnonTemplateAsParameterUsingAngleBracketLexer():
    template = """
            group test;
            top() ::= <<<x(a=\"\", b={})\\>>>
            x(a,b) ::= \"a=<a>, b=<b>\";
            """
    group = st3g(io.StringIO(template))
    a = group.getInstanceOf("top")
    expecting = "a=, b="
    result = str(a)
    assert expecting == result


def test_EmptyStringAndEmptyAnonTemplateAsParameterUsingDollarLexer():
    template = """
            group test;
            top() ::= <<$x(a=\"\", b={})$>>
            x(a,b) ::= \"a=$a$, b=$b$\";
            """
    group = st3g(io.StringIO(template), DefaultTemplateLexer.Lexer)
    a = group.getInstanceOf("top")
    expecting = "a=, b="
    result = str(a)
    assert expecting == result


def test_8BitEuroChars():
    """ FIXME: Danish does not work if typed directly in with default file
     *  encoding on windows. The character needs to be escaped as bellow.
     *  Please correct to escape the correct character.
     """
    e = st3t("Danish: \u0143 char")
    e = e.getInstanceOf()
    expecting = "Danish: \u0143 char"
    assert expecting == str(e)


def test_16BitUnicodeChar():
    e = st3t("DINGBAT CIRCLED SANS-SERIF DIGIT ONE: \u2780")
    e = e.getInstanceOf()
    expecting = "DINGBAT CIRCLED SANS-SERIF DIGIT ONE: \u2780"
    assert expecting == str(e)


def test_FirstOp():
    e = st3t("$first(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    expecting = "Ter"
    assert expecting == str(e)


def test_TruncOp():
    e = st3t("$trunc(names); separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    expecting = "Ter, Tom"
    assert expecting == str(e)


def test_RestOp():
    e = st3t("$rest(names); separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    expecting = "Tom, Sriram"
    assert expecting == str(e)


def test_RestOpEmptyList():
    e = st3t("$rest(names); separator=\", \"$")
    e = e.getInstanceOf()
    e.setAttribute("names", list())
    expecting = ""
    assert expecting == str(e)


def test_ReUseOfRestResult():
    template = """
        group test;
        a(names) ::= \"<b(rest(names))>\"
        b(x) ::= \"<x>, <x>\"
        """
    group = st3g(io.StringIO(template))
    e = group.getInstanceOf("a")
    names = ["Ter", "Tom"]
    e["names"] = names
    expecting = "Tom, Tom"
    assert expecting == str(e)


def test_LastOp():
    e = st3t("$last(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    expecting = "Sriram"
    assert expecting == str(e)


def test_CombinedOp():
    """ replace first of yours with first of mine """
    e = st3t("$[first(mine),rest(yours)]; separator=\", \"$")
    e = e.getInstanceOf()
    e["mine"] = "1"
    e["mine"] = "2"
    e["mine"] = "3"
    e["yours"] = "a"
    e["yours"] = "b"
    expecting = "1, b"
    assert expecting == str(e)


def test_CatListAndSingleAttribute():
    """ replace first of yours with first of mine """
    e = st3t("$[mine,yours]; separator=\", \"$")
    e = e.getInstanceOf()
    e["mine"] = "1"
    e["mine"] = "2"
    e["mine"] = "3"
    e["yours"] = "a"
    expecting = "1, 2, 3, a"
    assert expecting == str(e)


def test_ReUseOfCat():
    template = """
        group test;
        a(mine,yours) ::= \"<b([mine,yours])>\"
        b(x) ::= \"<x>, <x>\"
        """
    group = st3g(io.StringIO(template))
    e = group.getInstanceOf("a")
    mine = ["Ter", "Tom"]
    e["mine"] = mine
    yours = ["Foo"]
    e["yours"] = yours
    expecting = "TerTomFoo, TerTomFoo"
    assert expecting == str(e)


def test_CatListAndEmptyAttributes():
    """ + is overloaded to be cat strings and cat lists so the """
    """ two operands (from left to right) determine which way it """
    """ goes.  In this case, x+mine is a list so everything from their """
    """ to the right becomes list cat. """
    e = st3t("$[x,mine,y,yours,z]; separator=\", \"$")
    e = e.getInstanceOf()
    e["mine"] = "1"
    e["mine"] = "2"
    e["mine"] = "3"
    e["yours"] = "a"
    expecting = "1, 2, 3, a"
    assert expecting == str(e)


def test_NestedOp():
    """ // gets 2nd element """
    e = st3t("$first(rest(names))$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    expecting = "Tom"
    assert expecting == str(e)


def test_FirstWithOneAttributeOp():
    e = st3t(
        "$first(names)$"
    )
    e = e.getInstanceOf()
    e["names"] = "Ter"
    expecting = "Ter"
    assert expecting == str(e)


def test_LastWithOneAttributeOp():
    e = st3t(
        "$last(names)$"
    )
    e = e.getInstanceOf()
    e["names"] = "Ter"
    expecting = "Ter"
    assert expecting == str(e)


def test_LastWithLengthOneListAttributeOp():
    e = st3t("$last(names)$")
    e = e.getInstanceOf()
    e.setAttribute("names", ["Ter"])
    expecting = "Ter"
    assert expecting == str(e)


def test_RestWithOneAttributeOp():
    e = st3t("$rest(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    expecting = ""
    assert expecting == str(e)


def test_RestWithLengthOneListAttributeOp():
    e = st3t("$rest(names)$")
    e = e.getInstanceOf()
    e.setAttribute("names", ["Ter"])
    expecting = ""
    assert expecting == str(e)


def test_RepeatedRestOp():
    """  // gets 2nd element """
    e = st3t("$rest(names)$, $rest(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    expecting = "Tom, Tom"
    assert expecting == str(e)


def test_RepeatedIteratedAttrFromArg():
    """If an iterator is sent into ST, it must be cannot be reset after each
     *  use so repeated refs yield empty values.  This would
     *  work if we passed in a List not an iterator.  Avoid sending in iterators
     *  if you ref it twice.
      // This does not give TerTom twice!!
      """
    template = """
            group test;
            root(names) ::= \"$other(names)$\"
            other(x) ::= \"$x$, $x$\"
            """
    group = st3g(io.StringIO(template), DefaultTemplateLexer.Lexer)
    e = group.getInstanceOf("root")
    names = ["Ter", "Tom"]
    e["names"] = names
    expecting = "TerTom, "
    assert expecting == str(e)


def test_RepeatedRestOpAsArg():
    """ FIXME: BUG! Iterator is not reset from first to second $x$
     *  Either reset the iterator or pass an attribute that knows to get
     *  the iterator each time.  Seems like first, tail do not
     *  have same problem as they yield objects.
     *
     *  Maybe make a RestIterator like I have CatIterator."""
    template = """
            group test;
            root(names) ::= \"$other(rest(names))$\"
            other(x) ::= \"$x$, $x$\"
            """
    group = st3g(io.StringIO(template), DefaultTemplateLexer.Lexer)
    e = group.getInstanceOf("root")
    e["names"] = "Ter"
    e["names"] = "Tom"
    expecting = "Tom, Tom"
    assert expecting == str(e)


def test_IncomingLists():
    e = st3t("$rest(names)$, $rest(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    expecting = "Tom, Tom"
    assert expecting == str(e)


def test_IncomingListsAreNotModified():
    e = st3t("$names; separator=\", \"$")
    e = e.getInstanceOf()
    names = ["Ter", "Tom"]
    e["names"] = names
    e["names"] = "Sriram"
    expecting = "Ter, Tom, Sriram"
    assert expecting == str(e)

    assert len(names) == 2


def test_IncomingListsAreNotModified2():
    e = st3t("$names; separator=\", \"$")
    e = e.getInstanceOf()
    names = ["Ter", "Tom"]
    e["names"] = "Sriram"  # single element first now
    e["names"] = names
    expecting = "Sriram, Ter, Tom"
    assert expecting == str(e)

    assert len(names) == 2


def test_IncomingArraysAreOk():
    e = st3t("$names; separator=\", \"$")
    e = e.getInstanceOf()
    e.setAttribute("names", ["Ter", "Tom"])
    e["names"] = "Sriram"
    expecting = "Ter, Tom, Sriram"
    assert expecting == str(e)


def test_MultipleRefsToListAttribute():
    template = """
            group test;
            f(x) ::= \"<x> <x>\"
            """
    group = st3g(io.StringIO(template))
    e = group.getInstanceOf("f")
    e["x"] = "Ter"
    e["x"] = "Tom"
    expecting = "TerTom TerTom"
    assert expecting == str(e)


def test_ApplyTemplateWithSingleFormalArgs():
    template = """
            group test;
            test(names) ::= <<<names:bold(item=it); separator=\", \"> >>
            bold(item) ::= <<*<item>*>>
            """
    group = st3g(io.StringIO(template))
    e = group.getInstanceOf("test")
    e["names"] = "Ter"
    e["names"] = "Tom"
    expecting = "*Ter*, *Tom* "
    result = str(e)
    assert expecting == result


def test_ApplyTemplateWithNoFormalArgs():
    template = """
            group test;
            test(names) ::= <<<names:bold(); separator=\", \"> >>
            bold() ::= <<*<it>*>>
            """
    group = st3g(io.StringIO(template), AngleBracketTemplateLexer.Lexer)
    e = group.getInstanceOf("test")
    e["names"] = "Ter"
    e["names"] = "Tom"
    expecting = "*Ter*, *Tom* "
    result = str(e)
    assert expecting == result


def test_AnonTemplateArgs():
    e = st3t("$names:{n| $n$}; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    expecting = "Ter, Tom"
    assert expecting == str(e)


def test_AnonTemplateWithArgHasNoITArg():
    e = st3t("$names:{n| $n$:$it$}; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    error = None
    try:
        str(e)

    except NoSuchElementException as nse:
        error = nse.getMessage()

    expecting = "no such attribute: it in template context [anonymous anonymous]"
    assert error == expecting


def test_AnonTemplateArgs2():
    e = st3t("$names:{n| .$n$.}:{ n | _$n$_}; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    expecting = "_.Ter._, _.Tom._"
    assert expecting == str(e)


def test_FirstWithCatAttribute():
    e = st3t("$first([names,phones])$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    expecting = "Ter"
    assert expecting == str(e)


def test_FirstWithListOfMaps():
    e = st3t("$first(maps).Ter$")
    e = e.getInstanceOf()
    m1 = dict()
    m2 = dict()
    m1["Ter"] = "x5707"
    e["maps"] = m1
    m2["Tom"] = "x5332"
    e["maps"] = m2
    expecting = "x5707"
    assert expecting == str(e)

    e = e.getInstanceOf()
    alist = [m1, m2]
    e["maps"] = alist
    expecting = "x5707"
    assert expecting == str(e)


def test_FirstWithListOfMaps2():
    """ this FAILS! """
    e = st3t("$first(maps):{ m | $m.Ter$ }$")
    m1 = {"Ter": "x5707"}
    m2 = {"Tom": "x5332"}

    e["maps"] = m1
    e["maps"] = m2
    expecting = "x5707"
    assert expecting == str(e)

    e = e.getInstanceOf()
    alist = [m1, m2]
    e["maps"] = alist
    expecting = "x5707"
    assert expecting == str(e)


def test_JustCat():
    e = st3t("$[names,phones]$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    expecting = "TerTom12"
    assert expecting == str(e)


def test_Cat2Attributes():
    e = st3t("$[names,phones]; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    expecting = "Ter, Tom, 1, 2"
    assert expecting == str(e)


def test_Cat2AttributesWithApply():
    e = st3t("$[names,phones]:{a|$a$.}$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    expecting = "Ter.Tom.1.2."
    assert expecting == str(e)


def test_Cat3Attributes():
    e = st3t("$[names,phones,salaries]; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    e["salaries"] = "big"
    e["salaries"] = "huge"
    expecting = "Ter, Tom, 1, 2, big, huge"
    assert expecting == str(e)


def test_CatWithTemplateApplicationAsElement():
    e = st3t("$[names:{$it$!},phones]; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e.setAttribute("phones", "1")
    e["phones"] = "2"
    expecting = "Ter!, Tom!, 1, 2"
    assert expecting == str(e)


def test_CatWithIFAsElement():
    e = st3t("$[{$if(names)$doh$endif$},phones]; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e.setAttribute("phones", "1")
    e["phones"] = "2"
    expecting = "doh, 1, 2"
    assert expecting == str(e)


def test_CatWithNullTemplateApplicationAsElement():
    e = st3t("$[names:{$it$!},\"foo\"]:{x}; separator=\", \"$")
    e = e.getInstanceOf()
    e["phones"] = "1"
    e["phones"] = "2"
    expecting = "x"  # only one since template application gives nothing
    assert expecting == str(e)


def test_CatWithNestedTemplateApplicationAsElement():
    e = st3t("$[names, [\"foo\",\"bar\"]:{$it$!},phones]; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    expecting = "Ter, Tom, foo!, bar!, 1, 2"
    assert expecting == str(e)


def test_ListAsTemplateArgument():
    template = """
                group test;
                test(names,phones) ::= \"<foo([names,phones])>\"
                foo(items) ::= \"<items:{a | *<a>*}>\"
                """
    group = st3g(io.StringIO(template), AngleBracketTemplateLexer.Lexer)
    e = group.getInstanceOf("test")
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    expecting = "*Ter**Tom**1**2*"
    result = str(e)
    assert expecting == result


def test_SingleExprTemplateArgument():
    template = """
            group test;
            test(name) ::= \"<bold(name)>\"
            bold(item) ::= \"*<item>*\"
            """
    group = st3g(io.StringIO(template), AngleBracketTemplateLexer.Lexer)
    e = group.getInstanceOf("test")
    e["name"] = "Ter"
    expecting = "*Ter*"
    result = str(e)
    assert expecting == result


def test_SingleExprTemplateArgumentInApply():
    """ when you specify a single arg on a template application
    it overrides the setting of the iterated value "it" to that
    same single formal arg.  Your arg hides the implicitly set "it". """
    template = """
            group test;
            test(names,x) ::= \"<names:bold(x)>\"
            bold(item) ::= \"*<item>*\"
            """
    group = st3g(io.StringIO(template), AngleBracketTemplateLexer.Lexer)
    e = group.getInstanceOf("test")
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["x"] = "ick"
    expecting = "*ick**ick*"
    result = str(e)
    assert expecting == result


def test_SoleFormalTemplateArgumentInMultiApply():
    template = """
            group test;
            test(names) ::= \"<names:bold(),italics()>\"
            bold(x) ::= \"*<x>*\"
            italics(y) ::= \"_<y>_\"
            """
    group = st3g(io.StringIO(template),
                 AngleBracketTemplateLexer.Lexer)
    e = group.getInstanceOf("test")
    e["names"] = "Ter"
    e["names"] = "Tom"
    expecting = "*Ter*_Tom_"
    result = str(e)
    assert expecting == result


def test_SingleExprTemplateArgumentError():
    template = """
            group test;
            test(name) ::= \"<bold(name)>\"
            bold(item,ick) ::= \"*<item>*\"
            """
    errors = st3err.DEFAULT_ERROR_LISTENER
    group = st3g(io.StringIO(template),
                 AngleBracketTemplateLexer.Lexer, errors=errors)
    e = group.getInstanceOf("test")
    e["name"] = "Ter"
    result = str(e)
    logger.debug(f'result: {result}')
    expecting = "template bold must have exactly one formal arg in template context [test <invoke bold arg context>]"
    assert str(errors) == expecting


def test_InvokeIndirectTemplateWithSingleFormalArgs():
    template = """
            group test;
            test(templateName,arg) ::= \"<(templateName)(arg)>\"
            bold(x) ::= <<*<x>*>>
            italics(y) ::= <<_<y>_>>
            """
    group = st3g(io.StringIO(template))
    e = group.getInstanceOf("test")
    e["templateName"] = "italics"
    e["arg"] = "Ter"
    expecting = "_Ter_"
    result = str(e)
    assert expecting == result


def test_ParallelAttributeIteration():
    e = st3t("$names,phones,salaries:{n,p,s | $n$@$p$: $s$\n}$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    e["salaries"] = "big"
    e["salaries"] = "huge"
    expecting = "Ter@1: bigTom@2: huge"
    assert expecting == str(e)


def test_ParallelAttributeIterationWithNullValue():
    e = st3t("$names,phones,salaries:{n,p,s | $n$@$p$: $s$\n}$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    e.setAttribute("phones", ["1", None, "3"])
    e["salaries"] = "big"
    e["salaries"] = "huge"
    e["salaries"] = "enormous"
    expecting = """Ter@1: big
                       Tom@: huge
                       Sriram@3: enormous"""
    assert expecting == str(e)


def test_ParallelAttributeIterationHasI():
    e = st3t("$names,phones,salaries:{n,p,s | $i0$. $n$@$p$: $s$\n}$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    e["salaries"] = "big"
    e["salaries"] = "huge"
    expecting = "0. Ter@1: big1. Tom@2: huge"
    assert expecting == str(e)


def test_ParallelAttributeIterationWithDifferentSizes():
    e = st3t(
        "$names,phones,salaries:{n,p,s | $n$@$p$: $s$}; separator=\", \"$"
    )
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    e["phones"] = "1"
    e["phones"] = "2"
    e["salaries"] = "big"
    expecting = "Ter@1: big, Tom@2: , Sriram@: "
    assert expecting == str(e)


def test_ParallelAttributeIterationWithSingletons():
    e = st3t("$names,phones,salaries:{n,p,s | $n$@$p$: $s$}; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["phones"] = "1"
    e["salaries"] = "big"
    expecting = "Ter@1: big"
    assert expecting == str(e)


def test_ParallelAttributeIterationWithMismatchArgListSizes():
    errors = st3err.DEFAULT_ERROR_LISTENER
    e = st3t("$names,phones,salaries:{n,p | $n$@$p$}; separator=\", \"$")
    e.setErrorListener(errors)
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    e["salaries"] = "big"
    expecting = "Ter@1, Tom@2"
    assert expecting == str(e)
    errorExpecting = "number of arguments [n, p] mismatch between attribute list and "\
                     "anonymous template in context [anonymous]"
    assert errorExpecting == str(errors)


def test_ParallelAttributeIterationWithMissingArgs():
    errors = st3err.DEFAULT_ERROR_LISTENER
    e = st3t("$names,phones,salaries:{$n$@$p$}; separator=\", \"$")
    e.setErrorListener(errors)
    e = e.getInstanceOf()
    e["names"] = "Tom"
    e["phones"] = "2"
    e["salaries"] = "big"
    str(e)  # generate the error
    errorExpecting = "missing arguments in anonymous template in context [anonymous]"
    assert errorExpecting == str(errors)


def test_ParallelAttributeIterationWithDifferentSizesTemplateRefInsideToo():
    template = """
            group test;
            page(names,phones,salaries) ::=
                <<$names,phones,salaries:{n,p,s | $value(n)$@$value(p)$: $value(s)$}; separator=\", \"$>> +
            value(x=\"n/a\") ::= \"$x$\"
            """
    group = st3g(io.StringIO(template),
                 DefaultTemplateLexer.Lexer)
    p = group.getInstanceOf("page")
    p["names"] = "Ter"
    p["names"] = "Tom"
    p["names"] = "Sriram"
    p["phones"] = "1"
    p["phones"] = "2"
    p["salaries"] = "big"
    expecting = "Ter@1: big, Tom@2: n/a, Sriram@n/a: n/a"
    assert expecting == str(p)


def test_AnonTemplateOnLeftOfApply():
    e = st3t(
        "${foo}:{($it$)}$"
    )
    expecting = "(foo)"
    assert expecting == str(e)


def test_OverrideThroughConditional():
    template = """
        group base;
        "body(ick) ::= \"<if(ick)>ick<f()><else><f()><endif>\"" +
        f() ::= \"foo\"
        """
    group = st3g(io.StringIO(template))
    templates2 = """
            group sub;
            f() ::= \"bar\"
        """
    subgroup = st3g(io.StringIO(templates2),
                    AngleBracketTemplateLexer.Lexer,
                    None,
                    group)

    b = subgroup.getInstanceOf("body")
    expecting = "bar"
    result = str(b)
    assert expecting == result


class NonPublicProperty:
    pass


def test_NonPublicPropertyAccess():
    st = st3t("$x.foo$:$x.bar$")
    obj = {"foo": 9, "bar": "34"}

    st["x"] = obj
    expecting = "9:34"
    assert expecting == str(st)


def test_IndexVar():
    group = st3g("dummy", ".")
    t = st3t(group, "$A:{$i$. $it$}; separator=\"\\n\"$")
    t["A"] = "parrt"
    t["A"] = "tombu"
    expecting = """
        1. parrt
        2. tombu
    """
    assert expecting == str(t)


def test_Index0Var():
    group = st3g("dummy", ".")
    t = st3t(group, "$A:{$i0$. $it$}; separator=\"\\n\"$")
    t["A"] = "parrt"
    t["A"] = "tombu"
    expecting = """
        0. parrt
        1. tombu
    """
    assert expecting == str(t)


def test_IndexVarWithMultipleExprs():
    group = st3g("dummy", ".")
    t = st3t(group, "$A,B:{a,b|$i$. $a$@$b$}; separator=\"\\n\"$")
    t["A"] = "parrt"
    t["A"] = "tombu"
    t["B"] = "x5707"
    t["B"] = "x5000"
    expecting = """
        1. parrt@x5707
        2. tombu@x5000
    """
    assert expecting == str(t)


def test_Index0VarWithMultipleExprs():
    group = st3g("dummy", ".")
    t = st3t(group, "$A,B:{a,b|$i0$. $a$@$b$}; separator=\"\\n\"$")
    t["A"] = "parrt"
    t["A"] = "tombu"
    t["B"] = "x5707"
    t["B"] = "x5000"
    expecting = """
        0. parrt@x5707
        "1. tombu@x5000"
    """
    assert expecting == str(t)


def test_ArgumentContext():
    """ t is referenced within foo and so will be evaluated in that
    context.  it can therefore see name. """
    group = st3g("test")
    main = group.defineTemplate("main", "$foo(t={Hi, $name$}, name=\"parrt\")$")
    foo = group.defineTemplate("foo", "$t$")
    logger.debug(f'foo: {foo}')
    expecting = "Hi, parrt"
    assert expecting == str(main)


def test_NoDotsInAttributeNames():
    group = st3g("dummy", ".")
    t = st3t(group, "$user.Name$")
    error = None
    try:
        t["user.Name"] = "Kunle"

    except IllegalArgumentException as e:
        error = e.getMessage()

    expecting = "cannot have '.' in attribute names"
    assert expecting == error


def test_NoDotsInTemplateNames():
    errors = st3err.DEFAULT_ERROR_LISTENER
    templates = """
            group test;
            a.b() ::= <<foo>>
            """
    group = st3g(io.StringIO(templates), DefaultTemplateLexer.Lexer, errors=errors)
    logger.debug(f'group: {group}')
    expecting = "template group parse error: line 2:1: unexpected token:"
    assert str(errors).startswith(expecting)


def test_LineWrap():
    templates = """
            group test;
            array(values) ::= <<int[] a = { <values; wrap=\"\\n\", separator=\",\"> };>>
    """
    group = st3g(io.StringIO(templates))

    a = group.getInstanceOf("array")
    a.setAttribute("values",
                   [3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 2, 1, 6, 32, 5, 6, 77,
                    4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 6, 32, 5, 6, 77,
                    3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 1, 6, 32, 5])
    expecting = """
        int[] a = { 3,9,20,2,1,4,6,32,5,6,77,888,
        2,1,6,32,5,6,77,4,9,20,2,1,4,63,9,20,2,1,
        4,6,32,5,6,77,6,32,5,6,77,3,9,20,2,1,4,6,
        32,5,6,77,888,1,6,32,5 };"
    """
    assert expecting == a.toString(40)


def test_LineWrapWithNormalizedNewlines():
    templates = """
            group test;
            array(values) ::= <<int[] a = { <values; wrap=\"\\r\\n\", separator=\",\"> };>>
    """
    group = st3g(io.StringIO(templates))

    a = group.getInstanceOf("array")
    a.setAttribute("values",
                   [3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 2, 1, 6, 32, 5, 6, 77,
                    4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 6, 32, 5, 6, 77,
                    3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 1, 6, 32, 5])
    expecting = """[ 3,9,20,2,1,4,6,32,5,6,77,888,
        2,1,6,32,5,6,77,4,9,20,2,1,4,63,9,20,2,1,
        4,6,32,5,6,77,6,32,5,6,77,3,9,20,2,1,4,6,
        32,5,6,77,888,1,6,32,5 ]"""

    # StringWriter sw = new StringWriter();
    # StringTemplateWriter stw = new AutoIndentWriter(sw,)   # force \n as newline
    # stw.setLineWidth(40);
    # a.write(stw);
    # result =  str(sw);
    # assert expecting ==  result


def test_LineWrapAnchored():
    template = """
            group test;
            array(values) ::= <<int[] a = { <values; anchor, wrap=\"\\n\", separator=\",\"> };>>
            """
    group = st3g(io.StringIO(template))

    a = group.getInstanceOf("array")
    a.setAttribute("values",
                   [3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 2, 1, 6, 32, 5, 6, 77,
                    4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 6, 32, 5, 6, 77,
                    3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 1, 6, 32, 5])
    expecting = """[3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888,
                 2, 1, 6, 32, 5, 6, 77, 4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1,
                 4, 6, 32, 5, 6, 77, 6, 32, 5, 6, 77, 3, 9, 20, 2, 1, 4, 6,
                 32, 5, 6, 77, 888, 1, 6, 32, 5]"""
    assert expecting == str(a)


def test_SubtemplatesAnchorToo():
    templates = """
            group test;
            array(values) ::= <<{ <values; anchor, separator=\", \"> }>>
    """
    group = st3g(io.StringIO(templates))

    x = st3t(group, "<\\n>{ <stuff; anchor, separator=\",\\n\"> }<\\n>")
    x["stuff"] = "1"
    x["stuff"] = "2"
    x["stuff"] = "3"
    a = group.getInstanceOf("array")
    a.setAttribute("values", ["a", x, "b"])
    expecting = """
        { a, 
          { 1,
            2,
            3 }
          , b }
        """
    assert expecting == str(a)


def test_FortranLineWrap():
    template = """
            group test;
            func(args) ::= <<       FUNCTION line( <args; wrap=\"\\n      c\", separator=\",\"> )>>
            """
    group = st3g(io.StringIO(template))

    a = group.getInstanceOf("func")
    a.setAttribute("args",
                   ["a", "b", "c", "d", "e", "f"])
    expecting = """
               FUNCTION line( a,b,c,d,
              ce,f )
                  """
    assert expecting == a.toString(30)


def test_LineWrapWithDiffAnchor():
    template = """
            group test;
            array(values) ::= <<int[] a = { <{1,9,2,<values; wrap, separator=\",\">}; anchor> };>>
            """
    group = st3g(io.StringIO(template))

    a = group.getInstanceOf("array")
    a.setAttribute("values",
                   [3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 2, 1, 6, 32, 5, 6, 77,
                    4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1, 4, 6])
    expecting = """
        int[] a = { 1,9,2,3,9,20,2,1,4,
                    6,32,5,6,77,888,2,
                    1,6,32,5,6,77,4,9,
                    20,2,1,4,63,9,20,2,
                    1,4,6 };
    """
    assert expecting == a.toString(30)


def test_LineWrapEdgeCase():
    """ lineWidth==3 implies that we can have 3 characters at most """
    template = """
            group test;
            duh(chars) ::= <<<chars; wrap=\"\\n\"\\>>>
            """
    group = st3g(io.StringIO(template))

    a = group.getInstanceOf("duh")
    a.setAttribute("chars", ["a", "b", "c", "d", "e"])
    expecting = """
        abc
        de
    """
    assert expecting == str(a)


def test_LineWrapLastCharIsNewline():
    """ don't do \n if it's last element anyway """
    template = """
            group test;
            duh(chars) ::= <<<chars; wrap=\"\\n\"\\>>>
            """
    group = st3g(io.StringIO(template))

    a = group.getInstanceOf("duh")
    a.setAttribute("chars", ["a", "b", "", "d", "e"])
    expecting = """
        ab
        de
        """
    assert expecting == a.toString(3)


def test_LineWrapCharAfterWrapIsNewline():
    """ Once we wrap, we must dump chars as we see them.
    A newline right after a wrap is just an "unfortunate" event.
    People will expect a newline if it's in the data. """
    template = """
            group test;
            duh(chars) ::= <<<chars; wrap=\"\\n\"\\>>>
            """
    group = st3g(io.StringIO(template))

    a = group.getInstanceOf("duh")
    a.setAttribute("chars", ["a", "b", "c", "", "d", "e"])
    expecting = """
        abc
        
        de
"""
    assert expecting == str(a)


def test_LineWrapForAnonTemplate():
    """ width=9 is the 3 char; don't break til after ']' """
    template = """
            group test;
            duh(data) ::= <<!<data:{v|[<v>]}; wrap>!>>
            """
    group = st3g(io.StringIO(template))
    a = group.getInstanceOf("duh")
    a.setAttribute("data", [1, 2, 3, 4, 5, 6, 7, 8, 9])

    expecting = """
        ![1][2][3] 
        [4][5][6]
        [7][8][9]!
"""
    assert expecting == a.toString(9)


def test_LineWrapForAnonTemplateAnchored():
    template = """
            group test;
            duh(data) ::= <<!<data:{v|[<v>]}; anchor, wrap>!>>
    """
    group = st3g(io.StringIO(template))
    a = group.getInstanceOf("duh")
    a.setAttribute("data", [1, 2, 3, 4, 5, 6, 7, 8, 9])
    expecting = """
        ![1][2][3]
         [4][5][6]
         [7][8][9]!
"""
    assert expecting == a.toString(9)


def test_LineWrapForAnonTemplateComplicatedWrap():
    template = """
            group test;
            "top(s) ::= <<  <s>.>>"+
            str(data) ::= <<!<data:{v|[<v>]}; wrap=\"!+\\n!\">!>>
            """
    group = st3g(io.StringIO(template))

    t = group.getInstanceOf("top")

    s = group.getInstanceOf("str")

    s.setAttribute("data", [1, 2, 3, 4, 5, 6, 7, 8, 9])

    t["s"] = s
    expecting = """
          ![1][2]!+
          ![3][4]!+
          ![5][6]!+
          ![7][8]!+
          ![9]!.
"""
    assert expecting == str(t)


def test_IndentBeyondLineWidth():
    template = """
            group test;
            duh(chars) ::= <<    <chars; wrap=\"\\n\"\\>>>
    """
    group = st3g(io.StringIO(template))

    a = group.getInstanceOf("duh")
    a.setAttribute("chars", ["a", "b", "c", "d", "e"])
    expecting = """
            a
            b
            c
            d
            e
        """

    assert expecting == str(a)


def test_IndentedExpr():
    template = """
            group test;
            duh(chars) ::= <<    <chars; wrap=\"\\n\"\\>>>
            """
    group = st3g(io.StringIO(template))

    a = group.getInstanceOf("duh")
    a.setAttribute("chars", ["a", "b", "c", "d", "e"])
    expecting = """
            ab
            cd
            e
"""
    assert expecting == str(a)


def test_NestedIndentedExpr():
    template = """
            group test;
            top(d) ::= <<  <d>!>>
            duh(chars) ::= <<  <chars; wrap=\"\\n\"\\>>>
    """
    group = st3g(io.StringIO(template))

    top = group.getInstanceOf("top")
    duh = group.getInstanceOf("duh")
    duh.setAttribute("chars", ["a", "b", "c", "d", "e"])
    top["d"] = duh
    expecting = """
            ab
            cd
            e!
"""
    assert expecting == str(top)


def test_NestedWithIndentAndTrackStartOfExpr():
    template = """
            group test;
            top(d) ::= <<  <d>!>>
            duh(chars) ::= <<x: <chars; anchor, wrap=\"\\n\"\\>>>
            """
    group = st3g(io.StringIO(template))

    top = group.getInstanceOf("top")
    duh = group.getInstanceOf("duh")
    duh.setAttribute("chars", ["a", "b", "c", "d", "e"])
    top["d"] = duh
    expecting = """
          x: ab
             cd
             e!
"""
    assert expecting == top.toString(7)


def test_LineDoesNotWrapDueToLiteral():
    """ make it wrap because of ") throws Ick { " literal """
    template = """
            group test;
            m(args,body) ::= <<public void foo(<args; wrap=\"\\n\",separator=\", \">) throws Ick { <body> }>>
            """
    group = st3g(io.StringIO(template))

    a = group.getInstanceOf("m")
    a.setAttribute("args",
                   ["a", "b", "c"])
    a["body"] = "i=3;"
    n = len("public void foo(a, b, c")
    expecting = """
        "public void foo(a, b, c) throws Ick { i=3; }"
    """
    assert expecting == str(n)


def test_SingleValueWrap():
    """ make it wrap because of ") throws Ick { " literal """
    template = """
            group test;
            m(args,body) ::= <<{ <body; anchor, wrap=\"\\n\"> }>>
            """

    group = st3g(io.StringIO(template))
    m = group.getInstanceOf("m")

    m["body"] = "i=3;"

    expecting = """
        {
        "  i=3; }"
"""
    assert expecting == m.toString(2)


def test_LineWrapInNestedExpr():
    template = """
            group test;
            top(arrays) ::= <<Arrays: <arrays>done>>
            array(values) ::= <<int[] a = { <values; anchor, wrap=\"\\n\", separator=\",\"> };<\\n\\>>>
            """
    group = st3g(io.StringIO(template))

    top = group.getInstanceOf("top")
    a = group.getInstanceOf("array")

    a.setAttribute("values",
                   [3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 2, 1, 6, 32, 5, 6, 77,
                    4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 6, 32, 5, 6, 77,
                    3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 1, 6, 32, 5])

    top["arrays"] = a
    top["arrays"] = a  # add twice
    expecting = """
        Arrays: int[] a = { 3,9,20,2,1,4,6,32,5,
                            6,77,888,2,1,6,32,5,
                            6,77,4,9,20,2,1,4,63,
                            9,20,2,1,4,6,32,5,6,
                            77,6,32,5,6,77,3,9,20,
                            2,1,4,6,32,5,6,77,888,
                            1,6,32,5 };
        int[] a = { 3,9,20,2,1,4,6,32,5,6,77,888,
                    2,1,6,32,5,6,77,4,9,20,2,1,4,
                    63,9,20,2,1,4,6,32,5,6,77,6,
                    32,5,6,77,3,9,20,2,1,4,6,32,
                    5,6,77,888,1,6,32,5 }
        done
        """
    assert expecting == top.toString(40)


def test_Backslash():
    group = st3g("test")

    t = group.defineTemplate("t", "\\")

    expecting = "\\"
    assert expecting == str(t)


def test_Backslash2():
    group = st3g("test")

    t = group.defineTemplate("t", "\\ ")

    expecting = "\\ "

    assert expecting == str(t)


def test_EscapeEscape():
    group = st3g("test")
    t = group.defineTemplate("t", "\\\\$v$")

    t["v"] = "Joe"
    logger.info(t)

    expecting = "\\Joe"
    assert expecting == str(t)


def test_EscapeEscapeNestedAngle():
    group = st3g("test", AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", "<v:{a|\\\\<a>}>")

    t["v"] = "Joe"
    logger.info(t)

    expecting = "\\Joe"
    assert expecting == str(t)


def test_ListOfIntArrays():
    group = st3g("test", AngleBracketTemplateLexer.Lexer)

    t = group.defineTemplate("t", "<data:array()>")

    group.defineTemplate("array", "[<it:element(); separator=\",\">]")
    group.defineTemplate("element", "<it>")
    data = [[1, 2, 3], [10, 20, 30]]
    t["data"] = data
    logger.info(t)
    expecting = "[1,2,3][10,20,30]"
    assert expecting == str(t)


def test_NullOptionSingleNullValue():
    """ Test None option """
    group = st3g("test", AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", "<data; None=\"0\">")
    logger.info(t)
    expecting = "0"
    assert expecting == str(t)


def test_NullOptionHasEmptyNullValue():
    group = st3g("test", AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", "<data; None=\"\", separator=\", \">")
    data = [None, 1]
    t["data"] = data
    expecting = ", 1"
    assert expecting == str(t)


def test_NullOptionSingleNullValueInList():
    group = st3g("test", AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", "<data; None=\"0\">")
    data = [None]
    t["data"] = data
    logger.info(t)
    expecting = "0"
    assert expecting == str(t)


def test_NullValueInList():
    group = st3g("test", AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", "<data; None=\"-1\", separator=\", \">")

    data = [None, 1, None, 3, 4, None]
    t["data"] = data
    logger.info(t)
    expecting = "-1, 1, -1, 3, 4, -1"
    assert expecting == str(t)


def test_NullValueInListNoNullOption():
    group = st3g("test", AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", "<data; separator=\", \">")
    data = [None, 1, None, 3, 4, None]
    t["data"] = data
    logger.info(t)
    expecting = "1, 3, 4"
    assert expecting == str(t)


def test_NullValueInListWithTemplateApply():
    group = st3g("test", AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", "<data:array(); None=\"-1\", separator=\", \">")
    group.defineTemplate("array", "<it>")
    data = [None, 0, None, 2]
    t["data"] = data
    expecting = "0, -1, 2, -1"
    assert expecting == str(t)


def test_NullValueInListWithTemplateApplyNullFirstValue():
    group = st3g("test", AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", "<data:array(); None=\"-1\", separator=\", \">")
    group.defineTemplate("array", "<it>")
    data = [None, 0, None, 2]
    t["data"] = data
    expecting = "-1, 0, -1, 2"
    assert expecting == str(t)


def test_NullSingleValueInListWithTemplateApply():
    group = st3g("test", AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", "<data:array(); None=\"-1\", separator=\", \">")
    group.defineTemplate("array", "<it>")
    data = [None]
    t["data"] = data
    expecting = "-1"
    assert expecting == str(t)


def test_NullSingleValueWithTemplateApply():
    group = st3g("test", AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", "<data:array(); None=\"-1\", separator=\", \">")
    group.defineTemplate("array", "<it>")
    expecting = "-1"
    assert expecting == str(t)


def test_LengthOp():
    e = st3t(
        "$length(names)$"
    )
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    expecting = "3"
    assert expecting == str(e)


def test_LengthOpWithMap():
    e = st3t("$length(names)$")
    e = e.getInstanceOf()
    amap = {"Tom": "foo", "Sriram": "foo", "Doug": "foo"}
    e["names"] = amap
    expecting = "3"
    assert expecting == str(e)


def test_LengthOpWithSet():
    e = st3t("$length(names)$")
    e = e.getInstanceOf()
    m = {"Tom", "Sriram", "Doug"}
    e["names"] = m
    expecting = "3"
    assert expecting == str(e)


def test_LengthOpNull():
    e = st3t("$length(names)$")
    e = e.getInstanceOf()
    e["names"] = None
    expecting = "0"
    assert expecting == str(e)


def test_LengthOpSingleValue():
    e = st3t("$length(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    expecting = "1"
    assert expecting == str(e)


def test_LengthOpPrimitive():
    e = st3t("$length(ints)$")
    e = e.getInstanceOf()
    e.setAttribute("ints", [1, 2, 3, 4])
    expecting = "4"
    assert expecting == str(e)


def test_LengthOpOfListWithNulls():
    e = st3t("$length(data)$")
    e = e.getInstanceOf()
    data = ["Hi", None, "mom", None]
    e["data"] = data
    expecting = "4"  # Nones are counted
    assert expecting == str(e)


def test_StripOpOfListWithNulls():
    e = st3t("$strip(data)$")
    e = e.getInstanceOf()
    data = ["Hi", None, "mom", None]
    e["data"] = data
    expecting = "Himom"  # Nones are skipped
    assert expecting == str(e)


def test_StripOpOfListOfListsWithNulls():
    e = st3t("$strip(data):{list | $strip(list)$}; separator=\",\"$")
    e = e.getInstanceOf()
    data = [
        ["Hi", "mom"],
        None,
        ["Hi", None, "dad", None]]
    e["data"] = data
    expecting = "Himom,Hidad"  # Nones are skipped
    assert expecting == str(e)


def test_StripOpOfSingleAlt():
    e = st3t("$strip(data)$")
    e = e.getInstanceOf()
    e["data"] = "hi"
    expecting = "hi"  # Nones are skipped
    assert expecting == str(e)


def test_StripOpOfNull():
    e = st3t("$strip(data)$")
    e = e.getInstanceOf()
    expecting = ""  # Nones are skipped
    assert expecting == str(e)


def test_ReUseOfStripResult():
    template = """
        group test;
        a(names) ::= \"<b(strip(names))>\"
        b(x) ::= \"<x>, <x>\"
        """

    group = st3g(io.StringIO(template))
    e = group.getInstanceOf("a")
    names = ["Ter", None, "Tom"]
    e["names"] = names
    expecting = "TerTom, TerTom"
    assert expecting == str(e)


def test_LengthOpOfStrippedListWithNulls():
    e = st3t("$length(strip(data))$")
    e = e.getInstanceOf()
    data = ["Hi", None, "mom", None]
    e["data"] = data
    expecting = "2"  # Nones are counted
    assert expecting == str(e)


def test_LengthOpOfStrippedListWithNullsFrontAndBack():
    e = st3t("$length(strip(data))$")
    e = e.getInstanceOf()
    data = [None, None, None, "Hi", None, None, None, "mom", None, None, None]
    e["data"] = data
    expecting = "2"  # Nones are counted
    assert expecting == str(e)


def test_MapKeys():
    group = st3g("dummy", ".", AngleBracketTemplateLexer.Lexer)
    t = st3t(group, "<aMap.keys:{k|<k>:<aMap.(k)>}; separator=\", \">")
    amap = {"int": "0", "float": "0.0"}
    t["aMap"] = amap
    assert "int:0, float:0.0" == str(t)


def test_MapValues():
    group = st3g("dummy", ".", AngleBracketTemplateLexer.Lexer)
    t = st3t(group, "<aMap.values; separator=\", \"> <aMap.(\"i\"+\"nt\")>")
    amap = {"int": "0", "float": "0.0"}
    t["aMap"] = amap
    assert "0, 0.0 0" == str(t)


def test_MapKeysWithIntegerType():
    """ must get back an Integer from keys not a toString()'d version """
    group = st3g("dummy", ".", AngleBracketTemplateLexer.Lexer)
    t = st3t(group, "<aMap.keys:{k|<k>:<aMap.(k)>}; separator=\", \">")
    amap = dict()
    amap[1] = ["ick", "foo"]
    amap[2] = ["x", "y"]
    t["aMap"] = amap

    res = str(t)
    if (res == "2:xy, 1:ickfoo") or (res == "1:ickfoo, 2:xy"):
        pass
    else:
        logger.error("Map traversal did not return expected strings")


def test_ArgumentContext2():
    """ t is referenced within foo and so will be evaluated in that context.
     it can therefore see name.
    Use when super.attr name is implemented
     """
    group = st3g("test")
    main = group.defineTemplate("main", "$foo(t={Hi, $super.name$}, name=\"parrt\")$")
    main["name"] = "tombu"
    foo = group.defineTemplate("foo", "$t$")
    logger.debug(f'foo: {foo}')
    expecting = "Hi, parrt"
    assert expecting == str(main)


def test_GroupTrailingSemiColon():
    """
   Check what happens when a semicolon is  appended to a single line template
   Should fail with a parse error(?) and not a missing template error.
   FIXME: This should generate a warning or error about that semi colon.

  Bug ref: JIRA bug ST-2
 """
    try:
        templates = """
                group test;
                t1()::=\"R1\"; 
                t2() ::= \"R2\"                
                """
        group = st3g(io.StringIO(templates))

        st = group.getInstanceOf("t1")
        assert "R1" == str(st)

        st = group.getInstanceOf("t2")
        assert "R2" == str(st)

        logger.error("A parse error should have been generated")
        assert False

    except Exception as ex:
        logger.exception(f'foo: {ex}')


def test_SuperReferenceInIfClause():
    superGroupString = """
        group super;
        a(x) ::= \"super.a\"
        b(x) ::= \"<c()>super.b\"
        "c() ::= \"super.c\""
        """
    superGroup = st3g(io.StringIO(superGroupString), AngleBracketTemplateLexer.Lexer)
    subGroupString = """
        group sub;
        a(x) ::= \"<if(x)><super.a()><endif>\"
        b(x) ::= \"<if(x)><else><super.b()><endif>\"
        "c() ::= \"sub.c\""
        """
    subGroup = st3g(
        io.StringIO(subGroupString), AngleBracketTemplateLexer.Lexer)
    subGroup.setSuperGroup(superGroup)
    a = subGroup.getInstanceOf("a")
    a["x"] = "foo"
    assert "super.a" == str(a)
    b = subGroup.getInstanceOf("b")
    assert "sub.csuper.b" == str(b)
    c = subGroup.getInstanceOf("c")
    assert "sub.c" == str(c)


def test_ListLiteralWithEmptyElements():
    """ Added  feature  for ST - 21 """
    e = st3t("$[\"Ter\",,\"Jesse\"]:{n | $i$:$n$}; separator=\", \", None=\"\"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["phones"] = "1"
    e["salaries"] = "big"
    expecting = "1:Ter, 2:, 3:Jesse"
    assert expecting == str(e)


def test_TemplateApplicationAsOptionValue():
    st = st3t("Tokens : <rules; separator=names:{<it>}> ;", AngleBracketTemplateLexer.Lexer)
    st["rules"] = "A"
    st["rules"] = "B"
    st["names"] = "Ter"
    st["names"] = "Tom"
    expecting = "Tokens : ATerTomB ;"
    assert expecting == str(st)
