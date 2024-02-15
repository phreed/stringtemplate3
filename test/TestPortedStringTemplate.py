
import io
import logging
from textwrap import dedent
from collections import deque

import temppathlib

import stringtemplate3
from stringtemplate3.writers import StringTemplateWriter, AutoIndentWriter
from stringtemplate3.grouploaders import PathGroupLoader
from stringtemplate3.groups import StringTemplateGroup as St3G
from stringtemplate3.language import (DefaultTemplateLexer,
                                      AngleBracketTemplateLexer)
from stringtemplate3.language.ASTExpr import IllegalStateException
from stringtemplate3.templates import StringTemplate as St3T

import TestStringHelper as tsh
from TestStringHelper import (IllegalArgumentException, ErrorBuffer)

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

 THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR
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


def test_MissingInterfaceTemplate():
    """ this also tests the group loader """
    errors = ErrorBuffer()
    with temppathlib.TemporaryDirectory() as tmp_dir:
        St3G.registerGroupLoader(PathGroupLoader(dirs=tmp_dir.path, errors=errors))
        groupI = dedent("""
                interface testI;
                t();
                bold(item);
                optional duh(a,b,c);
        """)
        tsh.write_file(tmp_dir.path / "testI.sti", groupI)

        templates = dedent("""
            group testG implements testI;
            t() ::= <<foo>>
            duh(a,b,c) ::= <<foo>>
        """)
        stg_file = tsh.write_file(tmp_dir.path / "testG.stg", templates)

        with open(stg_file, "r") as reader:
            group = St3G(file=reader, errors=errors)
            logger.debug(f"group: {group}")

    assert str(errors) == "group testG does not satisfy interface testI: missing templates ['bold']"


def test_MissingOptionalInterfaceTemplate():
    """ this also tests the group loader """
    errors = ErrorBuffer()
    with temppathlib.TemporaryDirectory() as tmp_dir:
        St3G.registerGroupLoader(PathGroupLoader(dirs=tmp_dir.path, errors=errors))
        groupI = dedent("""\
                interface testI;
                t();
                bold(item);
                optional duh(a,b,c);
        """)
        tsh.write_file(tmp_dir.path / "testI.sti", groupI)

        templates = dedent("""\
            group testG implements testI;
            t() ::= <<foo>>
            bold(item) ::= <<foo>>
        """)
        stg_file = tsh.write_file(tmp_dir.path / "testG.stg", templates)

        with open(stg_file, "r") as reader:
            group = St3G(file=reader, errors=errors)
            logger.debug(f"group: {group}")

    assert str(errors) == ""  # should be NO errors


def test_MismatchedInterfaceTemplate():
    """ this also tests the group loader """
    errors = ErrorBuffer()
    with temppathlib.TemporaryDirectory() as tmp_dir:
        St3G.registerGroupLoader(PathGroupLoader(dirs=tmp_dir.path, errors=errors))
        groupI = dedent("""\
                interface testI;
                t();
                bold(item);
                optional duh(a,b,c);
        """)
        tsh.write_file(tmp_dir.path / "testI.sti", groupI)

        templates = dedent("""
            group testG implements testI;
            t() ::= <<foo>>
            bold(item) ::= <<foo>>
            duh(a,c) ::= <<foo>>
        """)
        stg_file = tsh.write_file(tmp_dir.path / "testG.stg", templates)

        with open(stg_file, "r") as reader:
            group = St3G(file=reader, errors=errors)
            logger.debug(f"group: {group}")

    assert str(errors) == \
           "group testG does not satisfy interface testI: " \
           "mismatched arguments on these templates ['optional duh(a, b, c)']"


def test_GroupFileFormat():
    templates = dedent("""\
            group test;
            t() ::= "literal template"
            bold(item) ::= " <b>$item$</b> "
            duh() ::= <<"xx">>
    """)
    group = St3G(file=io.StringIO(templates),
                 lexer=DefaultTemplateLexer.Lexer)

    assert str(group) == dedent("""\
        group test;
        bold(item) ::= << <b>$item$</b> >>
        duh() ::= <<"xx">>
        t() ::= <<literal template>>
        """)

    a = group.getInstanceOf("t")
    assert str(a) == "literal template"

    b = group.getInstanceOf("bold")
    b["item"] = "dork"
    assert str(b) == "<b>dork</b>"


def test_EscapedTemplateDelimiters():
    templates = dedent("""\
            group test;
            t() ::= <<$"literal":{a|$a$\\}}$ template\n>>
            bold(item) ::= <<<b>$item$</b\\>>>
            duh() ::= <<"xx">>
    """)
    group = St3G(file=io.StringIO(templates), lexer=DefaultTemplateLexer.Lexer)

    assert str(group) == dedent("""\
        group test;
        bold(item) ::= <<<b>$item$</b>>>
        duh() ::= <<"xx">>
        t() ::= <<$"literal":{a|$a$\\}}$ template>>
        """)

    b = group.getInstanceOf("bold")
    b["item"] = "dork"
    assert str(b) == "<b>dork</b>"

    a = group.getInstanceOf("t")
    assert str(a) == "literal} template"


def test_TemplateParameterDecls():
    """ Check syntax and setAttribute-time errors """
    templates = dedent("""\
            group test;
            t() ::= "no args but ref $foo$"
            t2(item) ::= "decl but not used is ok"
            t3(a,b,c,d) ::= <<$a$ $d$>>
            t4(a,b,c,d) ::= <<$a$ $b$ $c$ $d$>>
            """)
    group = St3G(file=io.StringIO(templates), lexer=DefaultTemplateLexer.Lexer)

    """ check setting unknown arg in empty formal list """
    a = group.getInstanceOf("t")
    error = None
    try:
        a["foo"] = "x"  # want KeyError

    except KeyError as ex:
        error = tsh.getMsg(ex)

    assert error == "'no such attribute: foo in template context [t]'"
    """ check setting known arg """
    a = group.getInstanceOf("t2")
    a["item"] = "x"  # shouldn't get exception
    """ check setting unknown arg in nonempty list of formal args """
    a = group.getInstanceOf("t3")
    a["b"] = "x"


def test_TemplateRedef():
    templates = dedent("""\
            group test;
            a() ::= "x"
            b() ::= "y"
            a() ::= "z"
    """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates), errors=errors)
    logger.debug(f"group: {group}")
    assert str(errors) == "redefinition of template: a"


def test_UndefinedArgumentAssignment():
    templates = dedent("""\
            group test;
            page(x) ::= <<$body(font=x)$>>
            body() ::= "<font face=$font$>my body</font>"
    """)
    group = St3G(file=io.StringIO(templates), lexer=DefaultTemplateLexer.Lexer)
    t = group.getInstanceOf("page")
    t["x"] = "Times"
    error = ""
    try:
        str(t)

    except KeyError as iae:
        error = tsh.getMsg(iae)

    assert error == "'template body has no such attribute: font in template context [page <invoke body arg context>]'"


def test_UndefinedArgumentAssignmentInApply():
    templates = dedent("""\
            group test;
            page(name,x) ::= <<$name:bold(font=x)$>>
            bold() ::= "<font face=$font$><b>$it$</b></font>"
    """)
    group = St3G(file=io.StringIO(templates), lexer=DefaultTemplateLexer.Lexer)
    t = group.getInstanceOf("page")
    t["x"] = "Times"
    t["name"] = "Ter"
    error = ""
    try:
        str(t)

    except KeyError as ke:
        error = tsh.getMsg(ke)
    except Exception as ex:
        assert False, "Unexpected"

    assert error == "'template bold has no such attribute: font in template context [page <invoke bold arg context>]'"


def test_UndefinedAttributeReference():
    templates = dedent("""\
            group test;
            page() ::= <<$bold()$>>
            bold() ::= "$name$"
    """)
    group = St3G(file=io.StringIO(templates),
                 lexer=DefaultTemplateLexer.Lexer)
    t = group.getInstanceOf("page")
    error = ""
    try:
        str(t)

    except KeyError as iae:
        error = tsh.getMsg(iae)

    assert error == "'no such attribute: name in template context [page bold]'"


def test_UndefinedDefaultAttributeReference():
    templates = dedent("""\
            group test;
            page() ::= <<$bold()$>>
            bold() ::= "$it$"
    """)
    group = St3G(file=io.StringIO(templates), lexer=DefaultTemplateLexer.Lexer)
    t = group.getInstanceOf("page")
    error = ""
    try:
        str(t)

    except KeyError as nse:
        error = tsh.getMsg(nse)

    assert error == "'no such attribute: it in template context [page bold]'"


def test_AngleBracketsNoGroup():
    st = St3T(template='Tokens : <rules; separator="|"> ;',
              lexer=AngleBracketTemplateLexer.Lexer)
    st["rules"] = "A"
    st["rules"] = "B"
    assert str(st) == "Tokens : A|B ;"


def test_RegionRef():
    templates = dedent("""\
            group test;
            a() ::= "X$@r()$Y"
    """)
    group = St3G(file=io.StringIO(templates),
                 lexer=DefaultTemplateLexer.Lexer)
    st = group.getInstanceOf("a")
    result = str(st)
    assert result == "XY"


def test_EmbeddedRegionRef():
    templates = dedent("""\
            group test;
            a() ::= "X$@r$blort$@end$Y"
    """)
    group = St3G(file=io.StringIO(templates), lexer=DefaultTemplateLexer.Lexer)
    st = group.getInstanceOf("a")
    result = str(st)
    assert result == "XblortY"


def test_RegionRefAngleBrackets():
    templates = dedent("""\
            group test;
            a() ::= "X<@r()>Y"
    """)
    group = St3G(file=io.StringIO(templates))
    st = group.getInstanceOf("a")
    result = str(st)
    assert result == "XY"


def test_EmbeddedRegionRefAngleBrackets():
    """ FIXME: This test fails due to inserted white space... """
    templates = dedent("""\
            group test;
            a() ::= "X<@r>blort<@end>Y"
    """)
    group = St3G(file=io.StringIO(templates))
    st = group.getInstanceOf("a")
    result = str(st)
    assert result == "XblortY"


def test_EmbeddedRegionRefWithNewlinesAngleBrackets():
    templates = dedent("""\
            group test;
            a() ::= "X<@r>
            blort
            <@end>
            Y"
    """)
    group = St3G(file=io.StringIO(templates))
    st = group.getInstanceOf("a")
    result = str(st)
    assert result == "XblortY"


def test_RegionRefWithDefAngleBrackets():
    templates = dedent("""\
            group test;
            a() ::= "X<@r()>Y"
            @a.r() ::= "foo"
    """)
    group = St3G(file=io.StringIO(templates))
    st = group.getInstanceOf("a")
    result = str(st)
    assert result == "XfooY"


def test_RegionRefWithDefInConditional():
    templates = dedent("""\
            group test;
            a(v) ::= "X<if(v)>A<@r()>B<endif>Y"
            @a.r() ::= "foo"
    """)
    group = St3G(file=io.StringIO(templates))
    st = group.getInstanceOf("a")
    st["v"] = True
    result = str(st)
    assert result == "XAfooBY"


def test_RegionRefWithImplicitDefInConditional():
    templates = dedent("""\
            group test;
            a(v) ::= "X<if(v)>A<@r>yo<@end>B<endif>Y"
            @a.r() ::= "foo"
    """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates), errors=errors)
    st = group.getInstanceOf("a")
    st["v"] = True
    result = str(st)
    assert result == "XAyoBY"

    assert str(errors) == "group test line 3: redefinition of template region: @a.r"


def test_RegionOverride():
    templates1 = dedent("""\
            group super;
            a() ::= "X<@r()>Y"
            @a.r() ::= "foo"
    """)
    group = St3G(file=io.StringIO(templates1))

    templates2 = dedent("""\
            group sub;
            @a.r() ::= "foo"
    """)
    subGroup = St3G(file=io.StringIO(templates2),
                    lexer=AngleBracketTemplateLexer.Lexer,
                    superGroup=group)

    st = subGroup.getInstanceOf("a")
    assert str(st) == "XfooY"


