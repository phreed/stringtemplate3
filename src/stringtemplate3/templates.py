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
from builtins import str
from builtins import object
import sys
import io
from copy import copy
import logging

from stringtemplate3 import antlr

from stringtemplate3.language import (
    FormalArgument,
    ChunkToken,
    ASTExpr, StringTemplateAST,
    TemplateParser,
    ActionLexer, ActionParser,
    ConditionalExpr, NewlineRef,
    StringTemplateToken,
)
from stringtemplate3.language.FormalArgument import UNKNOWN_ARGS

from stringtemplate3.writers import StringTemplateWriter
import stringtemplate3

logger = logging.getLogger(__name__)


class STAttributeList(list):
    """
    Just an alias for list, but this way I can track whether a
    list is something ST created or it's an incoming list.
    """

    pass


class Aggregate(object):
    """
    An automatically created aggregate of properties.

    I often have lists of things that need to be formatted, but the list
    items are actually pieces of data that are not already in an object.  I
    need ST to do something like:

    Ter=3432
    Tom=32234
    ....

    using template:

    $items:{$attr.name$=$attr.type$}$

    This example will call getName() on the objects in items attribute,
    but what if they aren't objects?
    I have perhaps two parallel arrays instead of a single array of objects containing two fields.
    One solution is to allow dictionaries to be handled like properties
    so that 'it.name' would fail getName() but then see that
    it's a dictionary and do it.get('name') instead.

    This very clean approach is espoused by some, but the problem is that
    it's a hole in my separation rules.  People can put the logic in the
    view because you could say: 'go get bob's data' in the view:

    Bob's Phone: $db.bob.phone$

    A view should not be part of the program and hence should never be able
    to go ask for a specific person's data.

    After much thought, I finally decided on a simple solution.  I've
    added setAttribute variants that pass in multiple property values,
    with the property names specified as part of the name using a special
    attribute name syntax: 'name.{propName1,propName2,...}'.  This
    object is a special kind of dictionary that hopefully prevents people
    from passing a subclass or other variant that they have created as
    it would be a loophole.  Anyway, the ASTExpr.getObjectProperty()
    method looks for Aggregate as a special case and does a get() instead
    of getPropertyName.
    """

    def __init__(self, master):
        self._properties = {}
        self._master = master

    def __setitem__(self, propName, propValue):
        """ 
        Allow StringTemplate to add values, but prevent the end user from doing so.
        Instead of relying on data hiding, we check the type of the master of this aggregate.
        """
        if isinstance(self._master, StringTemplate):
            self._properties[propName] = propValue
        else:
            raise AttributeError

    def get(self, propName, default=None):
        """
        Instead of relying on data hiding, we check the type of the master of this aggregate.
        """
        if isinstance(self._master, StringTemplate):
            return self._properties.get(propName, default)
        raise AttributeError

    def __getitem__(self, propName):
        """
        Instead of relying on data hiding, we check the type of the master of this aggregate.
        """
        if isinstance(self._master, StringTemplate):
            if propName in self._properties:
                return self._properties[propName]
            return None
        raise AttributeError

    def __contains__(self, propName):
        """
        Instead of relying on data hiding, we check the type of the master of this aggregate.
        """
        if isinstance(self._master, StringTemplate):
            return propName in self._properties
        raise AttributeError

    def __str__(self):
        return str(self._properties)


# <@r()>
REGION_IMPLICIT = 1
# <@r>...<@end>
REGION_EMBEDDED = 2
# @t.r() ::= "..." defined manually by coder
REGION_EXPLICIT = 3

ANONYMOUS_ST_NAME = "anonymous"
DEFAULT_GROUP_NAME = 'defaultGroup'

# incremental counter for templates IDs
templateCounter = 0


def getNextTemplateCounter():
    global templateCounter
    templateCounter += 1
    return templateCounter


def resetTemplateCounter():
    """
    reset the template ID counter to 0; def that testing routine
    can access but not really of interest to the user.
    """
    global templateCounter
    templateCounter = 0


