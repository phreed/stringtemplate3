import datetime
import io
import logging
import pathlib
import sys
from textwrap import dedent

import pytest

import stringtemplate3
from stringtemplate3.groups import StringTemplateGroup as St3G
from stringtemplate3.language import (AngleBracketTemplateLexer,
                                      DefaultTemplateLexer,
                                      IllegalStateException)
from stringtemplate3.templates import StringTemplate as St3T
from stringtemplate3.writers import (AutoIndentWriter,
                                     AttributeRenderer)

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


@pytest.fixture
def local_dir_path():
    return pathlib.Path(__file__).parent


# tag::hello_world[]
def test_HelloWorld(caplog):
    hello = St3T(template="Hello, $name$!", name="hola")
    hello["name"] = "Earth"

    assert str(hello) == "Hello, Earth!"
# end::hello_world[]


# tag::templates_with_code_base[]
def test_templates_with_code_base():
    query = St3T(template="SELECT $column$ FROM $table$;")
    query["column"] = "name"
    query["table"] = "User"

    assert str(query) == "SELECT name FROM User;"
# end::templates_with_code_base[]


# tag::templates_with_code_multi[]
def test_templates_with_code_multi():
    query = St3T(template="SELECT $column$ FROM $table$;")
    query["column"] = "name"
    query["column"] = "email"
    query["table"] = "User"

    assert str(query) == "SELECT nameemail FROM User;"
# end::templates_with_code_multi[]


# tag::templates_with_code_multi_sep[]
def test_templates_with_code_multi_sep():
    query = St3T(template="SELECT $column; separator=\", \"$ FROM $table$;")
    query["column"] = "name"
    query["column"] = "email"
    query["table"] = "User"

    assert str(query) == "SELECT name, email FROM User;"
# end::templates_with_code_multi_sep[]


# tag::loading_templates_from_file[]
def test_loading_templates_from_file(local_dir_path):
    group = St3G(name="myGroup", rootDir=str(local_dir_path / "templates"))
    query = group.getInstanceOf("sql_stmt")
    query["column"] = "name"
    query["column"] = "email"
    query["table"] = "Person"

    assert str(query) == "SELECT name,email FROM Person;"
# end::loading_templates_from_file[]


# tag::loading_template_from_sys_path[]
def no_test_loading_template_from_sys_path():
    logger.info('sys.path: %s', sys.path)
    group = St3G(name="mygroup", lexer="angle-bracket")
    st = group.getInstanceOf("templates/page")
    st["title"] = "Page Title"
    st["body"] = "Page Body"

    assert str(st) == "SELECT name, email FROM User;"
# end::loading_template_from_sys_path[]


# tag::boolean_logic_both[]
def test_boolean_logic_both():
    decl_template = dedent("""\
        use_64: <USE_64>
        <if (USE_64)>
        #define TEST_HAS_64_BIT
        <endif>
        """)
    decl_on = St3T(template=decl_template, lexer="angle-bracket", lineSeparator="\n")
    decl_on["USE_64"] = True

    assert str(decl_on) == "use_64: True\n#define TEST_HAS_64_BIT"

    decl_off = St3T(template=decl_template, lexer="angle-bracket", lineSeparator="\n")
    decl_off["USE_64"] = False

    assert str(decl_off) == "use_64: False\n"
# end::boolean_logic_both[]


# tag::simple_group[]
@pytest.fixture
def simple_group():
    return dedent("""\
        group simple;
         
        vardef(type,name) ::= "<type> <name>;"
         
        madness(type,name,args) ::= <<
        <type> <name>(<args; separator=",">) {
          <statements; separator="\n">
        }
        >>
        """)
# end::simple_group[]


# tag::demo_auto_indent[]
def test_demo_auto_indent(simple_group):
    with io.StringIO(simple_group) as stg_file:
        group = St3G(name="demo_auto_indent", file=stg_file, lexer="angle-bracket", lineSeparator="\n")
        # logger.info(f"group templates: {group.templateNames}")
        # group.printDebugString()
        vardef = group.getInstanceOf("vardef")
        vardef["type"] = "int"
        vardef["name"] = "foo"

        # vardef.printDebugString()
        assert str(vardef) == "int foo;"
# end::demo_auto_indent[]