def test_RegionOverrideRefSuperRegion():
    templates1 = dedent("""
            group super;
            a() ::= "X<@r()>Y"
            @a.r() ::= "foo"
    """)
    group = St3G(file=io.StringIO(templates1))

    templates2 = dedent("""
            group sub;
            @a.r() ::= "A<@super.r()>B"
    """)
    subGroup = St3G(file=io.StringIO(templates2),
                    lexer=AngleBracketTemplateLexer.Lexer,
                    superGroup=group)

    st = subGroup.getInstanceOf("a")
    result = str(st)
    assert result == "XAfooBY"


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

    templates1 = dedent("""
            group super;
            a() ::= "X<@r()>Y"
            @a.r() ::= "foo"
    """)
    group = St3G(file=io.StringIO(templates1))

    templates2 = dedent("""
            group sub;
            @a.r() ::= "<@super.r()>2"
    """)
    subGroup = St3G(file=io.StringIO(templates2),
                    lexer=AngleBracketTemplateLexer.Lexer,
                    superGroup=group)

    templates3 = dedent("""
            group subsub;
            @a.r() ::= "<@super.r()>3"
    """)
    subSubGroup = St3G(file=io.StringIO(templates3),
                       lexer=AngleBracketTemplateLexer.Lexer,
                       superGroup=subGroup)

    st = subSubGroup.getInstanceOf("a")
    result = str(st)
    assert result == "Xfoo23Y"


def test_RegionOverrideRefSuperImplicitRegion():
    templates1 = dedent("""
            group super;
            a() ::= "X<@r>foo<@end>Y"
    """)
    group = St3G(file=io.StringIO(templates1))

    templates2 = dedent("""
            group sub;
            @a.r() ::= "A<@super.r()>"
    """)
    subGroup = St3G(file=io.StringIO(templates2),
                    lexer=AngleBracketTemplateLexer.Lexer,
                    superGroup=group)

    st = subGroup.getInstanceOf("a")
    result = str(st)
    assert result == "XAfooY"


def test_EmbeddedRegionRedefError():
    """ cannot define an embedded template within group """
    templates = dedent("""\
            group test;
            a() ::= "X<@r>dork<@end>Y"
            @a.r() ::= "foo"
            """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates), errors=errors)
    st = group.getInstanceOf("a")
    str(st)
    result = str(errors)
    assert result == "group test line 3: redefinition of template region: @a.r"


def test_ImplicitRegionRedefError():
    """ cannot define an implicitly-defined template more than once """
    templates = dedent("""\
            group test;
            a() ::= "X<@r()>Y"
            @a.r() ::= "foo"
            @a.r() ::= "bar"
     """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates), errors=errors)
    st = group.getInstanceOf("a")
    str(st)
    result = str(errors)
    assert result == "group test line 4: redefinition of template region: @a.r"


def test_ImplicitOverriddenRegionRedefError():
    templates1 = dedent("""
        group super;
        a() ::= "X<@r()>Y"
        @a.r() ::= "foo"
    """)
    group = St3G(file=io.StringIO(templates1))

    templates2 = dedent("""\
        group sub;
        @a.r() ::= "foo"
        @a.r() ::= "bar"
    """)
    errors = ErrorBuffer()
    subGroup = St3G(file=io.StringIO(templates2),
                    lexer=AngleBracketTemplateLexer.Lexer,
                    errors=errors, superGroup=group)

    st = subGroup.getInstanceOf("a")
    logger.debug(f"st: {st}")
    result = str(errors)
    assert result == "group sub line 3: redefinition of template region: @a.r"


def test_UnknownRegionDefError():
    """ cannot define an implicitly-defined template more than once """
    templates = dedent("""\
            group test;
            a() ::= "X<@r()>Y"
            @a.q() ::= "foo"
    """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates), errors=errors)
    st = group.getInstanceOf("a")
    str(st)
    result = str(errors)
    assert result == "group test line 3: template a has no region called q"


def test_SuperRegionRefError():
    templates1 = dedent("""
        group super;
        a() ::= "X<@r()>Y"
        @a.r() ::= "foo"
    """)
    group = St3G(file=io.StringIO(templates1))

    templates2 = dedent("""
        group sub;
        @a.r() ::= "A<@super.q()>B"
    """)
    errors = ErrorBuffer()
    subGroup = St3G(file=io.StringIO(templates2),
                    lexer=AngleBracketTemplateLexer.Lexer,
                    errors=errors, superGroup=group)

    st = subGroup.getInstanceOf("a")
    logger.debug(f"st: {st}")
    result = str(errors)
    assert result == "template a has no region called q"


def test_MissingEndRegionError():
    """ cannot define an implicitly-defined template more than once """
    templates = dedent("""\
            group test;
            a() ::= "X$@r$foo"
    """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates),
                 lexer=DefaultTemplateLexer.Lexer,
                 errors=errors)
    st = group.getInstanceOf("a")
    str(st)
    result = str(errors)
    assert result == "missing region r $@end$ tag"


def test_MissingEndRegionErrorAngleBrackets():
    """ cannot define an implicitly-defined template more than once """
    templates = dedent("""\
            group test;
            a() ::= "X<@r>foo"
    """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates), errors=errors)
    st = group.getInstanceOf("a")
    str(st)
    result = str(errors)
    assert result == "missing region r <@end> tag"


def test_SimpleInheritance():
    """ make a bold template in the super group that you can inherit from sub """
    supergroup = St3G("super")
    subgroup = St3G("sub")
    bold = supergroup.defineTemplate("bold", "<b>$it$</b>")
    logger.debug(f"bold: {bold}")
    subgroup.superGroup = supergroup
    errors = ErrorBuffer()
    subgroup.errorListener = errors
    supergroup.errorListener = errors
    duh = St3T(group=subgroup, template="$name:bold()$")
    duh["name"] = "Terence"
    assert str(duh) == "<b>Terence</b>"


def test_OverrideInheritance():
    """ make a bold template in the super group and one in subgroup """
    supergroup = St3G("super")
    subgroup = St3G("sub")
    supergroup.defineTemplate("bold", "<b>$it$</b>")
    subgroup.defineTemplate("bold", "<strong>$it$</strong>")
    subgroup.superGroup = supergroup
    errors = ErrorBuffer()
    subgroup.errorListener = errors
    supergroup.errorListener = errors
    duh = St3T(group=subgroup, template="$name:bold()$")
    duh["name"] = "Terence"
    assert str(duh) == "<strong>Terence</strong>"


def test_MultiLevelInheritance():
    """ must loop up two levels to find bold() """
    rootgroup = St3G("root")
    level1 = St3G("level1")
    level2 = St3G("level2")
    rootgroup.defineTemplate("bold", "<b>$it$</b>")
    level1.superGroup = rootgroup
    level2.superGroup = level1
    errors = ErrorBuffer()
    rootgroup.errorListener = errors
    level1.errorListener = errors
    level2.errorListener = errors
    duh = St3T(group=level2, template="$name:bold()$")
    duh["name"] = "Terence"
    assert str(duh) == "<b>Terence</b>"


def test_MissingEndDelimiter():
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    st = St3T(group=group, template='stuff $a then more junk etc...')
    logger.info(f"template: {st}")
    logger.info(f"errors: {errors}")
    assert str(errors).startswith("problem parsing template 'anonymous': line 1:31: expecting '$', found '<EOF>'")


def test_SetButNotRefd():
    """  oops...should be 'c' """
    stringtemplate3.lintMode = True
    errors = ErrorBuffer()
    group = St3G("test", errors=errors)
    t = St3T(group=group,
             template='$a$ then $b$ and $c$ refs.')
    t["a"] = "Terence"
    t["b"] = "Terence"
    t["cc"] = "Terence"
    logger.info(f"result {t}, error: {errors}")
    stringtemplate3.lintMode = False
    assert str(errors) == "anonymous: set but not used: cc"


def test_NullTemplateApplication():
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group, template='$names:bold(x=it)$')
    t["names"] = "Terence"

    error = None
    try:
        str(t)

    except ValueError as ve:
        error = tsh.getMsg(ve)
    except Exception as ex:
        pass

    assert error == "Can't load template bold.st; context is [anonymous]; group hierarchy is [test]"


def test_NullTemplateToMultiValuedApplication():
    """  bold not found...empty string """
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group, template='$names:bold(x=it)$')
    t["names"] = "Terence"
    t["names"] = "Tom"
    logger.info(t)
    error = None
    try:
        str(t)
    except ValueError as ve:
        error = tsh.getMsg(ve)
    except Exception as ex:
        pass

    assert error == "Can't load template bold.st; context is [anonymous]; group hierarchy is [test]"


def test_ApplyingTemplateFromDiskWithPrecompiledIF():
    """ Create a temporary working directory 
    write the template files first to that directory.
    Specify a template to apply to an attribute
    Use a template group, so we can specify the start/stop chars
    """
    with temppathlib.TemporaryDirectory() as tmp_dir:
        page_file = tmp_dir.path / "page.st"
        with open(page_file, "w") as writer:
            writer.write(dedent("""
                <html><head>
                  <title>PeerScope: $title$</title>
                  </head>
                  <body>
                      $if(member)$User: $member:terse()$$endif$
                  </body>
                </head>
                """))

        terse_file = tmp_dir.path / "terse.st"
        with open(terse_file, "w") as writer:
            writer.write("""
            "$it.firstName$ $it.lastName$ (<tt>$it.email$</tt>)"
            """)

        group = St3G("dummy", str(tmp_dir.path))

        a = group.getInstanceOf("page")
        a["member"] = Connector()
        logger.info(f"'{a}'")
        assert str(a) == dedent("""\
                <html><head>
                  <title>PeerScope: </title>
                  </head>
                  <body>
                User: "Terence Parr (<tt>parrt@jguru.com</tt>)"
                  </body>
                </head>""")


def test_MultiValuedAttributeWithAnonymousTemplateUsingIndexVariableI():
    tgroup = St3G("dummy", ".")
    t = St3T(group=tgroup, 
             template=dedent("""\
                List:
                
                foo
                   
                $names:{<br>$i$. $it$
                }$
                """))
    t["names"] = "Terence"
    t["names"] = "Jim"
    t["names"] = "Sriram"
    logger.info(t)
    assert str(t) == dedent("""\
            List:
              
            foo
            
            <br>1. Terence
            <br>2. Jim
            <br>3. Sriram
            
    """)


def test_FindTemplateInSysPath():
    """ Look for templates in sys.path as resources
    "method.st" references body() so "body.st" will be loaded too
    """
    mgroup = St3G("method stuff", lexer=AngleBracketTemplateLexer.Lexer)
    m = mgroup.getInstanceOf("org/antlr/stringtemplate/test/method")
    m["visibility"] = "public"
    m["name"] = "foobar"
    m["returnType"] = "void"
    m["statements"] = "i=1;"  # body inherits these from method
    m["statements"] = "x=i;"
    
    logger.info(m)
    assert str(m) == dedent("""
            public void foobar() {
            \t// start of a body
            \ti=1;
            \tx=i;
            \t// end of a body
            "}"
            """)


def test_ApplyAnonymousTemplateToAggregateAttribute():
    """ also testing wacky spaces in aggregate spec """
    st = St3T("$items:{$it.lastName$, $it.firstName$\n}$")
    st["items.{firstName, lastName}"] = ("Ter", "Parr")
    st["items.{firstName, lastName}"] = ("Tom", "Burns")
    
    assert str(st) == dedent("""\
            Parr, Ter
            Burns, Tom
    """)


def test_MultiValuedAttributeWithSeparator():
    # """ if column can be multi-valued, specify a separator """
    group = St3G("dummy", ".", lexer=AngleBracketTemplateLexer.Lexer)
    query = St3T(group=group,
                 template='SELECT <distinct> <column; separator=", "> FROM <table>;')
    query["column"] = "name"
    query["column"] = "email"
    query["table"] = "User"

    assert str(query) == "SELECT  name, email FROM User;"

    query["distinct"] = "DISTINCT"
    assert str(query) == "SELECT DISTINCT name, email FROM User;"


