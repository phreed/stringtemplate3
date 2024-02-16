import calendar
import io
import logging

import yaml

from stringtemplate3 import StringTemplateErrorListener

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

"""
https://docs.python.org/3/howto/logging.html
https://theantlrguy.atlassian.net/wiki/spaces/ST/pages/1409137/StringTemplate+3.0+Printable+Documentation
"""


def getMsg(ex):
    if ex is None:
        return "no message provided"
    if hasattr(ex, "getMessage"):
        return ex.getMessage()
    if hasattr(ex, "message"):
        return ex.message
    if hasattr(ex, "__str__"):
        return ex.__str__()
    return f'{ex}'


class ErrorBuffer(StringTemplateErrorListener):
    def __init__(self):
        self.errorOutput = io.StringIO(u'')
        self.n = 0

    def error(self, msg, ex):
        """
        Write the error output into the error buffer
        """
        self.n += 1
        if self.n > 1:
            self.errorOutput.write('\n')
        if ex is not None:
            self.errorOutput.write(getMsg(ex) + '\n')
        else:
            self.errorOutput.write(msg)

    def warning(self, msg):
        self.n += 1
        self.errorOutput.write(msg)

    def equals(self, obj):
        if isinstance(obj, StringTemplateErrorListener):
            return self

    def __str__(self):
        return self.errorOutput.getvalue()


class IllegalArgumentException(Exception):
    """
    https://docs.oracle.com/javase/8/docs/api/java/lang/IllegalArgumentException.html
    """

    def __init__(self, *args):
        super().__init__(*args)


sample_day = calendar.weekday(2005, 7, 5)


def write_file(file_path, content):
    try:
        with open(file_path, 'wb') as writer:
            writer.write(bytes(content, 'utf8'))
    except IOError as ioe:
        print("can't write file", ioe)
    return file_path

