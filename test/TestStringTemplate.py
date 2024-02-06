import logging

import temppathlib

from stringtemplate3 import errors as st3err
from stringtemplate3.grouploaders import PathGroupLoader
from stringtemplate3.groups import StringTemplateGroup as st3g
from stringtemplate3.interfaces import StringTemplateGroupInterface as st3gi
from stringtemplate3.templates import StringTemplate as st3t

import TestStringHelper as tsh

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
