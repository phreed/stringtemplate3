import calendar
import io
import logging
from textwrap import dedent

import temppathlib

import stringtemplate3 as St3
from stringtemplate3 import errors as St3Err
from stringtemplate3.grouploaders import PathGroupLoader
from stringtemplate3.groups import StringTemplateGroup as St3G
from stringtemplate3.interfaces import StringTemplateGroupInterface as St3Gi
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


def test_AaaNoGroupLoader():
    templates = dedent("""
            group testG implements blort;
            t() ::= <<foo>>
            bold(item) ::= <<foo>>
            duh(a,b,c) ::= <<foo>>
            """)
    errors = ErrorBuffer()
    with temppathlib.TemporaryDirectory() as tmp_dir:
        stg_path = tsh.write_file(tmp_dir.path / "testG.stg", templates)

        with open(stg_path, "r") as reader:
            group = St3G(file=reader, errors=errors, lexer="angle-bracket")
            logger.debug(f"group: {group}")

    assert str(errors) == "no group loader registered"


def test_SingleValuedAttributes():
    """ all attributes are single-valued: """
    query = St3T("SELECT $column$ FROM $table$;")
    query["column"] = "name"
    query["table"] = "User"
    """ System.out.println(query); """
    assert "SELECT name FROM User;" == str(query)


def test_EscapesOutsideExpressions():
    b = St3T("It\\'s ok...\\$; $a:{\\'hi\\', $it$}$")
    b["a"] = "Ter"
    assert str(b) == "It\\'s ok...$; \\'hi\\', Ter"


class Connector3:
    def getValues(self):
        return [1, 2, 3]

    def getStuff(self):
        m = dict()
        m["a"] = "1"
        m["b"] = "2"
        return m


def test_ApplyAnonymousTemplateToArrayAndMapProperty():
    st = St3T("$x.values:{<li>$it$</li>}$")
    st.setAttribute("x", Connector3())
    expecting = "<li>1</li><li>2</li><li>3</li>"
    assert expecting == str(st)

    st = St3T("$x.stuff:{<li>$it$</li>}$")
    st.setAttribute("x", Connector3())
    expecting = "<li>1</li><li>2</li>"
    assert expecting == str(st)


def test_HashMapPropertyFetch():
    a = St3T("$stuff.prop$")
    amap = {"prop": "Terence"}
    a["stuff"] = amap
    assert str(a) == "Terence"


def test_HashMapPropertyFetchEmbeddedStringTemplate():
    a = St3T("$stuff.prop$")
    amap = {"prop": St3T("embedded refers to $title$")}
    a["stuff"] = amap
    a.setAttribute("title", "ST rocks")
    assert str(a) == "embedded refers to ST rocks"


