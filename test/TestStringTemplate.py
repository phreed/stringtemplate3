import logging
import io
import os

import pathlib
import sys

import pytest
import temppathlib
from textwrap import dedent

from stringtemplate3 import errors as St3Err
from stringtemplate3.grouploaders import PathGroupLoader
from stringtemplate3.groups import StringTemplateGroup as St3G
from stringtemplate3.interfaces import StringTemplateGroupInterface as St3Gi
from stringtemplate3.language import AngleBracketTemplateLexer, DefaultTemplateLexer
from stringtemplate3.templates import StringTemplate as St3T

import TestStringHelper as tsh
from TestStringHelper import ErrorBuffer

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


@pytest.fixture
def local_dir_path():
    return pathlib.Path(__file__).parent


# tag::hello_world[]
def test_HelloWorld():
    hello = St3T(template="Hello, $name$")
    hello["name"] = "World"

    assert str(hello) == "Hello, World"
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
    decl_on = St3T(template=decl_template, lexer="angle-bracket")
    decl_on["USE_64"] = True

    assert str(decl_on) == "use_64: True\n#define TEST_HAS_64_BIT"

    decl_off = St3T(template=decl_template, lexer="angle-bracket")
    decl_off["USE_64"] = False

    assert str(decl_off) == "use_64: False\n"
# end::boolean_logic_both[]


# tag::different_delimiters[]
def test_different_delimiters():
    a_template = dedent("""\
        <argument>
        $argument$
        """)
    w_bracket = St3T(template=a_template, lexer="angle-bracket")
    w_bracket["argument"] = "resolved"
    assert str(w_bracket) == "resolved\n$argument$\n"

    w_dollar = St3T(template=a_template, lexer="default")
    w_dollar["argument"] = "resolved"
    assert str(w_dollar) == "<argument>\nresolved\n"

    w_bracket = St3T(template=a_template, lexer=AngleBracketTemplateLexer.Lexer)
    w_bracket["argument"] = "resolved"
    assert str(w_bracket) == "resolved\n$argument$\n"

    w_dollar = St3T(template=a_template, lexer=DefaultTemplateLexer.Lexer)
    w_dollar["argument"] = "resolved"
    assert str(w_dollar) == "<argument>\nresolved\n"

# end::different_delimiters[]