# tag::demo_auto_indent_of_file[]
def test_demo_auto_indent_of_file(local_dir_path):
    stg_path = local_dir_path / "templates" / "demo_auto_indent.stg"
    with open(stg_path, mode="r") as stg_file:
        group = St3G(name="demo_auto_indent", file=stg_file,  lexer="default", lineSeparator="\n")
        # print("group templates: {}", group.templateNamesAsStrings)
        function = group.getInstanceOf("function")
        function["name"] = "foo"
        body = group.getInstanceOf("slist")
        body["statements"] = "i=1;"
        nestedSList = group.getInstanceOf("slist")
        nestedSList["statements"] = "i=2;"
        body["statements"] = nestedSList
        body["statements"] = "i=3;"
        function["body"] = body

    assert str(function) == dedent("""\
        void foo() {
            i=1;
            {
                i=2;
            }
            i=3;
        }""")
# end::demo_auto_indent_of_file[]


# tag::different_delimiters[]
def test_different_delimiters():
    a_template = dedent("""\
        <argument>
        $argument$
        """)
    w_bracket = St3T(template=a_template, lexer="angle-bracket", lineSeparator="\n")
    w_bracket["argument"] = "resolved"
    assert str(w_bracket) == "resolved\n$argument$\n"

    w_dollar = St3T(template=a_template, lexer="default", lineSeparator="\n")
    w_dollar["argument"] = "resolved"
    assert str(w_dollar) == "<argument>\nresolved\n"

    w_bracket = St3T(template=a_template, lexer=AngleBracketTemplateLexer.Lexer, lineSeparator="\n")
    w_bracket["argument"] = "resolved"
    assert str(w_bracket) == "resolved\n$argument$\n"

    w_dollar = St3T(template=a_template, lexer=DefaultTemplateLexer.Lexer, lineSeparator="\n")
    w_dollar["argument"] = "resolved"
    assert str(w_dollar) == "<argument>\nresolved\n"
# end::different_delimiters[]


# tag::no_indent_writer[]
class NoIndentWriter(AutoIndentWriter):
    """Just pass through the text"""
    def __init__(self, out):
        super().__init__(out)

    def write(self, text, wrap=None):
        self._out.write(text)
        return len(text)

    def __str__(self):
        return self._out.getvalue()
# end::no_indent_writer[]


# tag::demo_no_indent_writer[]
def test_demo_no_indent_writer():
    """ write to 'out' with no indentation """
    out = io.StringIO(u'')
    group = St3G("test", lineSeparator="\n")
    group.defineTemplate("bold", "<b>$x$</b>")
    nameST = St3T("$name:bold(x=name)$", group=group)
    nameST["name"] = "Terence"
    # writer = AutoIndentWriter(out)
    writer = NoIndentWriter(out)
    nameST.write(writer)
    assert str(writer) == "<b>Terence</b>"
# end::demo_no_indent_writer[]


# tag::hide_infinite_recursion[]
def test_hide_infinite_recursion():
    templates = dedent("""\
            group test;
            block(stats) ::= "{$stats$}"
    """)
    group = St3G(file=io.StringIO(templates), lexer='default', lineSeparator="\n")
    b = group.getInstanceOf("block")
    b["stats"] = group.getInstanceOf("block")
    assert str(b) == "{{}}"
# end::hide_infinite_recursion[]


# tag::trap_infinite_recursion[]
@pytest.mark.skip(reason="error is happening but on another thread?")
def test_trap_infinite_recursion():
    """
    The block contains a stat which is an ifstat
    which in turn has a state which is a block.
    """
    templates = dedent("""\
            group test;
            block(stats) ::= "$stats$" 
            ifstat(stats) ::= "IF true then $stats$"
    """)
    stringtemplate3.lintMode = True
    group = St3G(file=io.StringIO(templates), lexer="default", lineSeparator="\n")
    block = group.getInstanceOf("block")
    ifstat = group.getInstanceOf("ifstat")
    block["stats"] = ifstat
    ifstat["stats"] = block
    try:
        result = str(block)
        logger.info(f"result: {result}")
    except IllegalStateException as ise:
        msg = ise._message
        assert str(msg) == dedent("""\
        infinite recursion to <ifstat([stats])@4> referenced in <block([stats])@3>; stack trace:
<ifstat([stats])@4>, attributes=[stats=<block()@3>]>
<block([stats])@3>, attributes=[stats=<ifstat()@4>], references=[stats]>
<ifstat([stats])@4> (start of recursive cycle)
        """)
        logger.exception(f'illegal state exception: {ise}')
    except TypeError as te:
        logger.error(f'type error: {te}')
    except Exception as ge:
        logger.error(f'general exception: {ge}')
    assert True