def test_SimpleAutoIndent():
    a = St3T("""
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



def test_8BitEuroChars():
    """ FIXME: Danish does not work if typed directly in with default file
     *  encoding on windows. The character needs to be escaped as bellow.
     *  Please correct to escape the correct character.
     """
    e = St3T("Danish: \u0143 char")
    e = e.getInstanceOf()
    assert str(e) == "Danish: \u0143 char"


def test_16BitUnicodeChar():
    e = St3T("DINGBAT CIRCLED SANS-SERIF DIGIT ONE: \u2780")
    e = e.getInstanceOf()
    assert str(e) == "DINGBAT CIRCLED SANS-SERIF DIGIT ONE: \u2780"


def test_FirstOp():
    e = St3T("$first(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    assert str(e) == "Ter"


def test_RestOp():
    e = St3T("$rest(names); separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    assert str(e) == "Tom, Sriram"


def test_RestOpEmptyList():
    e = St3T("$rest(names); separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = list()
    assert str(e) == ""



def test_LastOp():
    e = St3T("$last(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    assert str(e) == "Sriram"


def test_CombinedOp():
    """ replace first of yours with first of mine """
    e = St3T("$[first(mine),rest(yours)]; separator=\", \"$")
    e = e.getInstanceOf()
    e["mine"] = "1"
    e["mine"] = "2"
    e["mine"] = "3"
    e["yours"] = "a"
    e["yours"] = "b"
    assert str(e) == "1, b"


def test_CatListAndSingleAttribute():
    """ replace first of yours with first of mine """
    e = St3T("$[mine,yours]; separator=\", \"$")
    e = e.getInstanceOf()
    e["mine"] = "1"
    e["mine"] = "2"
    e["mine"] = "3"
    e["yours"] = "a"
    assert str(e) == "1, 2, 3, a"


def test_CatListAndEmptyAttributes():
    """ + is overloaded to be cat strings and cat lists so the """
    """ two operands (from left to right) determine which way it """
    """ goes.  In this case, x+mine is a list so everything from their """
    """ to the right becomes list cat. """
    e = St3T("$[x,mine,y,yours,z]; separator=\", \"$")
    e = e.getInstanceOf()
    e["mine"] = "1"
    e["mine"] = "2"
    e["mine"] = "3"
    e["yours"] = "a"
    assert str(e) == "1, 2, 3, a"


def test_NestedOp():
    """ // gets 2nd element """
    e = St3T("$first(rest(names))$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    assert str(e) == "Tom"


def test_FirstWithOneAttributeOp():
    e = St3T(
        "$first(names)$"
    )
    e = e.getInstanceOf()
    e["names"] = "Ter"
    assert str(e) == "Ter"


def test_LastWithOneAttributeOp():
    e = St3T(
        "$last(names)$"
    )
    e = e.getInstanceOf()
    e["names"] = "Ter"
    assert str(e) == "Ter"


def test_LastWithLengthOneListAttributeOp():
    e = St3T("$last(names)$")
    e = e.getInstanceOf()
    e["names"] = ["Ter"]
    assert str(e) == "Ter"


def test_RestWithOneAttributeOp():
    e = St3T("$rest(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    assert str(e) == ""


def test_RestWithLengthOneListAttributeOp():
    e = St3T("$rest(names)$")
    e = e.getInstanceOf()
    e["names"] = ["Ter"]
    assert str(e) == ""


def test_RepeatedRestOp():
    """  // gets 2nd element """
    e = St3T("$rest(names)$, $rest(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    assert str(e) == "Tom, Tom"


def test_IncomingLists():
    e = St3T("$rest(names)$, $rest(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    assert str(e) == "Tom, Tom"


def test_IncomingListsAreNotModified():
    e = St3T("$names; separator=\", \"$")
    e = e.getInstanceOf()
    names = ["Ter", "Tom"]
    e["names"] = names
    e["names"] = "Sriram"
    assert str(e) == "Ter, Tom, Sriram"

    assert len(names) == 2


def test_IncomingListsAreNotModified2():
    e = St3T("$names; separator=\", \"$")
    e = e.getInstanceOf()
    names = ["Ter", "Tom"]
    e["names"] = "Sriram"  # single element first now
    e["names"] = names
    assert str(e) == "Sriram, Ter, Tom"

    assert len(names) == 2


def test_IncomingArraysAreOk():
    e = St3T("$names; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = ["Ter", "Tom"]
    e["names"] = "Sriram"
    assert str(e) == "Ter, Tom, Sriram"



def test_AnonTemplateArgs():
    e = St3T("$names:{n| $n$}; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    assert str(e) == "Ter, Tom"



def test_AnonTemplateArgs2():
    e = St3T("$names:{n| .$n$.}:{ n | _$n$_}; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    assert str(e) == "_.Ter._, _.Tom._"


def test_FirstWithCatAttribute():
    e = St3T("$first([names,phones])$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    assert str(e) == "Ter"


def test_FirstWithListOfMaps():
    e = St3T("$first(maps).Ter$")
    e = e.getInstanceOf()
    m1 = dict()
    m2 = dict()
    m1["Ter"] = "x5707"
    e["maps"] = m1
    m2["Tom"] = "x5332"
    e["maps"] = m2
    assert str(e) == "x5707"

    e = e.getInstanceOf()
    alist = [m1, m2]
    e["maps"] = alist
    assert str(e) == "x5707"


def test_JustCat():
    e = St3T("$[names,phones]$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    assert str(e) == "TerTom12"


def test_Cat2Attributes():
    e = St3T("$[names,phones]; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    assert str(e) == "Ter, Tom, 1, 2"


def test_Cat2AttributesWithApply():
    e = St3T("$[names,phones]:{a|$a$.}$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    assert str(e) == "Ter.Tom.1.2."


def test_Cat3Attributes():
    e = St3T("$[names,phones,salaries]; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    e["salaries"] = "big"
    e["salaries"] = "huge"
    assert str(e) == "Ter, Tom, 1, 2, big, huge"



def test_CatWithIFAsElement():
    e = St3T("$[{$if(names)$doh$endif$},phones]; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["phones"] = "1"
    e["phones"] = "2"
    assert str(e) == "doh, 1, 2"


def test_ParallelAttributeIterationWithDifferentSizes():
    e = St3T(
        "$names,phones,salaries:{n,p,s | $n$@$p$: $s$}; separator=\", \"$"
    )
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    e["phones"] = "1"
    e["phones"] = "2"
    e["salaries"] = "big"
    assert str(e) == "Ter@1: big, Tom@2: , Sriram@: "


def test_ParallelAttributeIterationWithSingletons():
    e = St3T("$names,phones,salaries:{n,p,s | $n$@$p$: $s$}; separator=\", \"$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["phones"] = "1"
    e["salaries"] = "big"
    assert str(e) == "Ter@1: big"


def test_ParallelAttributeIterationWithMissingArgs():
    errors = ErrorBuffer()
    e = St3T("$names,phones,salaries:{$n$@$p$}; separator=\", \"$")
    e.errorListener = errors
    e = e.getInstanceOf()
    e["names"] = "Tom"
    e["phones"] = "2"
    e["salaries"] = "big"
    str(e)  # generate the error
    errorExpecting = "missing arguments in anonymous template in context [anonymous]"
    assert errorExpecting == str(errors)


def test_AnonTemplateOnLeftOfApply():
    e = St3T(
        "${foo}:{($it$)}$"
    )
    assert str(e) == "(foo)"


def test_NonPublicPropertyAccess():
    st = St3T("$x.foo$:$x.bar$")
    obj = {"foo": 9, "bar": "34"}

    st["x"] = obj
    assert str(st) == "9:34"


def test_ArgumentContext():
    """ t is referenced within foo and so will be evaluated in that
    context.  it can therefore see name. """
    group = St3G("test")
    main = group.defineTemplate("main", "$foo(t={Hi, $name$}, name=\"parrt\")$")
    foo = group.defineTemplate("foo", "$t$")
    logger.debug(f'foo: {foo}')
    assert str(main) == "Hi, parrt"


def test_Backslash():
    group = St3G("test")

    t = group.defineTemplate("t", "\\")

    assert str(t) == "\\"


def test_Backslash2():
    group = St3G("test")

    t = group.defineTemplate("t", "\\ ")

    expecting = "\\ "

    assert str(t) == expecting


def test_EscapeEscape():
    group = St3G("test")
    t = group.defineTemplate("t", "\\\\$v$")

    t["v"] = "Joe"
    logger.info(t)

    assert str(t) == "\\Joe"


def test_LengthOp():
    e = St3T(
        "$length(names)$"
    )
    e = e.getInstanceOf()
    e["names"] = "Ter"
    e["names"] = "Tom"
    e["names"] = "Sriram"
    assert str(e) == "3"


def test_LengthOpWithMap():
    e = St3T("$length(names)$")
    e = e.getInstanceOf()
    amap = {"Tom": "foo", "Sriram": "foo", "Doug": "foo"}
    e["names"] = amap
    assert str(e) == "3"


def test_LengthOpWithSet():
    e = St3T("$length(names)$")
    e = e.getInstanceOf()
    m = {"Tom", "Sriram", "Doug"}
    e["names"] = m
    assert str(e) == "3"


def test_LengthOpNull():
    e = St3T("$length(names)$")
    e = e.getInstanceOf()
    e["names"] = None
    assert str(e) == "0"


def test_LengthOpSingleValue():
    e = St3T("$length(names)$")
    e = e.getInstanceOf()
    e["names"] = "Ter"
    assert str(e) == "1"


def test_LengthOpPrimitive():
    e = St3T("$length(ints)$")
    e = e.getInstanceOf()
    e["ints"] = [1, 2, 3, 4]
    assert str(e) == "4"


def test_LengthOpOfListWithNulls():
    e = St3T("$length(data)$")
    e = e.getInstanceOf()
    data = ["Hi", None, "mom", None]
    e["data"] = data
    assert str(e) == "4"  # Nones are counted


def test_StripOpOfListWithNulls():
    e = St3T("$strip(data)$")
    e = e.getInstanceOf()
    data = ["Hi", None, "mom", None]
    e["data"] = data
    assert str(e) == "Himom"  # Nones are skipped

def test_StripOpOfListOfListsWithNulls():
    e = St3T("$strip(data):{list | $strip(list)$}; separator=\",\"$")
    e = e.getInstanceOf()
    data = [
        ["Hi", "mom"],
        None,
        ["Hi", None, "dad", None]]
    e["data"] = data
    assert str(e) == "Himom,Hidad"  # Nones are skipped


def test_StripOpOfSingleAlt():
    e = St3T("$strip(data)$")
    e = e.getInstanceOf()
    e["data"] = "hi"
    assert str(e) == "hi"  # Nones are skipped


def test_StripOpOfNull():
    e = St3T("$strip(data)$")
    e = e.getInstanceOf()
    assert str(e) == ""  # Nones are skipped


def test_LengthOpOfStrippedListWithNulls():
    e = St3T("$length(strip(data))$")
    e = e.getInstanceOf()
    data = ["Hi", None, "mom", None]
    e["data"] = data
    assert str(e) == "2"  # Nones are counted


def test_LengthOpOfStrippedListWithNullsFrontAndBack():
    e = St3T("$length(strip(data))$")
    e = e.getInstanceOf()
    data = [None, None, None, "Hi", None, None, None, "mom", None, None, None]
    e["data"] = data
    assert str(e) == "2"  # Nones are counted


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
        group = St3G(io.StringIO(templates))

        st = group.getInstanceOf("t1")
        assert "R1" == str(st)

        st = group.getInstanceOf("t2")
        assert "R2" == str(st)

        logger.error("A parse error should have been generated")
        assert False

    except Exception as ex:
        logger.exception(f'foo: {ex}')


def test_interfaceFileFormat():
    groupI = dedent("""
        interface test;
        t();
        bold(item);
        optional duh(a,b,c);
    """)
    ix = St3Gi(file=io.StringIO(groupI))

    expecting = "interface test;\n"\
                "bold(item);\n" \
                "optional duh(a, b, c);\n" \
                "t();\n"
    assert str(ix) == expecting



def test_DumpMapAndSet():
    st = St3T("$items; separator=\",\"$")
    m = dict()
    m["a"] = "1"
    m["b"] = "2"
    m["c"] = "3"
    st["items"] = m
    assert str(st) == "1,2,3"

    st = st.getInstanceOf()
    s = {"1", "2", "3"}
    st["items"] = s
    split = str(st).split(",")
    split.sort()
    assert split[0] == "1"
    assert split[1] == "2"
    assert split[2] == "3"



def test_SuperTemplateRef():
    """ you can refer to a template defined in a super group via super.t() """
    group = St3G("super")
    subGroup = St3G("sub")
    subGroup.superGroup = group
    group.defineTemplate("page", "$font()$:text")
    group.defineTemplate("font", "Helvetica")
    subGroup.defineTemplate("font", "$super.font()$ and Times")
    st = subGroup.getInstanceOf("page")
    assert str(st) == "Helvetica and Times:text"


def test_ApplySuperTemplateRef():
    group = St3G("super")
    subGroup = St3G("sub")
    subGroup.superGroup = group
    group.defineTemplate("bold", "<b>$it$</b>")
    subGroup.defineTemplate("bold", "<strong>$it$</strong>")
    subGroup.defineTemplate("page", "$name:super.bold()$")
    st = subGroup.getInstanceOf("page")
    st["name"] = "Ter"
    assert str(st) == "<b>Ter</b>"


def test_TemplatePolymorphism():
    """ bold is defined in both super and sub
    if you create an instance of page via the subgroup,
    then bold() should evaluate to the subgroup not the super
    even though page is defined in the super.  Just like polymorphism.
    """
    group = St3G("super")
    subGroup = St3G("sub")
    subGroup.superGroup = group
    group.defineTemplate("bold", "<b>$it$</b>")
    group.defineTemplate("page", "$name:bold()$")
    subGroup.defineTemplate("bold", "<strong>$it$</strong>")
    st = subGroup.getInstanceOf("page")
    st["name"] = "Ter"
    assert str(st) == "<strong>Ter</strong>"


def test_CannotFindInterfaceFile():
    """ this also tests the group loader """
    errors = ErrorBuffer()
    with temppathlib.TemporaryDirectory() as tmp_dir:
        St3G.registerGroupLoader(PathGroupLoader(tmp_dir.path, errors))

        templates = """
            group testG implements blort;
            t() ::= <<foo>>
            bold(item) ::= <<foo>>
            duh(a,b,c) ::= <<foo>>
            """

        stg_file = tsh.write_file(tmp_dir.path / "testG.stg", templates)

        with open(stg_file, "r") as reader:
            group = St3G(file=reader, errors=errors)
            logger.debug(f"group: {group}")

    assert str(errors) == "no such interface file blort.sti"


def test_MultiDirGroupLoading():
    """ this also tests the group loader """
    with temppathlib.TemporaryDirectory() as tmp_dir:
        sub_dir = tmp_dir.path / "sub"
        try:
            sub_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as pe:
            logger.exception("can't make subdir in test", pe)
            return

        St3G.registerGroupLoader(PathGroupLoader(dirs=[tmp_dir.path, sub_dir]))

        templates = dedent("""\
            group testG2;
            t() ::= <<foo>>
            bold(item) ::= <<foo>>
            duh(a,b,c) ::= <<foo>>
            """)
        tsh.write_file(tmp_dir.path / "sub" / "testG2.stg", templates)

        group = St3G.loadGroup("testG2")

    assert str(group) == dedent("""\
        group testG2;
        bold(item) ::= <<foo>>
        duh(a,b,c) ::= <<foo>>
        t() ::= <<foo>>
        """)