def test_IFTemplate():
    group = St3G("dummy", rootDir=".",
                 lexer=AngleBracketTemplateLexer.Lexer)
    t = St3T(group=group,
             template="SELECT <column> FROM PERSON <if(cond)>WHERE ID=<id><endif>;")
    t["column"] = "name"
    t["cond"] = True
    t["id"] = "231"
    assert str(t) == "SELECT name FROM PERSON WHERE ID=231;"


def test_NestedIFTemplate():
    group = St3G(name="dummy", rootDir=".",
                 lexer=AngleBracketTemplateLexer.Lexer)
    t = St3T(group=group,
             template=dedent("""\
            ack<if(a)>
            foo
            <if(!b)>stuff<endif>
            <if(b)>no<endif>
            junk
            <endif>
            """))
    t["a"] = "blort"
    # """ leave b as None """
    
    assert str(t) == dedent("""\
            ackfoo
            stuff
            junk""")


def test_IFConditionWithTemplateApplication():
    group = St3G(name="dummy", rootDir=".")
    st = St3T(group=group,
              template='$if(names:{$it$})$Fail!$endif$ $if(!names:{$it$})$Works!$endif$',
              lexer="default")
    st["names"] = True
    assert str(st) == " Works!"


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
    group = St3G("dummy", ".")
    t = St3T(group=group,
             template=dedent("""\
                    <b>Name: $p.firstName$ $p.lastName$</b><br>
                    <b>Email: $p.email$</b><br>
                    "$p.bio$"
            """))
    t["p"] = Connector()
    logger.info("t is " + str(t))
    
    assert str(t) == dedent("""\
            <b>Name: Terence Parr</b><br>
            <b>Email: parrt@jguru.com</b><br>
            "Superhero by night..."
    """)


def test_ApplyRepeatedAnonymousTemplateWithForeignTemplateRefToMultiValuedAttribute():
    """ specify a template to apply to an attribute 
    Use a template group, so we can specify the start/stop chars
    """
    group = St3G("dummy", ".")
    group.defineTemplate(name="link",
                         template='<a href="$url$"><b>$title$</b></a>')
    duh_txt = dedent("""\
start|$p:{$link(url="/member/view?ID="+it.ID, title=it.firstName)$ $if(it.canEdit)$canEdit$endif$}:
{$it$<br>\n}$|end
        """)
    duh = St3T(group=group, template=duh_txt)
    duh["p"] = Connector()
    duh["p"] = Connector2()
    assert str(duh) == dedent("""\
        start|<a href="/member/view?ID=1"><b>Terence</b></a> <br>
        <a href="/member/view?ID=2"><b>Tom</b></a> canEdit<br>
        |end
    """)


class Tree:
    def __init__(self, t):
        self._text = t
        self._children = deque()

    @property
    def text(self):
        return self._text

    def addChild(self, c):
        self._children.append(c)

    @property
    def firstChild(self):
        if len(self._children) < 1:
            return None

        return self._children[0]

    @property
    def children(self):
        return self._children


def test_Recursion():
    group = St3G("dummy", rootDir=".", lexer=AngleBracketTemplateLexer.Lexer)
    group.defineTemplate("tree",
                         template=dedent("""\
                            <if(it.firstChild)>
                            ( <it.text> <it.children:tree(); separator=" "> )
                            <else>
                            <it.text>
                            <endif>
                            """))
    tree = group.getInstanceOf("tree")
    """ build ( a b (c d) e ) """
    root = Tree("a")
    root.addChild(Tree("b"))
    subtree = Tree("c")
    subtree.addChild(Tree("d"))
    root.addChild(subtree)
    root.addChild(Tree("e"))
    tree["it"] = root
    assert str(tree) == "( a b ( c d ) e )"


def test_NestedAnonymousTemplates():
    group = St3G("dummy", ".")
    t = St3T(group=group,
             template=dedent("""\
                        $A:{
                          <i>$it:{
                            <b>$it$</b>
                          }$</i>
                        }$
                """))
    t["A"] = "parrt"
    
    assert str(t) == '\n  <i>\n    <b>parrt</b>\n  </i>\n\n'


def test_AnonymousTemplateAccessToEnclosingAttributes():
    group = St3G("dummy", ".")
    t = St3T(group=group,
             template=dedent("""\
                    $A:{
                      <i>$it:{
                        <b>$it$, $B$</b>
                      }$</i>
                    "}$"
            """))
    t["A"] = "parrt"
    t["B"] = "tombu"
    
    assert str(t) == '\n  <i>\n    <b>parrt, tombu</b>\n  </i>\n""\n'


def test_NestedAnonymousTemplatesAgain():
    group = St3G("dummy", ".")
    logger.debug(f"group: {group}")
    t = St3T(group=group,
             template=dedent("""\
                    <table>
                    $names:{<tr>$it:{<td>$it:{<b>$it$</b>}$</td>}$</tr>}$
                    </table>
            """))
    t["names"] = "parrt"
    t["names"] = "tombu"
    
    assert str(t) == dedent("""\
            <table>
            <tr><td><b>parrt</b></td></tr><tr><td><b>tombu</b></td></tr>
            </table>
    """)


def test_ElseClause():
    e = St3T(template=dedent("""\
            $if(title)$foo
            $else$bar
            $endif$
        """))
    e["title"] = "sample"
    assert str(e) == "foo"

    e = e.getInstanceOf()
    assert str(e) == "bar"


def test_ElseIfClause():
    e = St3T(template=dedent("""\
            $if(x)$
            foo
            $elseif(y)$
            bar
            $endif$
        """))
    e["y"] = "yep"
    assert str(e) == "bar"


def test_ElseIfClauseAngleBrackets():
    e = St3T(template=dedent("""\
            <if(x)>foo
            <elseif(y)>bar
            <else>baz
            <endif>
            """),
             lexer=AngleBracketTemplateLexer.Lexer)
    e["x"] = "yep"
    out = io.StringIO(u'')
    e.printDebugString(out)
    logger.info(out.getvalue())
    assert str(e) == "bar"


def test_ElseIfClause2():
    e = St3T(dedent("""\
            $if(x)$
            foo
            $elseif(y)$
            bar
            $elseif(z)$
            blort
            $endif$
        """))
    e["z"] = "yep"
    assert str(e) == "blort"


def test_ElseIfClauseAndElse():
    e = St3T(template=dedent("""\
            $if(x)$
            foo
            $elseif(y)$
            bar
            $elseif(z)$
            z
            $else$
            blort
            $endif$
        """))
    assert str(e) == "blort"


def test_NestedIF():
    e = St3T(dedent("""\
            $if(title)$
            foo
            $else$
            $if(header)$
            bar
            $else$
            blort
            $endif$
            $endif$
        """))
    e["title"] = "sample"
    assert str(e) == "foo"

    e = e.getInstanceOf()
    e["header"] = "more"
    assert str(e) == "bar"

    e = e.getInstanceOf()
    assert str(e) == "blort"


def test_EmbeddedMultiLineIF():
    group = St3G("test")
    group.emitDebugStartStopStrings(True)
    main = St3T(group=group, template='$sub$')
    sub = St3T(group=group,
               template=dedent("""\
                    begin
                    $if(foo)$
                    $foo$
                    $else$
                    blort
                    $endif$
                """))
    sub["foo"] = "stuff"
    main["sub"] = sub
    
    assert str(main) == dedent("""\
        begin
        stuff""")

    main = St3T(group=group, template='$sub$')
    sub = sub.getInstanceOf()
    main["sub"] = sub
    
    assert str(main) == dedent("""\
        begin
        blort""")


def test_SimpleIndentOfAttributeList():
    templates = dedent("""\
            group test;
            list(names) ::= <<
              $names; separator="\\n"$
            >>
    """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates),
                 lexer=DefaultTemplateLexer.Lexer,
                 errors=errors)
    t = group.getInstanceOf("list")
    t["names"] = "Terence"
    t["names"] = "Jim"
    t["names"] = "Sriram"
    
    assert str(t) == '  Terence\n  Jim\n  Sriram'


def test_IndentOfMultilineAttributes():
    templates = dedent("""\
            group test;
            list(names) ::= <<
              $names; separator="\\n"$
            >>
    """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates),
                 lexer=DefaultTemplateLexer.Lexer,
                 errors=errors)
    t = group.getInstanceOf("list")
    t["names"] = "Terence\nis\na\nmaniac"
    t["names"] = "Jim"
    t["names"] = "Sriram\nis\ncool"
    
    assert str(t) == '  Terence\n  is\n  a\n  maniac\n  Jim\n  Sriram\n  is\n  cool'


def test_IndentOfMultipleBlankLines():
    """ no indent on blank line """
    templates = dedent("""\
            group test;
            list(names) ::= <<
              $names$
            >>
    """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates),
                 lexer=DefaultTemplateLexer.Lexer,
                 errors=errors)
    t = group.getInstanceOf("list")
    t["names"] = "Terence\n\nis a maniac"
    
    assert str(t) == '  Terence\n\n  is a maniac'


def test_IndentBetweenLeftJustifiedLiterals():
    templates = dedent("""\
            group test;
            list(names) ::= <<
            Before:
              $names; separator="\\n"$
            after
            >>
            """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates), lexer=DefaultTemplateLexer.Lexer, errors=errors)
    t = group.getInstanceOf("list")
    t["names"] = "Terence"
    t["names"] = "Jim"
    t["names"] = "Sriram"
    
    assert str(t) == dedent("""\
            Before:
              Terence
              Jim
              Sriram
            after\
            """)


def test_NestedIndent():
    templates = dedent("""\
            group test;
            method(name,stats) ::= <<
            void $name$() {
            \t$stats; separator="\\n"$
            }
            >>
            ifstat(expr,stats) ::= <<
            if ($expr$) {
              $stats; separator="\\n"$
            }
            >>
            assign(lhs,expr) ::= <<$lhs$=$expr$;>>
            """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates), lexer=DefaultTemplateLexer.Lexer, errors=errors)
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
    
    assert str(t) == dedent("""\
            void foo() {
            \tx=0;
            \tif (x>0) {
            \t  y=x+y;
            \t  z=4;
            \t}
            }\
            """)


class AlternateWriter(StringTemplateWriter):
    def __init__(self):
        super().__init__()
        self.buf = io.StringIO(u'')

    def pushIndentation(self, indent):
        pass

    def popIndentation(self):
        return None

    def pushAnchorPoint(self):
        pass

    def popAnchorPoint(self):
        pass

    def setLineWidth(self, lineWidth):
        pass

    def write(self, a_str, wrap=None):
        """
        if wrap is None: just pass through
        """
        if wrap is None:
            self.buf.write(a_str)
            len(a_str)
        return 0

    def writeWrapSeparator(self, wrap):
        return 0

    def writeSeparator(self, a_str):
        return self.write(a_str)


def test_AlternativeWriter():
    """ Provide an alternative to the default writer """
    group = St3G("test")
    group.defineTemplate(name="bold", template="<b>$x$</b>")
    name = St3T(group=group, template="$name:bold(x=name)$")
    name["name"] = "Terence"
    name.write(AlternateWriter())
    assert  str(name) == "<b>Terence</b>"


def test_ApplyAnonymousTemplateToMapAndSet0():
    st = St3T("$items:{<li>$it$</li>}$")
    m = dict()
    m["a"] = "1"
    m["b"] = "2"
    m["c"] = "3"
    st["items"] = m
    assert str(st) == "<li>1</li><li>2</li><li>3</li>"


def test_ApplyAnonymousTemplateToMapAndSet1():
    st = St3T("$items:{<li>$it$</li>}$")
    m = {"a", "b", "c"}
    st["items"] = m
    split = str(st).split("(</?li>){1,2}")
    assert "" == split[0]
    assert "a" == split[1]
    assert "b" == split[2]
    assert "c" == split[3]


