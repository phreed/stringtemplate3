# [The "BSD licence"]
# Copyright (c) 2003-2006 Terence Parr
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from builtins import object
import sys
import os
import traceback
from pathlib import Path

from stringtemplate3.utils import decodeFile
from stringtemplate3.groups import StringTemplateGroup
from stringtemplate3.interfaces import StringTemplateGroupInterface
from stringtemplate3.language import AngleBracketTemplateLexer


# tag::string_template_group_loader[]
class StringTemplateGroupLoader(object):
    """
    When group files derive from another group, we have to know how to
    load that group and its supergroups. This interface also knows how
    to load interfaces
    """

    def loadGroup(self, groupName, superGroup=None, lexer=None):
        """
        Load the group called groupName from somewhere.  Return null
        if no group is found.
        Groups with region definitions must know their supergroup to find
        templates during parsing.
        Specify the template lexer to use for parsing templates.  If null,
        it assumes angle brackets <...>.
        """

        raise NotImplementedError

    def loadInterface(self, interfaceName):
        """
        Load the interface called interfaceName from somewhere.  Return null
        if no interface is found.
        """

        raise NotImplementedError
# end::string_template_group_loader[]


class PathGroupLoader(StringTemplateGroupLoader):
    """
    A brain-dead loader that looks
    only in the directory(ies) specified in the constructor.
    You may specify the char encoding.
    """

    def __init__(self, dirs=None, errors=None):
        """
        Pass a single dir or multiple dirs separated by colons from which
        to load groups/interfaces.
        """
        super().__init__()

        if dirs is None:
            self._dirs = None
        elif isinstance(dirs, list):
            self._dirs = dirs
        elif isinstance(dirs, str):
            self._dirs = [dirs]
        elif isinstance(dirs, Path):
            self._dirs = [dirs]
        else:
            self._dirs = [dirs]
        self._errors = errors

        # # How are the files encoded (ascii, UTF8, ...)?
        #  You might want to read UTF8 for example on an ascii machine.
        self._file_char_encoding = sys.getdefaultencoding()

    def loadGroup(self, groupName, superGroup=None, lexer=None):
        if lexer is None:
            lexer = AngleBracketTemplateLexer.Lexer
        try:
            fr = self.locate(f"{groupName}.stg")
            if fr is None:
                self.error(f"no such group file {groupName}.stg")
                return None

            try:
                return StringTemplateGroup(
                    file=fr,
                    lexer=lexer,
                    errors=self._errors,
                    superGroup=superGroup
                )
            finally:
                fr.close()

        except IOError as ioe:
            self.error("can't load group " + groupName, ioe)

        return None

    def loadInterface(self, interfaceName):
        try:
            interfaceFileName = interfaceName + ".sti"
            fr = self.locate(interfaceFileName)
            if fr is None:
                self.error(f"no such interface file {interfaceFileName}")
                return None

            try:
                return StringTemplateGroupInterface(fr, self._errors)

            finally:
                fr.close()

        except (IOError, OSError) as ioe:
            self.error(f"can't load interface {interfaceName}", ioe)

        return None

    def locate(self, name):
        """
        Look in each directory for the file called 'name'.
        Return the decoded stream.
        """
        for adir in self._dirs:
            path = Path(adir, name)
            if path.is_file():
                stream = open(path, 'rt', encoding="utf-8", newline='')
                return stream
                # return decodeFile(stream, path, self.fileCharEncoding)

        return None

    @property
    def fileCharEncoding(self):
        return self._file_char_encoding

    @fileCharEncoding.setter
    def fileCharEncoding(self, fileCharEncoding):
        self._file_char_encoding = fileCharEncoding

    def error(self, msg, exc=None):
        if self._errors is not None:
            self._errors.error(msg, exc)

        else:
            sys.stderr.write("StringTemplate: " + msg + "\n")
            if exc is not None:
                traceback.print_exc()


class CommonGroupLoader(PathGroupLoader):
    """
    Subclass o PathGroupLoader that also works, if the package is
    packaged in a zip file.
    FIXME: this is not yet implemented, behaviour is identical to
    PathGroupLoader!
    """

    # FIXME: this needs to be overridden!
    def locate(self, name):
        """Look in each directory for the file called 'name'."""

        return PathGroupLoader.locate(self, name)
