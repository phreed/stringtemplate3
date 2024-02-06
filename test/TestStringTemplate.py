import logging
import io

import pathlib
import temppathlib
from textwrap import dedent

from stringtemplate3 import errors as st3err
from stringtemplate3.grouploaders import PathGroupLoader
from stringtemplate3.groups import StringTemplateGroup as St3G
from stringtemplate3.interfaces import StringTemplateGroupInterface as St3Gi
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


def test_HelloWorld():
    hello = St3T("Hello, $name$")
    hello["name"] = "World"
    actual = f"{hello}"

    expecting = "Hello, World"
    assert expecting == actual


def test_AaaNoGroupLoader():
    templates = dedent("""
            group testG implements blort;
            t() ::= <<foo>>
            bold(item) ::= <<foo>>
            duh(a,b,c) ::= <<foo>>
            """)
    errors = st3err.DEFAULT_ERROR_LISTENER
    with temppathlib.TemporaryDirectory() as tmp_dir:
        stg_path = tsh.write_file(tmp_dir.path / "testG.stg", templates)

        with open(stg_path, "r") as reader:
            group = St3G(file=reader, errors=errors, lexer="angle-bracket")
            logger.debug(f"group: {group}")

    expecting = "no group loader registered"
    assert expecting == str(errors)


def test_CannotFindInterfaceFile():
    """ this also tests the group loader """
    errors = st3err.DEFAULT_ERROR_LISTENER
    tmp_dir = temppathlib.TemporaryDirectory()
    St3G.registerGroupLoader(PathGroupLoader(tmp_dir.path, errors))

    templates = """
        group testG implements blort;
        t() ::= <<foo>>
        bold(item) ::= <<foo>>
        duh(a,b,c) ::= <<foo>>;
        """

    stg_file = tsh.write_file(tmp_dir.path / "testG.stg", templates)

    with open(stg_file, "r") as reader:
        group = St3G(file=reader, errors=errors)
        logger.debug(f"group: {group}")

    expecting = "no such interface file blort.sti"
    assert expecting == str(errors)


def test_MultiDirGroupLoading():
    """ this also tests the group loader """
    errors = ErrorBuffer()
    tmp_dir = temppathlib.TemporaryDirectory()
    sub_dir = tmp_dir.path / "sub"
    try:
        sub_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as pe:
        logger.exception("can't make subdir in test", pe)
        return

    St3G.registerGroupLoader(PathGroupLoader(tmp_dir.path, sub_dir))

    templates = """
        group testG2;
        t() ::= <<foo>>
        bold(item) ::= <<foo>>
        duh(a,b,c) ::= <<foo>>;
"""
    tsh.write_file(tmp_dir.path / "sub" / "testG2.stg", templates)

    group = St3G.loadGroup("testG2")
    expecting = """
    group testG2;
        bold(item) ::= <<foo>>
        duh(a,b,c) ::= <<foo>>
        t() ::= <<foo>>;
        """
    assert expecting == str(group)


def test_GroupSatisfiesSingleInterface():
    """ this also tests the group loader """
    errors = ErrorBuffer()
    tmp_dir = temppathlib.TemporaryDirectory()
    St3G.registerGroupLoader(PathGroupLoader(tmp_dir.path, errors))
    groupI = """
            interface testI;
            t();
            bold(item);
            optional duh(a,b,c);
            """
    tsh.write_file(tmp_dir.path / "testI.sti", groupI)

    templates = """
        group testG implements testI;
        t() ::= <<foo>>
        bold(item) ::= <<foo>>
        duh(a,b,c) ::= <<foo>>;
"""
    stg_file = tsh.write_file(tmp_dir.path / "testG.stg", templates)

    with open(stg_file, "rb") as reader:
        group = St3G(reader, errors=errors)
        logger.debug(f"group: {group}")

    expecting = ""  # should be no errors
    assert expecting == str(errors)