def test_LazyEvalOfSuperInApplySuperTemplateRef():
    """
    This is the same as testApplySuperTemplateRef() test
    except notice that here the supergroup defines page.
    As long as you create the instance via the subgroup, "super." 
    will evaluate lazily
    (i.e., not statically during template compilation)
    to the templates getGroup().superGroup value.
    If I create instance of page in group not subGroup,
    however, I will get an error as superGroup is None for group "group".
    """
    group = St3G("base")
    subGroup = St3G("sub")
    subGroup.superGroup = group
    group.defineTemplate("bold", "<b>$it$</b>")
    subGroup.defineTemplate("bold", "<strong>$it$</strong>")
    group.defineTemplate("page", "$name:super.bold()$")
    st = subGroup.getInstanceOf("page")
    st["name"] = "Ter"
    error = None
    try:
        str(st)

    except IllegalArgumentException as iae:
        assert tsh.getMsg(iae) == "base has no super group; invalid template: super.bold"
    except Exception as ex:
        assert False


def test_ListOfEmbeddedTemplateSeesEnclosingAttributes():
    templates = dedent("""\
            group test;
            output(cond,items) ::= <<page: $items$>>
            my_body() ::= <<$font()$stuff>>
            font() ::= <<$if(cond)$this$else$that$endif$>>
            """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(templates), lexer=DefaultTemplateLexer.Lexer, errors=errors)
    outputST = group.getInstanceOf("output")
    bodyST1 = group.getInstanceOf("my_body")
    bodyST2 = group.getInstanceOf("my_body")
    bodyST3 = group.getInstanceOf("my_body")
    outputST["items"] = bodyST1
    outputST["items"] = bodyST2
    outputST["items"] = bodyST3
    assert str(outputST) == "page: thatstuffthatstuffthatstuff"


def test_InheritArgumentFromRecursiveTemplateApplication():
    """ do not inherit attributes through formal args """
    templates = dedent("""\
            group test;
            "block(stats) ::= "<stats>""
            ifstat(stats) ::= "IF true then <stats>"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("block")
    b["stats"] = group.getInstanceOf("ifstat")
    b["stats"] = group.getInstanceOf("ifstat")

    assert str(b) == "IF True then IF True then "


def test_DeliberateRecursiveTemplateApplication():
    """ This test will cause infinite loop.  
    block contains a stat which contains the same block.
    Must be in lintMode to detect 
    note that attributes doesn't show up in ifstat() because
    recursion detection traps the problem before it writes out the
    infinitely-recursive template; I set the attributes attribute right
    before I render. 
    """
    templates = dedent("""\
            group test;
            block(stats) ::= "<stats>"
            ifstat(stats) ::= "IF True then <stats>"
            """)
    stringtemplate3.lintMode = True
    stringtemplate3.resetTemplateCounter()
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("block")
    ifstat = group.getInstanceOf("ifstat")
    b["stats"] = ifstat  # block has if stat
    ifstat["stats"] = b  # but make "if" contain block
    
    errors = ""
    try:
        result = str(b)
        logger.debug(f"result: {result}")

    except IllegalStateException as ise:
        errors = tsh.getMsg(ise)
    except Exception as e:
        pass

    logger.info("errors=" + errors + "'")
    stringtemplate3.lintMode = False
    assert errors == dedent("""
            infinite recursion to <ifstat([stats])@4> referenced in <block([stats])@3>; stack trace:
            <ifstat([stats])@4>, attributes=[stats=<block()@3>]>
            <block([stats])@3>, attributes=[stats=<ifstat()@4>], references=[stats]>
            <ifstat([stats])@4> (start of recursive cycle)
            "..."
            """)


def test_ImmediateTemplateAsAttributeLoop():
    """ even though block has a stats value that refers to itself, """
    """ there is no recursion because each instance of block hides """
    """ the stats value from above since it's a formal arg. """
    templates = dedent("""\
            group test;
            block(stats) ::= "{<stats>}"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("block")
    b["stats"] = group.getInstanceOf("block")

    assert str(b) == "{{}}"


def test_TemplateGetPropertyGetsAttribute():
    """ This test will cause infinite loop if missing attribute no """
    """ properly caught in getAttribute """
    templates = dedent("""\
            group test;
            Cfile(funcs) ::= <<
            #include <stdio.h>
            <funcs:{public void <it.name>(<it.args>);}; separator="\\n">
            <funcs; separator="\\n">
            >>
            func(name,args,body) ::= <<
            public void <name>(<args>) {<body>}
            >>
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("Cfile")
    f1 = group.getInstanceOf("func")
    f2 = group.getInstanceOf("func")
    f1["name"] = "f"
    f1["args"] = ""
    f1["body"] = "i=1;"
    f2["name"] = "g"
    f2["args"] = "int arg"
    f2["body"] = "y=1;"
    b["funcs"] = f1
    b["funcs"] = f2
    
    assert str(b) == dedent("""
        #include <stdio.h>
        public void f();
        public void g(int arg);
        public void f() {i=1;}
        public void g(int arg) {y=1;}
        """)


class Decl:
    def __init__(self, name, atype):
        self.name = name
        self.type = atype

    def getName(self):
        return self.name

    def getType(self):
        return self.type


def test_ComplicatedIndirectTemplateApplication():
    templates = dedent("""\
            group Java;
            
            file(variables) ::= <<
            <variables:{ v | <v.decl:(v.format)()>}; separator="\\n">
            >>
            intdecl(decl) ::= "int <decl.name> = 0;"
            intarray(decl) ::= "int[] <decl.name> = null;"
            """)
    group = St3G(file=io.StringIO(templates))
    f = group.getInstanceOf("file")
    f.setAttribute("variables.{decl,format}", Decl("i", "int"), "intdecl")
    f.setAttribute("variables.{decl,format}", Decl("a", "int-array"), "intarray")
    logger.info(f"{f=}")
    
    assert str(f) == dedent("""\
    int i = 0;
    int[] a = null;""")

    group = St3G(file=io.StringIO(templates))
    f = group.getInstanceOf("file")
    f["variables.{decl,format}"] = (Decl("i", "int"), "intdecl")
    f["variables.{decl,format}"] = (Decl("a", "int-array"), "intarray")
    logger.info(f"{f=}")

    assert str(f) == dedent("""\
    int i = 0;
    int[] a = null;""")


def test_IndirectTemplateApplication():
    templates = dedent("""\
            group dork;
            
            "test(name) ::= <<"
            <(name)()>
            >>
            first() ::= "the first"
            second() ::= "the second"
            """)
    group = St3G(file=io.StringIO(templates))
    f = group.getInstanceOf("test")
    f["name"] = "first"
    assert str(f) == "the first"


def test_IndirectTemplateWithArgsApplication():
    templates = dedent("""\
            group dork;
            
            test(name) ::= <<
            <(name)(a="foo")>
            >>
            first(a) ::= "the first: <a>"
            second(a) ::= "the second <a>"
            """)
    group = St3G(file=io.StringIO(templates))
    f = group.getInstanceOf("test")
    f["name"] = "first"
    assert str(f) == "the first: foo"


def test_NullIndirectTemplateApplication():
    """ t None be must be defined else error: None attr w/o formal def """
    templates = dedent("""\
            group dork;
            
            test(names,t) ::= <<
            <names:(t)()>
            >>
            ind() ::= "[<it>]"
            """)
    group = St3G(file=io.StringIO(templates))
    f = group.getInstanceOf("test")
    f["names"] = "me"
    f["names"] = "you"
    assert str(f) == ""


def test_NullIndirectTemplate():
    templates = dedent("""\
            group dork;
            
            test(name) ::= <<
            <(name)()>
            >>
            first() ::= "the first"
            second() ::= "the second"
            """)
    group = St3G(file=io.StringIO(templates))
    f = group.getInstanceOf("test")
    # f["name"] = "first"
    assert str(f) == ""


def test_EmbeddedComments():
    st = St3T("Foo $! ignore !$bar")
    assert str(st) == "Foo bar"

    st = St3T(template=dedent("""\
            Foo $! ignore
             and a line break!$
            bar
            """))
    assert str(st) == "Foo bar"

    st = St3T(template=dedent("""\
            $! start of line $ and $! ick
            !$boo
            """))
    assert str(st) == "boo"

    st = St3T(template=dedent("""
        $! start of line !$
        $! another to ignore !$
        $! ick
        !$boo
    """))
    assert str(st) == "boo"

    st = St3T(template=dedent("""\
        $! back !$$! to back !$ // can't detect; leaves \\n
        $! ick
        !$boo
    """))
    assert str(st) == 'boo\n'


def test_EmbeddedCommentsAngleBracketed():
    st = St3T(template="Foo <! ignore !>bar",
              lexer=AngleBracketTemplateLexer.Lexer)
    assert str(st) == "Foo bar"

    st = St3T(template=dedent("""\
            Foo <! ignore
             and a line break!>
            bar"""),
              lexer=AngleBracketTemplateLexer.Lexer
              )
    assert str(st) == "Foo bar"

    st = St3T(template=dedent("""
            <! start of line $ and <! ick
            !>boo"""),
              lexer=AngleBracketTemplateLexer.Lexer
              )
    assert str(st) == "boo"

    st = St3T(template=dedent("""\
        "<! start of line !>"
        "<! another to ignore !>"
        <! ick
        !>boo"""),
              lexer=AngleBracketTemplateLexer.Lexer
              )
    assert str(st) == "boo"

    st = St3T(template=dedent("""\
        <! back !><! to back !> // can't detect; leaves \\n
        <! ick
        !>boo"""),
              lexer=AngleBracketTemplateLexer.Lexer
              )
    assert str(st) == 'boo'


def test_LineBreak():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = St3T(template=dedent("""
              Foo <\\\\>
              \t  bar"""),
              lexer=AngleBracketTemplateLexer.Lexer)
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw))
    assert sw.getvalue() == "Foo bar"


def test_LineBreak2():
    """ expect \n in output
    TODO: use custom auto indent writer
    force \n as newline
    """
    st = St3T(template=dedent("""\
            Foo <\\\\>       
              \t  bar"""),
              lexer=AngleBracketTemplateLexer.Lexer)
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw, newline="\n"))
    assert sw.getvalue() == "Foo bar"


def test_LineBreakNoWhiteSpace():
    """ expect \n in output
    TODO: use custom auto indent writer
    force \n as newline
    """
    st = St3T(template=dedent("""\
            Foo <\\\\>
            bar"""),
              lexer=AngleBracketTemplateLexer.Lexer)
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw, newline="\n"))
    assert sw.getvalue() == "Foo bar"


def test_LineBreakDollar():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = St3T(template=dedent("""\
            Foo $\\\\$
              \t  bar"""),
              lexer=DefaultTemplateLexer.Lexer)
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw, newline="\n"))
    assert sw.getvalue() == "Foo bar"


def test_LineBreakDollar2():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = St3T(template=dedent("""\
            Foo $\\\\$          
              \t  bar"""),
              lexer=DefaultTemplateLexer.Lexer)
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw, newline="\n"))
    assert sw.getvalue() == "Foo bar"


def test_LineBreakNoWhiteSpaceDollar():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = St3T(template=dedent("""
            Foo $\\\\$
            bar"""),
              lexer=DefaultTemplateLexer.Lexer)
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw, newline="\n"))
    assert sw.getvalue() == "Foo bar"


def test_CharLiterals():
    """ expect \n in output
    TODO: use custom auto indent writer
    force \n as newline
    """
    st = St3T(template=dedent("""\
            Foo <\\r\\n> <\\n> <\\t> bar"""),
              lexer=AngleBracketTemplateLexer.Lexer)
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw))
    assert sw.getvalue() == "Foo \r\n \n \t bar"

    st = St3T(template=dedent("""\
            Foo $\\n$$\\t$ bar"""))
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw))
    assert sw.getvalue() == "Foo \n\t bar"

    st = St3T(template="Foo$\\ $bar$\\n$")
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw))
    assert sw.getvalue() == "Foo bar\n"