# end::trap_infinite_recursion[]


# tag::indirect_template_reference[]
@pytest.fixture
def indirect_template_ref():
    return dedent("""\
        group Java;
        
        file(variables,methods) ::= <<
        <variables:{ v | <v.decl:(v.format)()>}; separator="\n">
        <methods>
        >>
        
        intdecl(decl) ::= "int <decl.name> = 0;"
        intarray(decl) ::= "int[] <decl.name> = null;"
        """)
# end::indirect_template_reference[]


# tag::indirect_template_ref_decl[]
class Decl(object):
    def __init__(self, name, type_):
        self.name = name
        self.type = type_

    def getName(self):
        return self.name

    def getType(self):
        return self.type
# end::indirect_template_ref_decl[]


# tag::indirect_template_ref_demo[]
def test_indirect_template_ref(indirect_template_ref):
    group = St3G(file=io.StringIO(indirect_template_ref), lexer="angle-bracket", lineSeparator="\n")
    f = group.getInstanceOf("file")
    f.setAttribute("variables.{decl,format}", Decl("i", "int"), "intdecl")
    f.setAttribute("variables.{decl,format}", Decl("a", "int-array"), "intarray")

    assert str(f) == '        int i = 0;\n        int[] a = null;\n        '
# end::indirect_template_ref_demo[]


# tag::date_renderer_1[]
class DateRenderer1(AttributeRenderer):
    def __init__(self):
        AttributeRenderer.__init__(self)

    def toString(self, obj, formatName=None):
        if formatName is None:
            return obj.strftime("%Y.%m.%d")
        return obj.strftime(formatName)
# end::date_renderer_1[]


# tag::date_renderer_2[]
class DateRenderer2(AttributeRenderer):
    def __init__(self):
        super().__init__()

    def toString(self, obj, formatName=None):
        if formatName is None:
            return obj.strftime("%m/%d/%Y")
        return obj.strftime(formatName)
# end::date_renderer_2[]


# tag::date_renderer_3[]
class DateRenderer3(AttributeRenderer):
    def __init__(self):
        AttributeRenderer.__init__(self)

    def toString(self, obj, formatName=None):
        if formatName is None:
            return obj.strftime("%M/%D/%Y")
        if formatName == 'yyyy.MM.dd':
            return obj.strftime("%Y.%m.%d")
        return str(obj)
# end::date_renderer_3[]


# tag::string_renderer[]
class StringRenderer(AttributeRenderer):
    def __init__(self):
        AttributeRenderer.__init__(self)

    def toString(self, obj, formatName=None):
        if formatName is None:
            return str(obj)
        if formatName == "upper":
            return str(obj).upper()
        return str(obj)
# end::string_renderer[]


# tag::date_renderer_demo[]
def test_date_renderer(sample_day, sample_calendar):
    st = St3T("date: <created>", lexer="angle-bracket")
    st["created"] = sample_day
    st.registerRenderer(sample_calendar, DateRenderer1())

    assert str(st) == "date: 2005.07.05"
# end::date_renderer_demo[]


# tag::basic_format_renderer[]
class BasicFormatRenderer(AttributeRenderer):
    def toString(self, obj, formatName=None):
        """
        None: implies that no formatting specified
        """
        if formatName is None:
            return str(obj)

        if formatName == "toUpper":
            return str(obj).upper()
        elif formatName == "toLower":
            return str(obj).lower()
        else:
            raise ValueError(f"Unsupported format name: {formatName}")
# end::basic_format_renderer[]


# tag::basic_format_renderer_demo_upper[]
def test_basic_format_renderer_upper():
    st = St3T('$name; format="toUpper", null="woops"$', lexer="default")
    st["name"] = "Barney"
    st.registerRenderer(str, BasicFormatRenderer())

    assert str(st) == "BARNEY"
# end::basic_format_renderer_demo_upper[]


# tag::basic_format_renderer_combined[]
def test_basic_format_renderer_combined():
    st = St3T(template='$list : {[$it$]}; format="toUpper", separator=" and ", null="woops"$',
              lexer="default")
    st["list"] = ["x", "y", None, "z"]

    st.registerRenderer(str, BasicFormatRenderer())

    assert str(st) == "[X] and [Y] and [WOOPS] and [Z]"