class StringTemplate(object):
    """
    A StringTemplate is a "document" with holes in it where you can stick values.
    StringTemplate breaks up your template into chunks of text and attribute expressions.
    StringTemplate< ignores everything outside of attribute expressions,
    treating it as just text to spit out when you call StringTemplate.toString().
    """
    @property
    def defaultGroup(self):
        return StringTemplateGroup(name='defaultGroup', rootDir='.')

    def __init__(self, template=None, group=None, lexer=None, attributes=None, name=None, lineSeparator=os.linesep):
        """ Either:
          Create a blank template with no pattern and no attributes
        Or:
          Create an anonymous template.
          chunks (which point to self anonymous template) and attributes.
        Or:
          Create an anonymous template with no name, but with a group
        Or:
          Create a template
        """
        self._lineSeparator = lineSeparator
        self._referencedAttributes = None
        self._name = ANONYMOUS_ST_NAME if name is None else name
        self._templateID = getNextTemplateCounter()
        self._enclosingInstance = None
        self._argumentContext = None
        self._argumentsAST = None
        self._formalArgumentKeys = None
        self._formalArguments = UNKNOWN_ARGS
        self._numberOfDefaultArgumentValues = 0
        self._passThroughAttributes = False
        self._nativeGroup = None

        if group is not None:
            assert isinstance(group, StringTemplateGroup)
            self._group = group
        else:
            self._group = StringTemplateGroup(
                name=DEFAULT_GROUP_NAME, rootDir='.', lineSeparator=self._lineSeparator)

        if lexer is not None:
            self._group.templateLexerClass = lexer

        self._groupFileLine = None

        self._listener = None
        self._pattern = None
        self._attributes = None
        self._attributeRenderers = None
        self._chunks = None
        self._regionDefType = None
        self._isRegion = False
        self._regions = set()

        if template is not None:
            assert isinstance(template, str)
            self.template = template

        if attributes is not None:
            assert isinstance(attributes, dict)
            self._attributes = attributes

    @property
    def templateID(self):
        return self._templateID

    @property
    def passThroughAttributes(self):
        """
        Normally, formal parameters hide any attributes inherited from the
        enclosing template with the same name.  This is normally what you
        want, but makes it hard to invoke another template passing in all
        the data.  Use notation now: <otherTemplate(...)> to say "pass in
        all data".  Works great. Can also say <otherTemplate(foo="xxx",...)>
        """
        return self._passThroughAttributes

    @property
    def referencedAttributes(self):
        return self._referencedAttributes

    @property
    def attributes(self):
        """
        Map an attribute name to its value(s).
        These values are set by outside code via st[name] = value.
        StringTemplate is like self in that a template is both the "class def" and "instance".
        When you create a StringTemplate or setTemplate, the text is broken up into chunks.
        That is, compiled down into a series of chunks that can be evaluated later.
        You can have multiple.
        """
        return self._attributes

    @property
    def argumentsAST(self):
        """
        If self template is embedded in another template, the arguments
        must be evaluated just before each application when applying
        template to a list of values.  The "it" attribute must change
        with each application so that $names:bold(item=it)$ works.  If
        you evaluate once before starting the application loop then it
        has a single fixed value.  Eval.g saves the AST rather than evaluating
        before invoking applyListOfAlternatingTemplates().  Each iteration
        of a template application to a multivalued attribute, these args
        are re-evaluated with an initial context of:[it=...], [i=...].
        """
        return self._argumentsAST

    @property
    def argumentContext(self):
        """
        If self template is an embedded template such as when you apply
        a template to an attribute, then the arguments passed to self
        template represent the argument context--a set of values
        computed by walking the argument assignment list.
        For example, <name:bold(item=name, foo="x")> would result in an
        argument context of:[item=name], [foo="x"] for self template.
        This template would be the bold() template and
        the enclosingInstance would point at the template that held
        that <name:bold(...)> template call.
        When you want to get an attribute value,
        you first check the attributes for the 'self' template
        then the arg context then the enclosingInstance like resolving
        variables in pascal-like language with nested procedures.

        With multivalued attributes such as <faqList:briefFAQDisplay()> attribute "i" is set to 1..n.
        """
        return self._argumentContext

    @property
    def isRegion(self):
        """
        Does this template come from a <@region>...<@end> embedded in another template?
        """
        return self._isRegion

    @isRegion.setter
    def isRegion(self, value):
        self._isRegion = value

    @property
    def attributeRenderers(self):
        """
        A Map<Class,Object> that allows people to register a renderer for
        a particular kind of object to be displayed in this template.
        This overrides any renderer set for this template's group.

        Most of the time this map is not used because the StringTemplateGroup
        has the general renderer map for all templates in that group.
        Sometimes though you want to override the group's renderers.
        """
        return self._attributeRenderers

    @attributeRenderers.setter
    def attributeRenderers(self, renderers):
        self._attributeRenderers = renderers

    @property
    def pattern(self):
        """
        The original, immutable pattern/language.
        Not really used again after initial "compilation", setup/parsing.
        Equivalent to the 'template' property?
        """
        return self._pattern

    @pattern.setter
    def pattern(self, pattern):
        self._pattern = pattern

    @property
    def chunks(self):
        """
        A list of alternating string and ASTExpr references.
        This is compiled when the template is loaded/defined and walked
        to write out a template instance.
        """
        return self._chunks

    @chunks.setter
    def chunks(self, chunks):
        self._chunks = chunks

    @property
    def formalArgumentKeys(self):
        """
        When templates are defined in a group file format, the attribute
        list is provided including information about attribute cardinality
        such as present, optional, ...  When self information is available,
        rawSetAttribute should do a quick existence check as should the
        invocation of other templates.  So if you ref bold(item="foo") but
        item is not defined in bold(), then an exception should be thrown.
        When actually rendering the template, the cardinality is checked.
        This is a {str:FormalArgument} dictionary.
        """
        return self._formalArgumentKeys

    @formalArgumentKeys.setter
    def formalArgumentKeys(self, formalArgumentKeys):
        self._formalArgumentKeys = formalArgumentKeys

    @property
    def formalArguments(self):
        return self._formalArguments

    @formalArguments.setter
    def formalArguments(self, formalArgument):
        self._formalArguments = formalArgument

    @property
    def numberOfDefaultArgumentValues(self):
        """
        How many formal arguments to this template have default values specified?
        """
        return self._numberOfDefaultArgumentValues

    @numberOfDefaultArgumentValues.setter
    def numberOfDefaultArgumentValues(self, values):
        self._numberOfDefaultArgumentValues = values

    @property
    def name(self):
        """
        What's the name of the template?
        """
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def nativeGroup(self):
        """
        What group originally defined the prototype for self template?
        This affects the set of templates I can refer to.  super.t() must
        always refer to the super of the original group.

          group base;
          t ::= "base";

          group sub;
          t ::= "super.t()2"

          group subsub;
          t ::= "super.t()3"
        """
        return self._nativeGroup

    @nativeGroup.setter
    def nativeGroup(self, value):
        self._nativeGroup = value

    @property
    def group(self):
        """
        This template was created as part of what group?
        Even if this template was created from a prototype in a supergroup,
        its group will be the subgroup.
        That's the way polymorphism works.
        """
        return self._group

    @group.setter
    def group(self, grp):
        self._group = grp

    @property
    def listener(self):
        return self._listener

    @listener.setter
    def listener(self, value):
        self._listener = value

    @property
    def regions(self):
        """
        Set of implicit and embedded regions for this template.
        """
        return self._regions

    @regions.setter
    def regions(self, value):
        self._regions = value

    @property
    def regionDefType(self):
        """
        If someone refs <@r()> in template t, an implicit

          @t.r() ::= ""

        is defined, but you can overwrite this def by defining your own.
        We need to prevent more than one manual def though.
        Between this var and isEmbeddedRegion we can determine these cases.
        """
        return self._regionDefType

    @regionDefType.setter
    def regionDefType(self, value):
        self._regionDefType = value

    def dup(self, fr, to):
        """
        Make the 'to' template look exactly like the 'from' template except for the attributes.
        This is like creating an instance of a class in that the executable code is the same
        (the template chunks), but the instance data is blank (the attributes).
        Do not copy the enclosingInstance pointer since you will want self
        template to eval in a context different from the exemplar.
        """
        to.attributeRenderers = fr.attributeRenderers
        to.pattern = copy(fr.pattern)
        to.chunks = copy(fr.chunks)
        to.formalArgumentKeys = copy(fr.formalArgumentKeys)
        to.formalArguments = copy(fr.formalArguments)
        to.numberOfDefaultArgumentValues = fr.numberOfDefaultArgumentValues
        to.name = copy(fr.name)
        to.nativeGroup = fr.nativeGroup
        to.group = fr.group
        to.listener = copy(fr.listener)
        to.regions = fr.regions
        to.isRegion = fr.isRegion
        to.regionDefType = fr.regionDefType

    def getInstanceOf(self):
        """
        Make an instance of self template; it contains an exact copy of
        everything (except the attributes and enclosing instance pointer).
        So the new template refers to the previously compiled chunks of self
        template but does not have any attribute values.
        """
        if self._nativeGroup is not None:
            # create a template using the native group for this template
            # but its "group" is set to this.group by dup after creation so
            # polymorphism still works.
            t = self._nativeGroup.createStringTemplate()

        else:
            t = self._group.createStringTemplate()

        self.dup(self, t)
        return t

    @property
    def enclosingInstance(self):
        """
        Enclosing instance if I'm embedded within another template.
        IF-subtemplates are considered embedded as well.
        """
        return self._enclosingInstance

    @enclosingInstance.setter
    def enclosingInstance(self, enclosingInstance):
        if self == self._enclosingInstance:
            raise AttributeError('cannot embed template ' +
                                 str(self._name) + ' in itself')
        # set the parent for this template
        self._enclosingInstance = enclosingInstance

    @property
    def outermostEnclosingInstance(self):
        if self._enclosingInstance is not None:
            return self._enclosingInstance.outermostEnclosingInstance

        return self

    @property
    def outermostName(self):
        if self.enclosingInstance is not None:
            return self.enclosingInstance.outermostName
        return self._name

    @property
    def groupFileLine(self):
        """
        Return the outermost template's group file line number
        If this template is defined within a group file, what line number?
        """
        if self.enclosingInstance is not None:
            return self.enclosingInstance.groupFileLine

        return self._groupFileLine

    @groupFileLine.setter
    def groupFileLine(self, groupFileLine):
        self._groupFileLine = groupFileLine

    @property
    def template(self):
        return self._pattern

    @template.setter
    def template(self, template):
        self._pattern = template
        self.breakTemplateIntoChunks()

    @property
    def errorListener(self):
        """
        Where to report errors
        """
        if not self._listener:
            return self._group.errorListener
        return self._listener

    @errorListener.setter
    def errorListener(self, listener):
        self._listener = listener

    def reset(self):
        # just throw out table and make new one
        self._attributes = {}

    @property
    def predefinedAttributes(self):
        return None

    @predefinedAttributes.setter
    def predefinedAttributes(self, attrs):
        # only do self method so far in lint mode
        if not stringtemplate3.lintMode:
            pass

    def removeAttribute(self, name):
        if self._attributes is None:
            return
        del self._attributes[name]

    __delitem__ = removeAttribute

    def setAttribute(self, name, *values):
        """
        Set an attribute for self template.  If you set the same
        attribute more than once, you get a multivalued attribute.
        If you send in a StringTemplate object as a value, its
        enclosing instance (where it will inherit values from) is
        set to 'self'.  This would be the normal case, though you
        can set it back to None after this call if you want.
        If you send in a List plus other values to the same
        attribute, they all get flattened into one List of values.
        This will be a new list object so that incoming objects are
        not altered.
        If you send in an array, it is converted to a List.  Works
        with arrays of objects and arrays of:int,float,double.
        """

        if len(values) == 0:
            return
        if len(values) == 1:
            value = values[0]

            if value is None or name is None:
                return

            if '.' in name:
                raise ValueError("cannot have '.' in attribute names")

            if self._attributes is None:
                self._attributes = {}

            if isinstance(value, StringTemplate):
                value.enclosingInstance = self

            elif (isinstance(value, (list, tuple)) and
                  not isinstance(value, STAttributeList)):
                # convert to STAttributeList
                value = STAttributeList(value)

            # convert plain collections
            # get exactly in this scope (no enclosing)
            o = self._attributes.get(name, None)
            if o is None:  # new attribute
                self.rawSetAttribute(self._attributes, name, value)
                return

            # it will be a multi-value attribute
            if isinstance(o, STAttributeList):  # already a list made by ST
                v = o

            elif isinstance(o, list):  # existing attribute is non-ST List
                # must copy to an ST-managed list before adding new attribute
                v = STAttributeList()
                v.extend(o)
                self.rawSetAttribute(self._attributes, name, v)  # replace attribute w/list

            else:
                # non-list second attribute, must convert existing to ArrayList
                v = STAttributeList()  # make list to hold multiple values
                # make it point to list now
                self.rawSetAttribute(self._attributes, name, v)  # replace attribute w/list
                v.append(o)  # add previous single-valued attribute

            if isinstance(value, list):
                # flatten incoming list into existing
                if v != value:  # avoid weird cyclic add
                    v.extend(value)

            else:
                v.append(value)

        else:
            # # Create an aggregate from the list of properties in aggrSpec and
            #  fill with values from values array.
            #
            aggrSpec = name
            aggrName, properties = self.parseAggregateAttributeSpec(aggrSpec)
            if not values or len(properties) == 0:
                raise ValueError('missing properties or values for \'' + aggrSpec + '\'')
            if len(values) != len(properties):
                raise IndexError('number of properties in \'' + aggrSpec + '\' != number of values')
            aggr = Aggregate(self)
            for i, value in enumerate(values):
                if isinstance(value, StringTemplate):
                    value.enclosingInstance = self
                # else:
                #    value = AST.Expr.convertArrayToList(value)
                property_ = properties[i]
                aggr[property_] = value
            self.setAttribute(aggrName, aggr)

    def __setitem__(self, key, value):
        if isinstance(value, tuple):
            self.setAttribute(key, *value)
        else:
            self.setAttribute(key, value)

    def parseAggregateAttributeSpec(self, aggrSpec):
        """
        Split "aggrName.{propName1,propName2" into list [propName1,propName2]
        and the aggrName. Space is allowed around ','
        """

        dot = aggrSpec.find('.')
        if dot <= 0:
            raise ValueError('invalid aggregate attribute format: ' + aggrSpec)
        aggrName = aggrSpec[:dot].strip()
        propString = aggrSpec[dot + 1:]
        propString = [
            p.strip()
            for p in propString.split('{', 2)[-1].split('}', 2)[0].split(',')
        ]

        return aggrName, propString

    def rawSetAttribute(self, attributes, name, value):
        """
        Map a value to a named attribute.
        Throw KeyError if the named attribute is not formally defined
        in self's specific template and a formal argument list exists.
        """
        if self._formalArguments != UNKNOWN_ARGS and not self.hasFormalArgument(name):
            # a normal call to setAttribute with unknown attribute
            raise KeyError(f"no such attribute: {name} in template context " +
                           self.enclosingInstanceStackString)
        if value is not None:
            attributes[name] = value

    def rawSetArgumentAttribute(self, embedded, attributes, name, value):
        """
        Argument evaluation such as foo(x=y), x must
        be checked against foo's argument list not this's (which is
        the enclosing context).  So far, only eval.g uses arg self as
        something other than "this".
        """

        if embedded.formalArguments != UNKNOWN_ARGS and not embedded.hasFormalArgument(name):
            raise KeyError(f"template {embedded.name} has no such attribute: {name} in template context " +
                           self.enclosingInstanceStackString)
        if value is not None:
            attributes[name] = value

    def write(self, out):
        """
        Walk the chunks, asking them to write themselves out according
        to attribute values of 'self.attributes'.
        This is like evaluating or interpreting the StringTemplate as a program using the attributes.
        The chunks will be identical (point at same list) for all instances of self template.
        """

        if self._group.debugTemplateOutput:
            self._group.emitTemplateStartDebugString(self, out)

        n = 0
        self.predefinedAttributes = None
        self.setDefaultArgumentValues()
        if self._chunks:
            i = 0
            while i < len(self._chunks):
                a = self._chunks[i]
                chunkN = 0 if a is None else a.write(self, out)

                # expr-on-first-line-with-no-output NEWLINE => NEWLINE
                if (chunkN == 0 and
                        i == 0 and
                        i + 1 < len(self._chunks) and
                        isinstance(self._chunks[i + 1], NewlineRef)):
                    # skip next NEWLINE
                    i += 2  # skip *and* advance!
                    continue

                # NEWLINE expr-with-no-output NEWLINE => NEWLINE
                # Indented $...$ have the indent stored with the ASTExpr
                # so the indent does not come out as a StringRef
                if (not chunkN) and (i - 1) >= 0 and \
                        isinstance(self._chunks[i - 1], NewlineRef) and \
                        (i + 1) < len(self._chunks) and \
                        isinstance(self._chunks[i + 1], NewlineRef):
                    logger.debug('found pure \\n blank \\n pattern\n')
                    i += 1  # make it skip over the next chunk, the NEWLINE
                n += chunkN
                i += 1

        if self._group.debugTemplateOutput:
            self._group.emitTemplateStopDebugString(self, out)

        if stringtemplate3.lintMode:
            self.checkForTrouble()

        return n

    def get(self, this, attribute):
        """
        Resolve an attribute reference.  It can be in four possible places:

        1. the attribute list for the current template
        2. if self is an embedded template, somebody invoked us possibly
           with arguments--check the argument context
        3. if self is an embedded template, the attribute list for the
           enclosing instance (recursively up the enclosing instance chain)
        4. if nothing is found in the enclosing instance chain, then it might
           be a map defined in the group or the its supergroup etc...

        Attribute references are checked for validity.  If an attribute has
        a value, its validity was checked before template rendering.
        If the attribute has no value, then we must check to ensure it is a
        valid reference.  Somebody could reference any random value like $xyz$
        formal arg checks before rendering cannot detect self--only the ref
        can initiate a validity check.  So, if no value, walk up the enclosed
        template tree again, this time checking formal parameters not
        attributes dictionary.  The formal definition must exist even if no
        value.

        To avoid infinite recursion in str(), we have another condition
        to check regarding attribute values.  If your template has a formal
        argument, foo, then foo will hide any value available from "above"
        in order to prevent infinite recursion.

        This method is not static so people can override its functionality.
        """

        if not this:
            return None

        if stringtemplate3.lintMode:
            this.trackAttributeReference(attribute)

        # is it here?
        o = None
        if this.attributes and attribute in this.attributes:
            o = this.attributes[attribute]
            return o

        # nope, check argument context in case embedded
        if not o:
            argContext = this.argumentContext
            if argContext and attribute in argContext:
                o = argContext[attribute]
                return o

        if (not o) and \
                (not this.passThroughAttributes) and \
                this.hasFormalArgument(attribute):
            # if you've defined attribute as formal arg for self template,
            # and it has no value, do not look up the enclosing dynamic scopes.
            # This avoids potential infinite recursion.
            return None

        # not locally defined, check enclosingInstance if embedded
        if (not o) and this.enclosingInstance:
            logger.debug(f'looking for {self._name}.{attribute} in super [={this.enclosingInstance.name}]\n')
            valueFromEnclosing = self.get(this.enclosingInstance, attribute)
            if not valueFromEnclosing:
                self.checkNullAttributeAgainstFormalArguments(this, attribute)
            o = valueFromEnclosing

        # not found and no enclosing instance to look at
        elif (not o) and (not this.enclosingInstance):
            # It might be a map in the group or supergroup...
            o = this.group.getMap(attribute)

        return o

    def getAttribute(self, name):
        return self.get(self, name)

    __getitem__ = getAttribute

    def breakTemplateIntoChunks(self):
        """
        Walk a template, breaking it into a list of
        chunks: Strings and actions/expressions.
        """

        logger.debug(f'parsing template: {self._pattern}')
        if not self._pattern:
            return
        try:
            # instead of creating a specific template lexer, use
            # an instance of the class specified by the user.
            # The default is DefaultTemplateLexer.
            # The only constraint is that you use an ANTLR lexer,
            # so I can use the special ChunkToken.
            lexerClass = self._group.templateLexerClass
            chunkStream = lexerClass(io.StringIO(self._pattern))
            chunkStream._this = self
            chunkStream.setTokenObjectClass(ChunkToken)
            chunkifier = TemplateParser.Parser(chunkStream)
            chunkifier.template(self)
        except Exception as ex:
            if stringtemplate3.crashOnActionParseError:
                raise

            name = "<unknown>"
            if self._name:
                name = self._name

            outerName = self.outermostName
            if outerName and not name == outerName:
                name = name + ' nested in ' + outerName

            self.error('problem parsing template \'' + name + '\' ', ex)

    def parseAction(self, action):
        lexer = ActionLexer.Lexer(io.StringIO(str(action)))
        parser = ActionParser.Parser(lexer, self)
        parser.setASTNodeClass(StringTemplateAST)
        lexer.setTokenObjectClass(StringTemplateToken)
        try:
            options = parser.action()
            tree = parser.AST
            if not tree:
                return None

            if tree.type == ActionParser.CONDITIONAL:
                return ConditionalExpr(self, tree)
            else:
                return ASTExpr(self, tree, options)

        except antlr.RecognitionException as re:
            if stringtemplate3.crashOnActionParseError:
                raise re
            self.error(f"Can't recognize chunk: {action}", re)
        except antlr.TokenStreamException as tse:
            if stringtemplate3.crashOnActionParseError:
                raise tse
            self.error(f"Can't parse chunk: {action}", tse)

        return None

    def addChunk(self, e):
        if not self._chunks:
            self._chunks = []
        self._chunks.append(e)

    # ----------------------------------------------------------------------------
    #                      F o r m a l  A r g  S t u f f
    # ----------------------------------------------------------------------------

    def setDefaultArgumentValues(self):
        """
        Set any default argument values that were not set by the
        invoking template or by setAttribute directly.  Note
        that the default values may be templates.  Their evaluation
        context is the template itself and, hence, can see attributes
        within the template, any arguments, and any values inherited
        by the template.

        Default values are stored in the argument context rather than
        the template attributes table just for consistency's sake.
        """

        if not self._numberOfDefaultArgumentValues:
            return
        if not self._argumentContext:
            self._argumentContext = {}
        if self._formalArguments != UNKNOWN_ARGS:
            argNames = self._formalArgumentKeys
            for argName in argNames:
                # use the default value then
                arg = self._formalArguments[argName]
                if arg.defaultValueST:
                    existingValue = self.getAttribute(argName)
                    if not existingValue:  # value unset?
                        # if no value for attribute, set arg context
                        # to the default value.  We don't need an instance
                        # here because no attributes can be set in
                        # the arg templates by the user.
                        self._argumentContext[argName] = arg.defaultValueST

    def lookupFormalArgument(self, name):
        """
        From self template upward in the enclosing template tree,
        recursively look for the formal parameter.
        """

        if not self.hasFormalArgument(name):
            if self.enclosingInstance:
                arg = self.enclosingInstance.lookupFormalArgument(name)
            else:
                arg = None
        else:
            arg = self.getFormalArgument(name)
        return arg

    def getFormalArgument(self, name):
        return self._formalArguments[name]

    def hasFormalArgument(self, name):
        return name in self._formalArguments

    def defineEmptyFormalArgumentList(self):
        self._formalArgumentKeys = []
        self._formalArguments = {}

    def defineFormalArgument(self, names, defaultValue=None):
        if not names:
            return
        if isinstance(names, str):
            name = names
            if defaultValue:
                self._numberOfDefaultArgumentValues += 1
            a = FormalArgument(name, defaultValue)
            if self._formalArguments == UNKNOWN_ARGS:
                self._formalArguments = {}
            self._formalArgumentKeys = [name]
            self._formalArguments[name] = a
        elif isinstance(names, list):
            for name in names:
                a = FormalArgument(name, defaultValue)
                if self._formalArguments == UNKNOWN_ARGS:
                    self._formalArgumentKeys = []
                    self._formalArguments = {}
                self._formalArgumentKeys.append(name)
                self._formalArguments[name] = a

    def registerRenderer(self, attributeClassType, renderer):
        """
        Register a renderer for all objects of a particular type.  This
        overrides any renderer set in the group for this class type.
        """

        if not self._attributeRenderers:
            self._attributeRenderers = {}
        self._attributeRenderers[attributeClassType] = renderer

    def getAttributeRenderer(self, attributeClassType):
        """
        What renderer is registered for this attributeClassType for
        this template.  If not found, the template's group is queried.
        """

        renderer = None
        if self._attributeRenderers is not None:
            renderer = self._attributeRenderers.get(attributeClassType, None)

        if renderer is not None:
            # found it
            return renderer

        # we have no renderer overrides for the template or none for class arg
        # check parent template if we are embedded
        if self.enclosingInstance is not None:
            return self.enclosingInstance.getAttributeRenderer(attributeClassType)

        # else check group
        return self._group.getAttributeRenderer(attributeClassType)

    # ----------------------------------------------------------------------------
    #                      U t i l i t y  R o u t i n e s
    # ----------------------------------------------------------------------------

    def warning(self, msg):
        if self.errorListener is not None:
            self.errorListener.warning(msg)
        else:
            logger.info(f'StringTemplate: warning: {msg}')

    def error(self, msg, e=None):
        if self.errorListener is not None:
            self.errorListener.error(msg, e)
        elif e:
            logger.info('StringTemplate: error: {msg} ', exc_info=e)
        else:
            logger.info('StringTemplate: error:  {msg} ')

    def trackAttributeReference(self, name):
        """
        Indicates that 'name' has been referenced in self template.
        """

        if not self._referencedAttributes:
            self._referencedAttributes = []
        if name not in self._referencedAttributes:
            self._referencedAttributes.append(name)

    @classmethod
    def isRecursiveEnclosingInstance(cls, st):
        """
        Look up the enclosing instance chain (and include self) to see
        if st is a template already in the enclosing instance chain.
        """

        if not st:
            return False
        p = st.enclosingInstance
        if p == st:
            # self-recursive
            return True
        # now look for indirect recursion
        while p:
            if p == st:
                return True
            p = p.enclosingInstance
        return False

    @property
    def enclosingInstanceStackTrace(self):
        buf = io.StringIO(u'')
        seen = {}
        p = self
        while p:
            if hash(p) in seen:
                buf.write(p.templateDeclaratorString)
                buf.write(" (start of recursive cycle)\n...")
                break
            seen[hash(p)] = p
            buf.write(p.templateDeclaratorString)
            if p.attributes:
                buf.write(", attributes=[")
                i = 0
                for attrName in list(p.attributes.keys()):
                    if i > 0:
                        buf.write(", ")
                    i += 1
                    buf.write(attrName)
                    o = p.attributes[attrName]
                    if isinstance(o, StringTemplate):
                        buf.write('=<' + o.name + '()@')
                        buf.write(str(o.templateID) + '>')
                    elif isinstance(o, list):
                        buf.write("=List[..")
                        n = 0
                        for st in o:
                            if isinstance(st, StringTemplate):
                                if n > 0:
                                    buf.write(", ")
                                n += 1
                                buf.write('<' + st.name + '()@')
                                buf.write(str(st.templateID) + '>')

                        buf.write("..]")

                buf.write(']')
            if p.referencedAttributes:
                buf.write(', references=')
                buf.write(p.referencedAttributes)
            buf.write('>\n')
            p = p.enclosingInstance
        # if self.enclosingInstance:
        #     buf.write(enclosingInstance.getEnclosingInstanceStackTrace())

        return buf.getvalue()

    @property
    def templateDeclaratorString(self):
        return f'<{self._name}({self._formalArgumentKeys})@{self._templateID}>'

    def getTemplateHeaderString(self, showAttributes):
        if showAttributes and self._attributes is not None:
            return self._name + str(list(self._attributes.keys()))

        return self._name

    def checkNullAttributeAgainstFormalArguments(self, this, attribute):
        """
        A reference to an attribute with no value, must be compared against
        the formal parameter to see if it exists; if it exists all is well,
        but if not, throw an exception.

        Don't do the check if no formal parameters exist for self template
        ask enclosing.
        """

        if this.formalArguments == UNKNOWN_ARGS:
            # bypass unknown arg lists
            if this.enclosingInstance:
                self.checkNullAttributeAgainstFormalArguments(
                    this.enclosingInstance, attribute)
        else:
            formalArg = this.lookupFormalArgument(attribute)
            if not formalArg:
                raise KeyError(f'no such attribute: {attribute} in template context ' +
                               self.enclosingInstanceStackString)

    def checkForTrouble(self):
        """
        Executed after evaluating a template.  For now, checks for setting
        of attributes not reference.
        """

        # we have table of set values and list of values referenced
        # compare, looking for SET BUT NOT REFERENCED ATTRIBUTES
        if not self._attributes:
            return
        for name in list(self._attributes.keys()):
            if self._referencedAttributes and \
                    name not in self._referencedAttributes:
                self.warning(self._name + ': set but not used: ' + name)

        # can do the reverse, but will have lots of False warnings :(

    @property
    def enclosingInstanceStackString(self):
        """
        If an instance of x is enclosed in a y which is in a z, return
        a String of these instance names in order from topmost to lowest;
        here that would be "[z y x]".
        """

        names = []
        p = self
        while p:
            names.append(p.name)
            p = p.enclosingInstance
        names.reverse()
        s = '['
        while names:
            s += names[0]
            if len(names) > 1:
                s += ' '
            names = names[1:]
        return s + ']'

    def addRegionName(self, name):
        self._regions.add(name)

    def containsRegionName(self, name):
        return name in self._regions

    def toDebugString(self):
        buf = io.StringIO(u'')
        buf.write('template-' + self.templateDeclaratorString + ': ')
        buf.write('chunks=')
        if self._chunks:
            buf.write(str(self._chunks))
        buf.write('\n')
        buf.write('attributes=[')
        if self._attributes:
            n = 0
            for name in list(self._attributes.keys()):
                if n > 0:
                    buf.write(',')
                buf.write(name + '=')
                value = self._attributes[name]
                if isinstance(value, StringTemplate):
                    buf.write(value.toDebugString())
                else:
                    buf.write(value)
                n += 1
        buf.write(']')
        retval = buf.getvalue()
        buf.close()
        return retval

    def toString(self, lineWidth=StringTemplateWriter.NO_WRAP):
        """
        Returns a string representation of the
        """
        out = io.StringIO(u'')
        wr = self._group.getStringTemplateWriter(out)
        wr.lineWidth = lineWidth
        try:
            self.write(wr)
        except IOError as ioe:
            self.error("Got IOError writing to writer" + str(wr.__class__.__name__))
        finally:
            # reset so next toString() does not wrap;
            # normally this is a new writer each time,
            # but just in case they override the group to reuse the writer.
            wr.lineWidth = StringTemplateWriter.NO_WRAP

        return out.getvalue()

    __str__ = toString

    def toStructureString(self, indent=0):
        """
        Don't print values, just report the nested structure with attribute names.
        Follow (nest) attributes that are templates only.
        """

        buf = io.StringIO(u'')

        buf.write('  ' * indent)  # indent
        buf.write(self._name)
        buf.write(str(list(self._attributes.keys())))  # FIXME: errr.. that's correct?
        buf.write(":\n")
        if self._attributes is not None:
            attrNames = list(self._attributes.keys())
            for name in attrNames:
                value = self._attributes[name]
                if isinstance(value, StringTemplate):  # descend
                    buf.write(value.toStructureString(indent + 1))

                else:
                    if isinstance(value, list):
                        for o in value:
                            if isinstance(o, StringTemplate):  # descend
                                buf.write(o.toStructureString(indent + 1))

                    elif isinstance(value, dict):
                        for o in list(value.values()):
                            if isinstance(o, StringTemplate):  # descend
                                buf.write(o.toStructureString(indent + 1))

        return buf.getvalue()

    def getDOTForDependencyGraph(self, showAttributes):
        """
        Generate a DOT file for displaying the template enclosure graph; e.g.,
        digraph prof {
            "t1" -> "t2"
            "t1" -> "t3"
            "t4" -> "t5"
        }
        """
        structure = (
                "digraph StringTemplateDependencyGraph {\n" +
                "node [shape=$shape$, $if(width)$width=$width$,$endif$" +
                "      $if(height)$height=$height$,$endif$ fontsize=$fontsize$];\n" +
                "$edges:{e|\"$e.src$\" -> \"$e.trg$\"\n}$" +
                "}\n"
        )

        graphST = StringTemplate(structure)
        edges = {}
        self.getDependencyGraph(edges, showAttributes)
        # for each source template
        for src, targetNodes in edges.items():
            # for each target template
            for trg in targetNodes:
                graphST.setAttribute("edges.{src,trg}", src, trg)

        graphST.setAttribute("shape", "none")
        graphST.setAttribute("fontsize", "11")
        graphST.setAttribute("height", "0")  # make height
        return graphST

    def getDependencyGraph(self, edges, showAttributes):
        """
        Get a list of n->m edges where template n contains template m.
        The map you pass in is filled with edges: key->value.  Useful
        for having DOT print out an enclosing template graph. It
        finds all direct template invocations too like <foo()> but not
        indirect ones like <(name)()>.

        Ack, I just realized that this is done statically and hence
        cannot see runtime arg values on statically included templates.
        Hmm...someday figure out to do this dynamically as if we were
        evaluating the templates.  There will be extra nodes in the tree
        because we are static like method and method[...] with args.
        """

        srcNode = self.getTemplateHeaderString(showAttributes)
        if self._attributes is not None:
            for name, value in self._attributes.items():
                if isinstance(value, StringTemplate):
                    targetNode = value.getTemplateHeaderString(showAttributes)
                    self.putToMultiValuedMap(edges, srcNode, targetNode)
                    value.getDependencyGraph(edges, showAttributes)  # descend

                else:
                    if isinstance(value, list):
                        for o in value:
                            if isinstance(o, StringTemplate):
                                targetNode = o.getTemplateHeaderString(showAttributes)
                                self.putToMultiValuedMap(edges, srcNode, targetNode)
                                o.getDependencyGraph(edges, showAttributes)  # descend

                    elif isinstance(value, dict):
                        for o in list(value.values()):
                            if isinstance(o, StringTemplate):
                                targetNode = o.getTemplateHeaderString(showAttributes)
                                self.putToMultiValuedMap(edges, srcNode, targetNode)
                                o.getDependencyGraph(edges, showAttributes)  # descend

        # look in chunks too for template refs
        for chunk in self._chunks:
            if not isinstance(chunk, ASTExpr):
                continue

            from stringtemplate3.language.ActionEvaluator import INCLUDE
            tree = chunk.AST
            includeAST = antlr.CommonAST(
                antlr.CommonToken(INCLUDE, "include")
            )

            for t in tree.findAllPartial(includeAST):
                templateInclude = t.firstChild.text
                # System.out.println("found include "+templateInclude);
                self.putToMultiValuedMap(edges, srcNode, templateInclude)
                group = self._group
                if group is not None:
                    st = group.getInstanceOf(templateInclude)
                    # descend into the reference template
                    st.getDependencyGraph(edges, showAttributes)

    def putToMultiValuedMap(self, a_map, key, value):
        """Manage a hash table like it has multiple unique values."""
        try:
            a_map[key].append(value)
        except KeyError:
            a_map[key] = [value]

    def printDebugString(self, out=sys.stderr):
        out.write('template-' + self._name + ':\n')
        out.write('chunks=')
        if self._chunks:
            totalChunks = len(self._chunks)
            for ix, chunk in enumerate(self._chunks):
                chunkN = out.write(str(chunk))
                if ((not chunkN) and
                        (ix - 1) >= 0 and
                        isinstance(self._chunks[ix - 1], NewlineRef) and
                        (ix + 1) < totalChunks and
                        isinstance(self._chunks[ix + 1], NewlineRef)):
                    logger.debug('found pure \\n blank \\n pattern\n')
        else:
            out.write('no chunks found\n')
        if not self._attributes:
            return
        out.write("\n")
        out.write("attributes=[\n")
        for nx, name in enumerate(list(self._attributes.keys())):
            if nx > 0:
                out.write(',\n')
            value = self._attributes[name]
            if isinstance(value, StringTemplate):
                out.write(f'{name}=')
                value.printDebugString()
            else:
                if isinstance(value, list):
                    for ix, o in enumerate(value):
                        out.write(f'{name}[{ix}] is {o.__class__.__name__}=')
                        if isinstance(o, StringTemplate):
                            o.printDebugString()
                        else:
                            out.write(o)
                else:
                    out.write(f"{name}={value}")
        out.write("]\n")


# initialize here, because of cyclic imports
from stringtemplate3.groups import StringTemplateGroup

StringTemplateGroup.NOT_FOUND_ST = StringTemplate()
ASTExpr.MAP_KEY_VALUE = StringTemplate()