def test_NewlineNormalizationInTemplateString():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = St3T(template=dedent("""\
            Foo\r
            Bar
            """),
              lexer=AngleBracketTemplateLexer.Lexer
              )
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw, "\n"))
    assert sw.getvalue() == "Foo\nbar\n"


def test_NewlineNormalizationInTemplateStringPC():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = St3T(template=dedent("""\
            Foo\r
            Bar
            """),
              lexer=AngleBracketTemplateLexer.Lexer)
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw, "\r\n"))
    assert sw.getvalue() == "Foo\r\nBar\r\n"


def test_NewlineNormalizationInAttribute():
    """ expect \n in output
    TODO: use custom auto indent writer
    """
    st = St3T(template=dedent("""\
            Foo\r
            <name>"""),
              lexer=AngleBracketTemplateLexer.Lexer)
    st["name"] = "a\nb\r\nc"
    sw = io.StringIO(u'')
    st.write(AutoIndentWriter(sw, newline="\n"))
    assert sw.getvalue() == "Foo\na\nb\nc"


def test_UnicodeLiterals():
    st = St3T(template='Foo <\\uFEA5\\n\\u00C2> bar',
              lexer=AngleBracketTemplateLexer.Lexer)
    assert str(st) == "Foo \ufea5\n\u00C2 bar"

    st = St3T(template='Foo $\\uFEA5\\n\\u00C2$ bar\n')
    assert str(st) == "Foo \ufea5\n\u00C2 bar\n"

    st = St3T("Foo$\\ $bar$\\n$")
    assert str(st) == "Foo bar\n"


def test_MissingIteratedConditionalValueGetsNOSeparator():
    """ empty conditional values get no separator """
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group, template='$users:{$if(it.ok)$$it.name$$endif$}; separator=","$')
    t["users.{name,ok}"] = "Terence", True
    t["users.{name,ok}"] = "Tom", False
    t["users.{name,ok}"] = "Frank", True
    t["users.{name,ok}"] = "Johnny", False
    assert str(t) == "Terence,Frank"


def test_MissingIteratedConditionalValueGetsNOSeparator2():
    """ empty conditional values get no separator """
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group, template='$users:{$if(it.ok)$$it.name$$endif$}; separator=","$')
    t["users.{name,ok}"] = "Terence", True
    t["users.{name,ok}"] = "Tom", False
    t["users.{name,ok}"] = "Frank", False
    t["users.{name,ok}"] = "Johnny", False
    assert str(t) == "Terence"


def test_MissingIteratedDoubleConditionalValueGetsNOSeparator():
    """ empty conditional values get no separator """
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group,
             template='$users:{$if(it.ok)$$it.name$$endif$$if(it.ok)$$it.name$$endif$}; separator=","$')
    t["users.{name,ok}"] = "Terence", False
    t["users.{name,ok}"] = "Tom", True
    t["users.{name,ok}"] = "Frank", True
    t["users.{name,ok}"] = "Johnny", True
    assert str(t) == "TomTom,FrankFrank,JohnnyJohnny"


def test_IteratedConditionalWithEmptyElseValueGetsSeparator():
    """ empty conditional values get no separator """
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group,
             template='$users:{$if(it.ok)$$it.name$$else$$endif$}; separator=","$')
    t["users.{name,ok}"] = "Terence", True
    t["users.{name,ok}"] = "Tom", False
    t["users.{name,ok}"] = "Frank", True
    t["users.{name,ok}"] = "Johnny", False
    assert str(t) == "Terence,,Frank,"


def test_WhiteSpaceAtEndOfTemplate():
    """ users.list references row.st which has a single blank line at the end. 
    I.e., there are 2 \n in a row at the end 
    ST should eat all whitespace at end """
    group = St3G("group")
    pageST = group.getInstanceOf("org/antlr/stringtemplate/test/page")
    listST = group.getInstanceOf("org/antlr/stringtemplate/test/users_list")
    listST["users"] = Connector()
    listST["users"] = Connector2()
    pageST["title"] = "some title"
    pageST["body"] = listST
    
    assert str(pageST) == dedent("""some title
        "Terence parrt@jguru.comTom tombu@jguru.com"
        """)


class Duh:
    def users(self):
        return []


def test_SizeZeroButNonNullListGetsNoOutput():
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group,
             template="""
        begin
        $duh.users:{name: $it$}; separator=", "$
        end""")
    t["duh"] = Duh()
    assert str(t) == "beginend"


def test_NullListGetsNoOutput():
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group,
             template="""
        begin
        $users:{name: $it$}; separator=", "$
        end""")
    # t["users"] = Duh()
    assert str(t) == "beginend"


def test_EmptyListGetsNoOutput():
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group,
             template="""
        begin
        $users:{name: $it$}; separator=", "$
        end""")
    t["users"] = list()
    assert str(t) == "beginend"


def test_EmptyListNoIteratorGetsNoOutput():
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group,
             template="""
        begin
        $users; separator=", "$
        end""")
    t["users"] = list()
    assert str(t) == "beginend"


def test_EmptyExprAsFirstLineGetsNoOutput():
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    group.defineTemplate("bold", "<b>$it$</b>")
    t = St3T(group=group,
             template="""
        $users$
        end""")
    assert str(t) == "end"


def test_SizeZeroOnLineByItselfGetsNoOutput():
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group,
             template=dedent("""\
        begin
        $name$
        $users:{name: $it$}$
        $users:{name: $it$}; separator=", "$
        end"""))
    assert str(t) == "beginend"


def test_SizeZeroOnLineWithIndentGetsNoOutput():
    group = St3G("test")
    errors = ErrorBuffer()
    group.errorListener = errors
    t = St3T(group=group,
             template=dedent("""\
                        begin
                            $name$
                        $users:{name: $it$}$
                        $users:{name: $it$$\\n$}$
                    end"""))
    assert str(t) == "beginend"


def test_NonNullButEmptyIteratorTestsFalse():
    group = St3G("test")
    t = St3T(group=group,
             template="""
                    $if(users)$
                    Users: $users:{$it.name$ }$
                    $endif$
                    """)
    t["users"] = list()
    assert str(t) == ""