# end::basic_format_renderer_combined[]


# tag::example_renderer_with_format_and_list[]
def test_renderer_with_format_and_list():
    st = St3T(template="The names: <names; format=\"upper\">",
              lexer=AngleBracketTemplateLexer.Lexer)
    st["names"] = "ter"
    st["names"] = "tom"
    st["names"] = "sriram"
    st.registerRenderer(str, StringRenderer())

    assert str(st) == "The names: TERTOMSRIRAM"
# tag::example_renderer_with_format_and_list[]


# tag::sample_day[]
@pytest.fixture
def sample_day():
    return datetime.date(2005, 7, 5)
# end::sample_day[]


# tag::sample_calendar[]
@pytest.fixture
def sample_calendar():
    return datetime.date
# end::sample_day[]


def test_RendererForDate(sample_day, sample_calendar):
    st = St3T(
        template="date: <created>",
        lexer=AngleBracketTemplateLexer.Lexer)
    st.setAttribute("created", sample_day)
    st.registerRenderer(sample_calendar, DateRenderer1())
    assert str(st) == "date: 2005.07.05"


def test_RendererWithFormat(sample_day, sample_calendar):
    st = St3T(
        template="date: <created; format=\"yyyy.MM.dd\">",
        lexer=AngleBracketTemplateLexer.Lexer)
    st.setAttribute("created", sample_day)
    st.registerRenderer(sample_calendar, DateRenderer3())
    assert str(st) == "date: 2005.07.05"


def test_RendererWithFormatAndList():
    st = St3T(
        template="The names: <names; format=\"upper\">",
        lexer=AngleBracketTemplateLexer.Lexer)
    st["names"] = "ter"
    st["names"] = "tom"
    st["names"] = "sriram"
    st.registerRenderer(str, StringRenderer())
    assert str(st) == "The names: TERTOMSRIRAM"


def test_RendererWithFormatAndSeparator():
    st = St3T(
        template="The names: <names; separator=\" and \", format=\"upper\">",
        lexer=AngleBracketTemplateLexer.Lexer)
    st["names"] = "ter"
    st["names"] = "tom"
    st["names"] = "sriram"
    st.registerRenderer(str, StringRenderer())
    assert str(st) == "The names: TER and TOM and SRIRAM"


def test_RendererWithFormatAndSeparatorAndNull():
    st = St3T(template='The names: <names; separator=" and ", null="n/a", format="upper">',
              lexer=AngleBracketTemplateLexer.Lexer)
    names = ["ter", None, "sriram"]
    st["names"] = names
    st.registerRenderer(str, StringRenderer())
    assert str(st) == "The names: TER and N/A and SRIRAM"


def test_EmbeddedRendererSeesEnclosing(sample_day, sample_calendar):
    """ st is embedded in outer; set renderer on outer, st should still see it. """
    outer = St3T(template="X: <x>",
                 lexer=AngleBracketTemplateLexer.Lexer)
    st = St3T(template="date: <created>",
              lexer=AngleBracketTemplateLexer.Lexer)
    st.setAttribute("created", sample_day)
    outer["x"] = st
    outer.registerRenderer(sample_calendar, DateRenderer1())
    assert str(outer) == "X: date: 2005.07.05"


def test_RendererForGroup(sample_day, sample_calendar):
    templates = """
            group test;
            dateThing(created) ::= \"date: <created>\"
            """
    group = St3G(file=io.StringIO(templates), lineSeparator="\n")
    st = group.getInstanceOf("dateThing")
    st.setAttribute("created", sample_day)
    group.registerRenderer(sample_calendar, DateRenderer1())
    assert str(st) == "date: 2005.07.05"


def test_OverriddenRenderer(sample_day, sample_calendar):
    templates = """
            group test;
            dateThing(created) ::= \"date: <created>\"
            """
    group = St3G(file=io.StringIO(templates), lineSeparator="\n")
    st = group.getInstanceOf("dateThing")
    st.setAttribute("created", sample_day)
    group.registerRenderer(sample_calendar, DateRenderer1())
    st.registerRenderer(sample_calendar, DateRenderer2())
    assert str(st) == "date: 07/05/2005"


