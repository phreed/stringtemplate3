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
import os
from builtins import object
from collections import abc


class AttributeRenderer(object):
    """
    This interface describes an object that knows how to format or otherwise
    render an object appropriately.  Usually this is used for locale changes
    for objects such as Date and floating point numbers...  You can either
    have an object that is sensitive to the locale or have a different object
    per locale.

    Each template may have a renderer for each object type or can default
    to the group's renderer or the super group's renderer if the group doesn't
    have one.

    The toString(Object,String) method is used when the user uses the
    format option: $o; format="f"$.  It checks the formatName and applies the
    appropriate formatting.  If the format string passed to the renderer is
    not recognized then simply call toString().
    """

    def __init__(self):
        pass

    def toString(self, o, formatName=None):
        pass


# tag::string_template_writer[]
class StringTemplateWriter(object):
    """
    Generic StringTemplate output writer filter.
 
    Literals and the elements of expressions are emitted via write().
    Separators are emitted via writeSeparator() because they must be
    handled specially when wrapping lines (we don't want to wrap
    in between an element and its separator).
    """

    NO_WRAP = -1

    def __init__(self):
        pass

    def pushIndentation(self, indent):
        raise NotImplementedError

    def popIndentation(self):
        raise NotImplementedError

    def pushAnchorPoint(self):
        raise NotImplementedError

    def popAnchorPoint(self):
        raise NotImplementedError
        
    @property
    def lineWidth(self):
        """ 
        Used when wrapping, a soft limit on the line width.
        """
        raise NotImplementedError
        
    @lineWidth.setter
    def lineWidth(self, width):
        raise NotImplementedError

    def write(self, a_str, wrap=None):
        """
        Write the string and return how many actual chars were written.
        With auto indentation and wrapping, more chars than length(str)
        can be emitted. No wrapping is done unless wrap is not None
        """
        raise NotImplementedError

    def writeWrapSeparator(self, wrap):
        """
        Because we might need to wrap at a non-atomic string boundary
        (such as when we wrap in between template applications '<data:{v|[<v>]}; wrap>')
        we need to expose the wrap string
        writing just like for the separator.
        """

        raise NotImplementedError

    def writeSeparator(self, text):
        """
        Write a separator.  Same as write() except that a \n cannot
        be inserted before emitting a separator.
        """

        raise NotImplementedError
# end::string_template_writer[]


class AutoIndentWriter(StringTemplateWriter):
    """
    Essentially a char filter that knows how to auto-indent output
    by maintaining a stack of indent levels.  I set a flag upon newline
    and then next nonwhitespace char resets flag and spits out indention.
    The indent stack is a stack of strings, so we can repeat original indent
    not just the same number of columns (don't have to worry about tabs vs
    spaces then).

    Anchors are char positions (tabs won't work) that indicate where all
    future wraps should justify to.  The wrap position is actually the
    largest of either the last anchor or the indentation level.
    
    This is a filter on a Writer.

    '\n' is the proper way to say newline for options and templates.
    Templates can mix them but use '\n' for sure on options like wrap="\n".
    ST will generate the right thing.
    Override the default (locale) newline by passing in a string to the constructor.
    """
    def __init__(self, out, line_sep=os.linesep):
        super().__init__()

        # # stack of indents
        self._indents = [None]  # start with no indent

        # # Stack of integer anchors (char positions in line)
        self._anchors = []

        self._out = out
        self._atStartOfLine = True

        self._line_sep = line_sep

        self._charPosition = 0
        self._lineWidth = self.NO_WRAP

        self._charPositionOfStartOfExpr = 0

    @property
    def lineWidth(self):
        """
        Track char position in the line (later we can think about tabs).
        Indexed from 0.
        We want to keep charPosition <= lineWidth.
        This is the position we are *about* to write not the position last written to.
        """
        return self._lineWidth

    @lineWidth.setter
    def lineWidth(self, lineWidth):
        self._lineWidth = lineWidth

    def pushIndentation(self, indent):
        """
        Push even blank (null) indents as they are like scopes;
        must be able to pop them back off stack.
        """
        self._indents.append(indent)

    def popIndentation(self):
        return self._indents.pop(-1)

    @property
    def indentationWidth(self):
        """
        Get the width of the total indentation.
        """
        return sum(len(ind) for ind in self._indents if ind is not None and isinstance(ind, abc.Sized))

    @property
    def lastAnchor(self):
        """
        Return the last anchor in the stack.
        """
        return self._anchors[-1]

    def pushAnchorPoint(self):
        self._anchors.append(self._charPosition)

    def popAnchorPoint(self):
        self._anchors.pop(-1)

    def write(self, text, wrap=None):
        """
        Write out a string literal or attribute expression or expression element.

        If doing line wrap, then check wrap before emitting this str.
        If at or beyond desired line width then emit a line-separator and any indentation
        before spitting out this str.

        If a line-separator is encountered, write it out unchanged.
        """
        assert isinstance(text, str), repr(text)

        n = 0
        if wrap is not None:
            n += self.writeWrapSeparator(wrap)

        # Ignore any \r respond only to \n
        for ch in text:
            if ch in '\r':
                continue

            if ch in '\n':
                self._atStartOfLine = True
                self._charPosition = -1  # set so the write below sets to 0
                n += len(self._line_sep)
                self._out.write(self._line_sep)
                self._charPosition += n
                continue

            if self._atStartOfLine:
                n += self.indent()
                self._atStartOfLine = False

            n += 1
            self._out.write(ch)
            self._charPosition += 1

        return n

    def writeWrapSeparator(self, wrap):
        n = 0

        # if wrap and not already at start of line (last char was \n)
        # and we have hit or exceeded the threshold
        if (self._lineWidth != self.NO_WRAP and
                not self._atStartOfLine and
                self._charPosition >= self._lineWidth):
            # ok to wrap
            # Walk wrap string and look for A\nB.
            # Spit out A then spit indent or anchor,
            # whichever is larger, then spit out B
            for ch in wrap:
                if ch == '\n':
                    n += 1
                    self._out.write(ch)
                    # atStartOfLine = true;
                    self._charPosition = 0

                    indentWidth = self.indentationWidth
                    try:
                        lastAnchor = self.lastAnchor
                    except IndexError:  # no anchors saved
                        lastAnchor = 0

                    if lastAnchor > indentWidth:
                        # use anchor not indentation
                        n += self.indent(lastAnchor)

                    else:
                        # indent is farther over than last anchor, ignore anchor
                        n += self.indent()

                    # continue writing any chars out

                else:  # write A or B part
                    n += 1
                    self._out.write(ch)
                    self._charPosition += 1

        return n

    def writeSeparator(self, text):
        return self.write(text)

    def indent(self, spaces=None):
        if spaces is None:
            n = 0
            for ind in self._indents:
                if ind is not None and isinstance(ind, abc.Sized):
                    n += len(ind)
                    self._out.write(ind)

            self._charPosition += n
            return n

        else:
            self._out.write(' ' * spaces)
            self._charPosition += spaces
            return spaces


class NoIndentWriter(AutoIndentWriter):
    """ Just pass through the text """

    def __init__(self, out):
        super(NoIndentWriter, self).__init__(out)

    def write(self, a_str, wrap=None):
        self._out.write(a_str)
        return len(a_str)