def test_DoNotInheritAttributesThroughFormalArgs():
    """ name is not visible in stat because of the formal arg called name. 
    somehow, it must be set. """
    templates = dedent("""\
            group test;
            method(name) ::= "<stat()>"
            stat(name) ::= "x=y   # <name>"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    assert str(b) == "x=y   # "


def test_ArgEvaluationContext():
    """ attribute name is not visible in stat because of the formal 
    arg called name in template stat.  However, we can set its value
    with an explicit name=name.  This looks weird, but makes total
    sense as the rhs is evaluated in the context of method and the lhs
    is evaluated in the context of stat's arg list. """
    templates = dedent("""\
            group test;
            method(name) ::= "<stat(name=name)>"
            stat(name) ::= "x=y   # <name>"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    assert str(b) == "x=y   # foo"


def test_PassThroughAttributes():
    templates = dedent("""\
            group test;
            method(name) ::= "<stat(...)>"
            stat(name) ::= "x=y   # <name>"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    assert str(b) == "x=y   # foo"


def test_PassThroughAttributes2():
    templates = dedent("""\
            group test;
            method(name) ::= <<
            <stat(value="34",...)>
            >>
            stat(name,value) ::= "x=<value>   # <name>"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    assert str(b) == "x=34   # foo"


def test_DefaultArgument():
    templates = dedent("""\
            group test;
            method(name) ::= <<
            <stat(...)>
            >>
            stat(name,value="99") ::= "x=<value>   # <name>"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    assert str(b) == "x=99   # foo"


def test_DefaultArgument2():
    templates = dedent("""\
            group test;
            stat(name,value="99") ::= "x=<value>   # <name>"
    """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("stat")
    b["name"] = "foo"
    assert str(b) == "x=99   # foo"


class Field:
    def __init__(self):
        self.name = "parrt"
        self.n = 0

    def str(self):
        return "Field"


def test_DefaultArgumentManuallySet():
    templates = dedent("""\
            group test;
            method(fields) ::= <<
            <fields:{f | <stat(f=f)>}>
            >>
            stat(f,value={<f.name>}) ::= "x=<value>   # <f.name>"
            """)
    group = St3G(file=io.StringIO(templates))
    m = group.getInstanceOf("method")
    m["fields"] = Field()
    assert str(m) == "x=parrt   # parrt"


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
    templates = dedent("""\
            group test;
            method(fields) ::= <<
            <fields:{f | <stat(...)>}>
            >>
            stat(f,value={<f.name>}) ::= "x=<value>   # <f.name>"
            """)
    group = St3G(file=io.StringIO(templates))
    m = group.getInstanceOf("method")
    m["fields"] = Field()
    assert str(m) == "x=parrt   # parrt"


def test_DefaultArgumentImplicitlySet2():
    templates = dedent("""\
            group test;
            method(fields) ::= <<
            <fields:{f | <f:stat()>}>  // THIS SHOULD BE ERROR; >1 arg?
            >>
            stat(f,value={<f.name>}) ::= "x=<value>   # <f.name>"
            """)
    group = St3G(file=io.StringIO(templates))
    m = group.getInstanceOf("method")
    m["fields"] = Field()
    assert str(m) == "x=parrt   # parrt"


def test_DefaultArgumentAsTemplate():
    templates = dedent("""\
            group test;
            method(name,size) ::= <<
            <stat(...)>
            >>
            stat(name,value={<name>}) ::= "x=<value>   # <name>"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    b["size"] = "2"
    assert str(b) == "x=foo   # foo"


def test_DefaultArgumentAsTemplate2():
    templates = dedent("""\
            group test;
            method(name,size) ::= <<
            <stat(...)>
            >>
            stat(name,value={ [<name>] }) ::= "x=<value>   # <name>"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    b["size"] = "2"
    assert str(b) == "x= [foo]    # foo"


def test_DoNotUseDefaultArgument():
    templates = dedent("""\
            group test;
            method(name) ::= <<
            <stat(value="34",...)>
            >>
            stat(name,value="99") ::= "x=<value>   # <name>"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    assert str(b) == "x=34   # foo"


class Counter:
    def __init__(self):
        self.n = 0

    def str(self):
        self.n += 1
        return f"{self.n}"


def test_DefaultArgumentInParensToEvalEarly():
    templates = dedent("""\
            group test;
            A(x) ::= "<B()>"
            B(y={<(x)>}) ::= "<y> <x> <x> <y>"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("A")
    b["x"] = Counter()
    assert str(b) == "0 1 2 0"


def test_ArgumentsAsTemplates():
    templates = dedent("""\
            group test;
            method(name,size) ::= <<
            <stat(value={<size>})>
            >>
            stat(value) ::= "x=<value>;"
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    b["size"] = "34"
    assert str(b) == "x=34;"


def test_TemplateArgumentEvaluatedInSurroundingContext():
    templates = dedent("""\
            group test;
            file(m,size) ::= "<m>"
            method(name) ::= <<
            <stat(value={<size>.0})>
            >>
            stat(value) ::= "x=<value>;"
            """)
    group = St3G(file=io.StringIO(templates))
    f = group.getInstanceOf("file")
    f["size"] = "34"
    m = group.getInstanceOf("method")
    m["name"] = "foo"
    f["m"] = m
    assert str(m) == "x=34.0;"


def test_ArgumentsAsTemplatesDefaultDelimiters():
    templates = dedent("""\
            group test;
            method(name,size) ::= <<
            $stat(value={$size$})$
            >>
            stat(value) ::= "x=$value$;"
            """)
    group = St3G(file=io.StringIO(templates), lexer=DefaultTemplateLexer.Lexer)
    b = group.getInstanceOf("method")
    b["name"] = "foo"
    b["size"] = "34"
    assert str(b) == "x=34;"


def test_DefaultArgsWhenNotInvoked():
    templates = dedent("""\
            group test;
            b(name="foo") ::= ".<name>."
            """)
    group = St3G(file=io.StringIO(templates))
    b = group.getInstanceOf("b")
    assert str(b) == ".foo."


def test_Map():
    template = dedent("""
            group test;
            typeInit ::= ["int":"0", "float":"0.0"]
            var(type,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "int"
    st["name"] = "x"
    assert str(st) == "int x = 0;"


def test_MapValuesAreTemplates():
    template = dedent("""
            group test;
            typeInit ::= ["int":"0<w>", "float":"0.0<w>"]
            var(type,w,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(template))
    st = group.getInstanceOf("var")
    st["w"] = "L"
    st["type"] = "int"
    st["name"] = "x"
    assert str(st) == "int x = 0L;"


def test_MapKeyLookupViaTemplate():
    """ ST doesn't do a toString on .(key) values, it just uses the value 
    of key rather than key itself as the key.  But, if you compute a 
    key via a template """
    template = dedent("""
            group test;
            typeInit ::= ["int":"0<w>", "float":"0.0<w>"]
            var(type,w,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(template))
    st = group.getInstanceOf("var")
    st["w"] = "L"
    st["type"] = St3T("int")
    st["name"] = "x"
    assert str(st) == "int x = 0L;"


def test_MapMissingDefaultValueIsEmpty():
    template = dedent("""
            group test;
            typeInit ::= ["int":"0", "float":"0.0"]
            var(type,w,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(template))
    st = group.getInstanceOf("var")
    st["w"] = "L"
    st["type"] = "double"  # double not in typeInit map
    st["name"] = "x"
    assert str(st) == "double x = ;"  # weird, but tests default value is key


def test_MapHiddenByFormalArg():
    template = dedent("""
            group test;
            typeInit ::= ["int":"0", "float":"0.0"]
            var(typeInit,type,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "int"
    st["name"] = "x"
    assert str(st) == "int x = ;"


def test_MapEmptyValueAndAngleBracketStrings():
    template = dedent("""
            group test;
            typeInit ::= ["int":"0", "float":, "double":<<0.0L>>]
            var(type,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "float"
    st["name"] = "x"
    assert str(st) == "float x = ;"


def test_MapDefaultValue():
    template = dedent("""
            group test;
            typeInit ::= ["int":"0", default:"None"]
            var(type,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "UserRecord"
    st["name"] = "x"
    assert str(st) == "UserRecord x = None;"


def test_MapEmptyDefaultValue():
    template = dedent("""
            group test;
            typeInit ::= ["int":"0", default:]
            var(type,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "UserRecord"
    st["name"] = "x"
    assert str(st) == "UserRecord x = ;"


def test_MapDefaultValueIsKey():
    template = dedent("""
            group test;
            typeInit ::= ["int":"0", default:key]
            var(type,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(template))
    st = group.getInstanceOf("var")
    st["type"] = "UserRecord"
    st["name"] = "x"
    assert str(st) == "UserRecord x = UserRecord;"


def test_MapDefaultStringAsKey():
    """ 
    Test that a map can have only the default entry.
     * <p>
     * Bug ref: JIRA bug ST-15 (Fixed)
    """
    templates = dedent("""\
            group test;
            typeInit ::= ["default":"foo"] 
            var(type,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(templates))
    st = group.getInstanceOf("var")
    st["type"] = "default"
    st["name"] = "x"
    assert str(st) == "default x = foo;"


def test_MapDefaultIsDefaultString():
    """  Test that a map can return a <b>string</b> with the word: default.
     * <p>
     * Bug ref: JIRA bug ST-15 (Fixed)
     """
    templates = dedent("""\
            group test;
            map ::= [default: "default"] 
            t1() ::= "<map.(1)>" 
            """)
    group = St3G(file=io.StringIO(templates))
    st = group.getInstanceOf("t1")
    assert str(st) == "default"


def test_MapViaEnclosingTemplates():
    template = dedent("""
            group test;
            typeInit ::= ["int":"0", "float":"0.0"]
            intermediate(type,name) ::= "<var(...)>"
            var(type,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(template))
    st = group.getInstanceOf("intermediate")
    st["type"] = "int"
    st["name"] = "x"
    assert str(st) == "int x = 0;"


def test_MapViaEnclosingTemplates2():
    template = dedent("""
            group test;
            typeInit ::= ["int":"0", "float":"0.0"]
            intermediate(stuff) ::= "<stuff>"
            var(type,name) ::= "<type> <name> = <typeInit.(type)>;"
            """)
    group = St3G(file=io.StringIO(template))
    intermediate = group.getInstanceOf("intermediate")
    var = group.getInstanceOf("var")
    var["type"] = "int"
    var["name"] = "x"
    intermediate["stuff"] = var
    assert str(intermediate) == "int x = 0;"


def test_EmptyGroupTemplate():
    template = dedent("""
            group test;
            foo() ::= ""
            """)
    group = St3G(file=io.StringIO(template))
    a = group.getInstanceOf("foo")
    assert str(a) == ""


def test_EmptyStringAndEmptyAnonTemplateAsParameterUsingAngleBracketLexer():
    template = dedent("""
            group test;
            top() ::= <<<x(a="", b={})\\>>>
            x(a,b) ::= "a=<a>, b=<b>"
            """)
    group = St3G(file=io.StringIO(template))
    a = group.getInstanceOf("top")
    assert str(a) == "a=, b="


def test_EmptyStringAndEmptyAnonTemplateAsParameterUsingDollarLexer():
    template = dedent("""
            group test;
            top() ::= <<$x(a="", b={})$>>
            x(a,b) ::= "a=$a$, b=$b$"
            """)
    group = St3G(file=io.StringIO(template), lexer=DefaultTemplateLexer.Lexer)
    a = group.getInstanceOf("top")
    assert str(a) == "a=, b="


def test_TruncOp():
    e = St3T("$trunc(names); separator=", "$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    assert str(e) == "Ter, Tom"



def test_ReUseOfRestResult():
    template = dedent("""
        group test;
        a(names) ::= "<b(rest(names))>"
        b(x) ::= "<x>, <x>"
        """)
    group = St3G(file=io.StringIO(template))
    e = group.getInstanceOf("a")
    names = ["Ter", "Tom"]
    e["names"] = names
    assert str(e) == "Tom, Tom"


def test_ReUseOfCat():
    template = dedent("""
        group test;
        a(mine,yours) ::= "<b([mine,yours])>"
        b(x) ::= "<x>, <x>"
        """)
    group = St3G(file=io.StringIO(template))
    e = group.getInstanceOf("a")
    mine = ["Ter", "Tom"]
    e["mine"] = mine
    yours = ["Foo"]
    e["yours"] = yours
    assert str(e) == "TerTomFoo, TerTomFoo"


def test_RepeatedRestOpAsArg():
    """ FIXME: BUG! Iterator is not reset from first to second $x$
     *  Either reset the iterator or pass an attribute that knows to get
     *  the iterator each time.  Seems like first, tail do not
     *  have same problem as they yield objects.
     *
     *  Maybe make a RestIterator like I have CatIterator."""
    template = dedent("""
            group test;
            root(names) ::= "$other(rest(names))$"
            other(x) ::= "$x$, $x$"
            """)
    group = St3G(file=io.StringIO(template), lexer=DefaultTemplateLexer.Lexer)
    e = group.getInstanceOf("root")
    e["names"] = "Ter"
    e["names"] = "Tom"
    assert str(e) == "Tom, Tom"


def test_MultipleRefsToListAttribute():
    template = dedent("""
            group test;
            f(x) ::= "<x> <x>"
            """)
    group = St3G(file=io.StringIO(template))
    e = group.getInstanceOf("f")
    e["x"] = "Ter"
    e["x"] = "Tom"
    assert str(e) == "TerTom TerTom"


def test_ApplyTemplateWithSingleFormalArgs():
    template = dedent("""
            group test;
            test(names) ::= <<<names:bold(item=it); separator=", "> >>
            bold(item) ::= <<*<item>*>>
            """)
    group = St3G(file=io.StringIO(template))
    e = group.getInstanceOf("test")
    e["names"] = "Ter"
    e["names"] = "Tom"
    assert str(e) == "*Ter*, *Tom* "


def test_ApplyTemplateWithNoFormalArgs():
    template = dedent("""
            group test;
            test(names) ::= <<<names:bold(); separator=", "> >>
            bold() ::= <<*<it>*>>
            """)
    group = St3G(file=io.StringIO(template), lexer=AngleBracketTemplateLexer.Lexer)
    e = group.getInstanceOf("test")
    e["names"] = "Ter"
    e["names"] = "Tom"
    assert str(e) == "*Ter*, *Tom* "


def test_AnonTemplateWithArgHasNoITArg():
    e = St3T("$names:{n| $n$:$it$}; separator=", "$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    error = None
    try:
        str(e)

    except KeyError as nse:
        error = tsh.getMsg(nse)

    assert error == "'no such attribute: it in template context [anonymous anonymous]'"


def test_FirstWithListOfMaps2():
    """ this FAILS! """
    e = St3T("$first(maps):{ m | $m.Ter$ }$")
    m1 = {"Ter": "x5707"}
    m2 = {"Tom": "x5332"}

    e["maps"] = m1
    e["maps"] = m2
    assert str(e) == "x5707"

    e = e.getInstanceOf()
    alist = [m1, m2]
    e["maps"] = alist
    assert str(e) == "x5707"


def test_CatWithTemplateApplicationAsElement():
    e = St3T("$[names:{$it$!},phones]; separator=", "$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    assert str(e) == "Ter!, Tom!, 1, 2"

def test_CatWithNullTemplateApplicationAsElement():
    e = St3T(template='$[names:{$it$!},"foo"]:{x}; separator=", "$')
    e = e.getInstanceOf()
    e["phones"] = "1"
    e["phones"] = "2"
    assert str(e) == "x"  # only one since template application gives nothing


def test_CatWithNestedTemplateApplicationAsElement():
    e = St3T(template='$[names, ["foo","bar"]:{$it$!},phones]; separator=", "$')
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    assert str(e) == "Ter, Tom, foo!, bar!, 1, 2"


def test_ListAsTemplateArgument():
    template = dedent("""
                group test;
                test(names,phones) ::= "<foo([names,phones])>"
                foo(items) ::= "<items:{a | *<a>*}>"
                """)
    group = St3G(file=io.StringIO(template), lexer=AngleBracketTemplateLexer.Lexer)
    e = group.getInstanceOf("test")
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    assert str(e) == "*Ter**Tom**1**2*"


def test_SingleExprTemplateArgument():
    template = dedent("""
            group test;
            test(name) ::= "<bold(name)>"
            bold(item) ::= "*<item>*"
            """)
    group = St3G(file=io.StringIO(template), lexer=AngleBracketTemplateLexer.Lexer)
    e = group.getInstanceOf("test")
    e["name"] = "Ter"
    assert str(e) == "*Ter*"


def test_SingleExprTemplateArgumentInApply():
    """ when you specify a single arg on a template application
    it overrides the setting of the iterated value "it" to that
    same single formal arg.  Your arg hides the implicitly set "it". """
    template = dedent("""
            group test;
            test(names,x) ::= "<names:bold(x)>"
            bold(item) ::= "*<item>*"
            """)
    group = St3G(file=io.StringIO(template), lexer=AngleBracketTemplateLexer.Lexer)
    e = group.getInstanceOf("test")
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["x"] = "ick"
    assert str(e) == "*ick**ick*"


def test_SoleFormalTemplateArgumentInMultiApply():
    template = dedent("""
            group test;
            test(names) ::= "<names:bold(),italics()>"
            bold(x) ::= "*<x>*"
            italics(y) ::= "_<y>_"
            """)
    group = St3G(file=io.StringIO(template),
                 lexer=AngleBracketTemplateLexer.Lexer)
    e = group.getInstanceOf("test")
    e["names"] = "Ter"
    e["names"] = "Tom"
    assert str(e) == "*Ter*_Tom_"


def test_SingleExprTemplateArgumentError():
    template = dedent("""
            group test;
            test(name) ::= "<bold(name)>"
            bold(item,ick) ::= "*<item>*"
            """)
    errors = ErrorBuffer()
    group = St3G(file=io.StringIO(template),
                 lexer=AngleBracketTemplateLexer.Lexer, errors=errors)
    e = group.getInstanceOf("test")
    e["name"] = "Ter"
    result = str(e)
    logger.debug(f'result: {result}')
    assert str(errors) == \
           "template bold must have exactly one formal arg in template context" \
           "[test <invoke bold arg context>]"


def test_InvokeIndirectTemplateWithSingleFormalArgs():
    template = dedent("""
            group test;
            test(templateName,arg) ::= "<(templateName)(arg)>"
            bold(x) ::= <<*<x>*>>
            italics(y) ::= <<_<y>_>>
            """)
    group = St3G(file=io.StringIO(template))
    e = group.getInstanceOf("test")
    e["templateName"] = "italics"
    e["arg"] = "Ter"
    assert str(e) == "_Ter_"


def test_ParallelAttributeIteration():
    e = St3T("$names,phones,salaries:{n,p,s | $n$@$p$: $s$\\n}$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    e["salaries"] = "big"
    e["salaries"] = "huge"
    assert str(e) == "Ter@1: bigTom@2: huge"


def test_ParallelAttributeIterationWithNullValue():
    e = St3T("$names,phones,salaries:{n,p,s | $n$@$p$: $s$\\n}$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    e["phones"] = ["1", None, "3"]
    e["salaries"] = "big"
    e["salaries"] = "huge"
    e["salaries"] = "enormous"

    assert str(e) == dedent("""\
        Ter@1: big
        Tom@: huge
        Sriram@3: enormous""")


def test_ParallelAttributeIterationHasI():
    e = St3T("$names,phones,salaries:{n,p,s | $i0$. $n$@$p$: $s$\\n}$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    e["salaries"] = "big"
    e["salaries"] = "huge"
    assert str(e) == "0. Ter@1: big1. Tom@2: huge"


def test_ParallelAttributeIterationWithMismatchArgListSizes():
    errors = ErrorBuffer()
    e = St3T("""$names,phones,salaries:{n,p | $n$@$p$}; separator=", "$""")
    e.errorListener = errors
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    e["salaries"] = "big"
    assert str(e) == "Ter@1, Tom@2"

    assert str(errors) == "'number of arguments [n, p] mismatch between attribute list and "\
                          "anonymous template in context [anonymous]'"


def test_ParallelAttributeIterationWithDifferentSizesTemplateRefInsideToo():
    template = dedent("""
            group test;
            page(names,phones,salaries) ::=
                <<$names,phones,salaries:{n,p,s | $value(n)$@$value(p)$: $value(s)$}; separator=", "$>>
            value(x="n/a") ::= "$x$"
            """)
    group = St3G(file=io.StringIO(template),
                 lexer=DefaultTemplateLexer.Lexer)
    p = group.getInstanceOf("page")
    p["names"] = "Ter"
    p["names"] = "Tom"
    p["names"] = "Sriram"
    p["phones"] = "1"
    p["phones"] = "2"
    p["salaries"] = "big"
    assert str(p) == "Ter@1: big, Tom@2: n/a, Sriram@n/a: n/a"



def test_OverrideThroughConditional():
    template = dedent("""
        group base;
        "body(ick) ::= "<if(ick)>ick<f()><else><f()><endif>""
        f() ::= "foo"
        """)
    group = St3G(file=io.StringIO(template))
    templates2 = dedent("""
            group sub;
            f() ::= "bar"
        """)
    subgroup = St3G(file=io.StringIO(templates2),
                    lexer=AngleBracketTemplateLexer.Lexer,
                    superGroup=group)

    b = subgroup.getInstanceOf("body")
    assert str(b) == "bar"


class NonPublicProperty:
    pass


def test_IndexVar():
    group = St3G("dummy", ".")
    t = St3T(group=group, template='$A:{$i$. $it$}; separator="\\n"$')
    t["A"] = "parrt"
    t["A"] = "tombu"

    assert str(t) == dedent("""
        1. parrt
        2. tombu
    """)


def test_Index0Var():
    group = St3G("dummy", ".")
    t = St3T(group=group, template='$A:{$i0$. $it$}; separator="\\n"$')
    t["A"] = "parrt"
    t["A"] = "tombu"

    assert str(t) == dedent("""
        0. parrt
        1. tombu
    """)


def test_IndexVarWithMultipleExprs():
    group = St3G("dummy", ".")
    t = St3T(group=group, template='$A,B:{a,b|$i$. $a$@$b$}; separator="\\n"$')
    t["A"] = "parrt"
    t["A"] = "tombu"
    t["B"] = "x5707"
    t["B"] = "x5000"

    assert str(t) == dedent("""
        1. parrt@x5707
        2. tombu@x5000
    """)


def test_Index0VarWithMultipleExprs():
    group = St3G("dummy", ".")
    t = St3T(group=group, template='$A,B:{a,b|$i0$. $a$@$b$}; separator="\\n"$')
    t["A"] = "parrt"
    t["A"] = "tombu"
    t["B"] = "x5707"
    t["B"] = "x5000"

    assert str(t) == dedent("""
        0. parrt@x5707
        "1. tombu@x5000"
    """)


def test_NoDotsInAttributeNames():
    group = St3G("dummy", ".")
    t = St3T(group=group, template='$user.Name$')
    error = None
    try:
        t["user.Name"] = "Kunle"

    except IllegalArgumentException as iae:
        error = tsh.getMsg(iae)

    assert error == "'cannot have '.' in attribute names'"


def test_NoDotsInTemplateNames():
    errors = ErrorBuffer()
    templates = dedent("""\
            group test;
            a.b() ::= <<foo>>
            """)
    group = St3G(file=io.StringIO(templates),
                 lexer=DefaultTemplateLexer.Lexer,
                 errors=errors)
    logger.debug(f'group: {group!s}')
    assert str(errors).startswith("template group parse error: line 2:1: unexpected token:")


def test_LineWrap():
    templates = dedent("""\
            group test;
            array(values) ::= <<int[] a = { <values; wrap="\\n", separator=","> };>>
    """)
    group = St3G(file=io.StringIO(templates))

    a = group.getInstanceOf("array")
    a["values"] = [3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 2, 1, 6, 32, 5, 6, 77,
                   4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 6, 32, 5, 6, 77,
                   3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 1, 6, 32, 5]

    assert a.toString(40) == dedent("""
        int[] a = { 3,9,20,2,1,4,6,32,5,6,77,888,
        2,1,6,32,5,6,77,4,9,20,2,1,4,63,9,20,2,1,
        4,6,32,5,6,77,6,32,5,6,77,3,9,20,2,1,4,6,
        32,5,6,77,888,1,6,32,5 };"
    """)


def test_LineWrapWithNormalizedNewlines():
    templates = dedent("""\
            group test;
            array(values) ::= <<int[] a = { <values; wrap="\\r\\n", separator=","> };>>
    """)
    group = St3G(file=io.StringIO(templates))

    a = group.getInstanceOf("array")
    a["values"] = [3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 2, 1, 6, 32, 5, 6, 77,
                   4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 6, 32, 5, 6, 77,
                   3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 1, 6, 32, 5]
    sw = io.StringIO(u'')
    stw = AutoIndentWriter(sw, newline='\n')
    stw.setLineWidth(40)
    a.write(stw)
    assert sw.getvalue() == dedent("""\
            [ 3,9,20,2,1,4,6,32,5,6,77,888,
            2,1,6,32,5,6,77,4,9,20,2,1,4,63,9,20,2,1,
            4,6,32,5,6,77,6,32,5,6,77,3,9,20,2,1,4,6,
            32,5,6,77,888,1,6,32,5 ]""")


def test_LineWrapAnchored():
    template = dedent("""
            group test;
            array(values) ::= <<int[] a = { <values; anchor, wrap="\\n", separator=","> };>>
            """)
    group = St3G(file=io.StringIO(template))

    a = group.getInstanceOf("array")
    a["values"] = [3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 2, 1, 6, 32, 5, 6, 77,
                   4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 6, 32, 5, 6, 77,
                   3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 1, 6, 32, 5]

    assert str(a) == dedent("""[3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888,
                 2, 1, 6, 32, 5, 6, 77, 4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1,
                 4, 6, 32, 5, 6, 77, 6, 32, 5, 6, 77, 3, 9, 20, 2, 1, 4, 6,
                 32, 5, 6, 77, 888, 1, 6, 32, 5]""")


def test_SubtemplatesAnchorToo():
    templates = dedent("""\
            group test;
            array(values) ::= <<{ <values; anchor, separator=", "> }>>
    """)
    group = St3G(file=io.StringIO(templates))

    x = St3T(group=group, template='<\\n>{ <stuff; anchor, separator=",\\n"> }<\\n>')
    x["stuff"] = "1"
    x["stuff"] = "2"
    x["stuff"] = "3"
    a = group.getInstanceOf("array")
    a["values"] = ["a", x, "b"]

    assert str(a) == dedent("""
        { a, 
          { 1,
            2,
            3 }
          , b }
        """)


def test_FortranLineWrap():
    template = dedent("""
            group test;
            func(args) ::= <<       FUNCTION line( <args; wrap="\\n      c", separator=","> )>>
            """)
    group = St3G(file=io.StringIO(template))

    a = group.getInstanceOf("func")
    a["args"] = ["a", "b", "c", "d", "e", "f"]

    assert a.toString(30) == dedent("""
               FUNCTION line( a,b,c,d,
              ce,f )
                  """)


def test_LineWrapWithDiffAnchor():
    template = dedent("""
            group test;
            array(values) ::= <<int[] a = { <{1,9,2,<values; wrap, separator=",">}; anchor> };>>
            """)
    group = St3G(file=io.StringIO(template))

    a = group.getInstanceOf("array")
    a["values"] = [3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 2, 1, 6, 32, 5, 6, 77,
                   4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1, 4, 6]

    assert a.toString(30) == dedent("""
        int[] a = { 1,9,2,3,9,20,2,1,4,
                    6,32,5,6,77,888,2,
                    1,6,32,5,6,77,4,9,
                    20,2,1,4,63,9,20,2,
                    1,4,6 };
    """)


def test_LineWrapEdgeCase():
    """ lineWidth==3 implies that we can have 3 characters at most """
    template = dedent("""
            group test;
            duh(chars) ::= <<<chars; wrap="\\n"\\>>>
            """)
    group = St3G(file=io.StringIO(template))

    a = group.getInstanceOf("duh")
    a["chars"] = ["a", "b", "c", "d", "e"]

    assert str(a) == dedent("""
        abc
        de
    """)


def test_LineWrapLastCharIsNewline():
    """ don't do \n if it's last element anyway """
    template = dedent("""
            group test;
            duh(chars) ::= <<<chars; wrap="\\n"\\>>>
            """)
    group = St3G(file=io.StringIO(template))

    a = group.getInstanceOf("duh")
    a["chars"] = ["a", "b", "", "d", "e"]

    assert a.toString(3) == dedent("""
        ab
        de
        """)


def test_LineWrapCharAfterWrapIsNewline():
    """ Once we wrap, we must dump chars as we see them.
    A newline right after a wrap is just an "unfortunate" event.
    People will expect a newline if it's in the data. """
    template = dedent("""
            group test;
            duh(chars) ::= <<<chars; wrap="\\n"\\>>>
            """)
    group = St3G(file=io.StringIO(template))

    a = group.getInstanceOf("duh")
    a["chars"] = ["a", "b", "c", "", "d", "e"]

    assert str(a) == dedent("""
        abc
        
        de
     """)


def test_LineWrapForAnonTemplate():
    """ width=9 is the 3 char; don't break til after ']' """
    template = dedent("""
            group test;
            duh(data) ::= <<!<data:{v|[<v>]}; wrap>!>>
            """)
    group = St3G(file=io.StringIO(template))
    a = group.getInstanceOf("duh")
    a["data"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    assert a.toString(9) == dedent("""
        ![1][2][3] 
        [4][5][6]
        [7][8][9]!
     """)


def test_LineWrapForAnonTemplateAnchored():
    template = dedent("""
            group test;
            duh(data) ::= <<!<data:{v|[<v>]}; anchor, wrap>!>>
    """)
    group = St3G(file=io.StringIO(template))
    a = group.getInstanceOf("duh")
    a["data"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    assert a.toString(9) == dedent("""
        ![1][2][3]
         [4][5][6]
         [7][8][9]!
     """)


def test_LineWrapForAnonTemplateComplicatedWrap():
    template = dedent("""
            group test;
            "top(s) ::= <<  <s>.>>"
            str(data) ::= <<!<data:{v|[<v>]}; wrap="!+\\n!">!>>
            """)
    group = St3G(file=io.StringIO(template))

    t = group.getInstanceOf("top")

    s = group.getInstanceOf("str")

    s["data"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    t["s"] = s

    assert str(t) == dedent("""
          ![1][2]!
          ![3][4]!
          ![5][6]!
          ![7][8]!
          ![9]!.
     """)


def test_IndentBeyondLineWidth():
    template = dedent("""
            group test;
            duh(chars) ::= <<    <chars; wrap="\\n"\\>>>
    """)
    group = St3G(file=io.StringIO(template))

    a = group.getInstanceOf("duh")
    a["chars"] = ["a", "b", "c", "d", "e"]

    assert str(a) == dedent("""
            a
            b
            c
            d
            e
        """)


def test_IndentedExpr():
    template = dedent("""
            group test;
            duh(chars) ::= <<    <chars; wrap="\\n"\\>>>
            """)
    group = St3G(file=io.StringIO(template))

    a = group.getInstanceOf("duh")
    a["chars"] = ["a", "b", "c", "d", "e"]

    assert str(a) == dedent("""
            ab
            cd
            e
     """)


def test_NestedIndentedExpr():
    template = dedent("""
            group test;
            top(d) ::= <<  <d>!>>
            duh(chars) ::= <<  <chars; wrap="\\n"\\>>>
    """)
    group = St3G(file=io.StringIO(template))

    top = group.getInstanceOf("top")
    duh = group.getInstanceOf("duh")
    duh["chars"] = ["a", "b", "c", "d", "e"]
    top["d"] = duh

    assert str(top) == dedent("""
            ab
            cd
            e!
     """)


def test_NestedWithIndentAndTrackStartOfExpr():
    template = dedent("""
            group test;
            top(d) ::= <<  <d>!>>
            duh(chars) ::= <<x: <chars; anchor, wrap="\\n"\\>>>
            """)
    group = St3G(file=io.StringIO(template))

    top = group.getInstanceOf("top")
    duh = group.getInstanceOf("duh")
    duh["chars"] = ["a", "b", "c", "d", "e"]
    top["d"] = duh

    assert top.toString(7) == dedent("""
          x: ab
             cd
             e!
     """)


def test_LineDoesNotWrapDueToLiteral():
    """ make it wrap because of ") throws Ick { " literal """
    template = dedent("""
            group test;
            m(args,body) ::= <<public void foo(<args; wrap="\\n",separator=", ">) throws Ick { <body> }>>
            """)
    group = St3G(file=io.StringIO(template))

    a = group.getInstanceOf("m")
    a["args"] = ["a", "b", "c"]
    a["body"] = "i=3;"
    n = len("public void foo(a, b, c")

    assert str(n) == dedent("""
        "public void foo(a, b, c) throws Ick { i=3; }"
    """)


def test_SingleValueWrap():
    """ make it wrap because of ") throws Ick { " literal """
    template = dedent("""
            group test;
            m(args,body) ::= <<{ <body; anchor, wrap="\\n"> }>>
            """)

    group = St3G(file=io.StringIO(template))
    m = group.getInstanceOf("m")

    m["body"] = "i=3;"

    assert m.toString(2) == dedent("""\
        {
        "  i=3; }"
     """)


def test_LineWrapInNestedExpr():
    template = dedent("""\
            group test;
            top(arrays) ::= <<Arrays: <arrays>done>>
            array(values) ::= <<int[] a = { <values; anchor, wrap="\\n", separator=","> };<\\n\\>>>
            """)
    group = St3G(file=io.StringIO(template))

    top = group.getInstanceOf("top")
    a = group.getInstanceOf("array")

    a["values"] = [3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 2, 1, 6, 32, 5, 6, 77,
                   4, 9, 20, 2, 1, 4, 63, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 6, 32, 5, 6, 77,
                   3, 9, 20, 2, 1, 4, 6, 32, 5, 6, 77, 888, 1, 6, 32, 5]

    top["arrays"] = a
    top["arrays"] = a  # add twice

    assert top.toString(40) == dedent("""\
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
                    5,6,77,888,1,6,32,5 };
        done""")


def test_EscapeEscapeNestedAngle():
    group = St3G("test", lexer=AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", "<v:{a|\\\\<a>}>")

    t["v"] = "Joe"
    logger.info(t)

    assert str(t) == "\\Joe"


def test_ListOfIntArrays():
    group = St3G("test", lexer=AngleBracketTemplateLexer.Lexer)

    t = group.defineTemplate("t", "<data:array()>")

    group.defineTemplate("array", template='[<it:element(); separator=",">]')
    group.defineTemplate("element", "<it>")
    data = [[1, 2, 3], [10, 20, 30]]
    t["data"] = data
    logger.info(t)
    assert str(t) == "[1,2,3][10,20,30]"


def test_NullOptionSingleNullValue():
    """ Test None option """
    group = St3G("test", lexer=AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t",
                             template='<data; null="0">')
    logger.info(t)
    assert str(t) == "0"


def test_NullOptionHasEmptyNullValue():
    group = St3G("test", lexer=AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t",
                             template='<data; null="", separator=", ">')
    data = [None, 1]
    t["data"] = data
    assert str(t) == ", 1"


def test_NullOptionSingleNullValueInList():
    group = St3G("test", lexer=AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", template='<data; null="0">')
    data = [None]
    t["data"] = data
    logger.info(t)
    assert str(t) == "0"


def test_NullValueInList():
    group = St3G("test", lexer=AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", template='<data; null="-1", separator=", ">')

    data = [None, 1, None, 3, 4, None]
    t["data"] = data
    logger.info(t)
    assert str(t) == "-1, 1, -1, 3, 4, -1"


def test_NullValueInListNoNullOption():
    group = St3G("test", lexer=AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", template='<data; separator=", ">')
    data = [None, 1, None, 3, 4, None]
    t["data"] = data
    logger.info(t)
    assert str(t) == "1, 3, 4"


def test_NullValueInListWithTemplateApply():
    group = St3G("test", lexer=AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t",
                             template='<data:array(); null="-1", separator=", ">')
    group.defineTemplate("array", "<it>")
    data = [None, 0, None, 2]
    t["data"] = data
    assert str(t) == "-1, 0, -1, 2"


def test_NullValueInListWithTemplateApplyNullFirstValue():
    group = St3G("test", lexer=AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", template='<data:array(); null="-1", separator=", ">')
    group.defineTemplate("array", "<it>")
    data = [None, 0, None, 2]
    t["data"] = data
    assert str(t) == "-1, 0, -1, 2"


def test_NullSingleValueInListWithTemplateApply():
    group = St3G("test", lexer=AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", '<data:array(); null="-1", separator=", ">')
    group.defineTemplate("array", "<it>")
    data = [None]
    t["data"] = data
    assert str(t) == "-1"


def test_NullSingleValueWithTemplateApply():
    group = St3G("test", lexer=AngleBracketTemplateLexer.Lexer)
    t = group.defineTemplate("t", '<data:array(); null="-1", separator=", ">')
    group.defineTemplate("array", "<it>")
    assert str(t) == "-1"


def test_ReUseOfStripResult():
    template = dedent("""\
        group test;
        a(names) ::= "<b(strip(names))>"
        b(x) ::= "<x>, <x>"
        """)

    group = St3G(file=io.StringIO(template))
    a = group.getInstanceOf("a")
    names = ["Ter", None, "Tom"]
    a["names"] = names
    assert str(a) == "TerTom, TerTom"


def test_MapKeys():
    group = St3G("dummy", ".", lexer=AngleBracketTemplateLexer.Lexer)
    t = St3T(group=group, template='<aMap.keys:{k|<k>:<aMap.(k)>}; separator=", ">')
    amap = {"int": "0", "float": "0.0"}
    t["aMap"] = amap
    assert "int:0, float:0.0" == str(t)


def test_MapValues():
    group = St3G("dummy", ".", lexer=AngleBracketTemplateLexer.Lexer)
    t = St3T(group=group, template='<aMap.values; separator=", "> <aMap.("i"+"nt")>')
    amap = {"int": "0", "float": "0.0"}
    t["aMap"] = amap
    assert "0, 0.0 0" == str(t)


def test_MapKeysWithIntegerType():
    """ must get back an Integer from keys not a toString()'d version """
    group = St3G("dummy", ".", lexer=AngleBracketTemplateLexer.Lexer)
    t = St3T(group=group, template='<aMap.keys:{k|<k>:<aMap.(k)>}; separator=", ">')
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
    group = St3G("test")
    main = group.defineTemplate("main", '$foo(t={Hi, $super.name$}, name="parrt")$')
    main["name"] = "tombu"
    foo = group.defineTemplate("foo", "$t$")
    logger.debug(f'foo: {foo}')
    assert str(main) == "Hi, parrt"


def test_RepeatedIteratedAttrFromArg():
    """ If an iterator is sent into ST,
    it must be cannot be reset after each  use so repeated refs yield empty values.
    This would work if we passed in a List not an iterator.
    Avoid sending in iterators if you ref it twice.
    This does not give TerTom twice!!
    """
    template = dedent("""
            group test;
            root(names) ::= "$other(names)$"
            other(x) ::= "$x$, $x$"
            """)
    group = St3G(file=io.StringIO(template), lexer=DefaultTemplateLexer.Lexer)
    e = group.getInstanceOf("root")
    names = iter(["Ter", "Tom"])
    e["names"] = names
    assert str(e) == "TerTom, "


def test_SuperReferenceInIfClause():
    superGroupString = """
        group super;
        a(x) ::= "super.a"
        b(x) ::= "<c()>super.b"
        c() ::= "super.c"
        """
    superGroup = St3G(file=io.StringIO(superGroupString), lexer=AngleBracketTemplateLexer.Lexer)
    subGroupString = dedent("""
        group sub;
        a(x) ::= "<if(x)><super.a()><endif>"
        b(x) ::= "<if(x)><else><super.b()><endif>"
        c() ::= "sub.c"
        """)
    subGroup = St3G(file=io.StringIO(subGroupString), lexer=AngleBracketTemplateLexer.Lexer)
    subGroup.superGroup = superGroup
    a = subGroup.getInstanceOf("a")
    a["x"] = "foo"
    assert str(a) == "super.a"
    b = subGroup.getInstanceOf("b")
    assert str(b) == "sub.csuper.b"
    c = subGroup.getInstanceOf("c")
    assert str(c) == "sub.c"


def test_ListLiteralWithEmptyElements():
    """ Added  feature  for ST - 21 """
    e = St3T('$["Ter",,"Jesse"]:{n | $i$:$n$}; separator=", ", null=""$')
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["phones"] = "1"
    e["salaries"] = "big"
    assert str(e) == "1:Ter, 2:Jesse"


def test_TemplateApplicationAsOptionValue():
    st = St3T(template="Tokens : <rules; separator=names:{<it>}> ;",
              lexer=AngleBracketTemplateLexer.Lexer)
    st["rules"] = "A"
    st["rules"] = "B"
    st["names"] = "Ter"
    st["names"] = "Tom"
    assert str(st) == "Tokens : ATerTomB ;"
