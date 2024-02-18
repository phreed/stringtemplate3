
header {
from ASTExpr import *
import stringtemplate3
import traceback
}

header "GroupParser.__init__" {
    self.group_ = None
}

options {
    language="Python";
}

/** Match a group of template definitions beginning
 *  with a group name declaration.  Templates are enclosed
 *  in double-quotes or <<...>> quotes for multi-line templates.
 *  Template names have arg lists that indicate the cardinality
 *  of the attribute: present, optional, zero-or-more, one-or-more.
 *  Here is a sample group file:

        group nfa;

        // an NFA has edges and states
        nfa(states,edges) ::= <<
        digraph NFA {
        rankdir=LR;
        <states; separator="\\n">
        <edges; separator="\\n">
        }
        >>

        state(name) ::= "node [shape = circle]; <name>;"

 */

class GroupParser extends Parser;

options {
    k=3;
}

{
    def reportError(self, e):
        if self.group_:
            self.group_.error("template group parse error", e)
        else:
            sys.stderr.write("template group parse error: " + str(e) + '\n')
            traceback.print_exc()
}

group[g]
{
    self.group_ = g
}
    :   "group" name:ID { g.name = name.text }
        ( COLON s:ID {g.superGroup = s.text} )?
        ( "implements" i:ID {g.implementInterface(i.text)}
            ( COMMA i2:ID {g.implementInterface(i2.text)} )*
        )?
        SEMI
        ( template[g] | mapdef[g] )*
        EOF
    ;

template[g]
{
    formalArgs = {}
    st = None
    ignore = False
    templateName = None
    line = self.LT(1).line
}
    :   (   AT scope:ID DOT region:ID
            {
                templateName = g.getMangledRegionName(scope.text,region.text)
                if g.isDefinedInThisGroup(templateName):
                    g.error("group "+g.name+" line "+str(line)+": redefinition of template region: @"+
                        scope.text+"."+region.text)
                    st = stringtemplate3.StringTemplate() // create bogus template to fill in

                else:
                    err = False
                    // @template.region() ::= "..."
                    scopeST = g.lookupTemplate(scope.text)
                    if scopeST is None:
                        g.error("group "+g.name+" line "+str(line)+": reference to region within undefined template: "+
                            scope.text)
                        err = True

                    if not scopeST.containsRegionName(region.text):
                        g.error("group "+g.name+" line "+str(line)+": template "+scope.text+" has no region called "+
                            region.text)
                        err = True

                    if err:
                        st = stringtemplate3.StringTemplate()

                    else:
                        st = g.defineRegionTemplate(
                            scope.text,
                            region.text,
                            None,
                            stringtemplate3.REGION_EXPLICIT
                        )

            }
        |   name:ID {templateName = name.text}
            {
                if g.isDefinedInThisGroup(templateName):
                    g.error("redefinition of template: " + templateName)
                    // create bogus template to fill in
                    st = stringtemplate3.StringTemplate()
                else:
                    st = g.defineTemplate(templateName, None)
            }
        )
        {
            if st is not None:
                st.groupFileLine = line
        }
        LPAREN
        ( args[st] | { st.defineEmptyFormalArgumentList() } )
        RPAREN
        DEFINED_TO_BE
        ( t:STRING { st.template = t.text }
        | bt:BIGSTRING { st.template = bt.text }
        )
    |   alias:ID DEFINED_TO_BE target:ID
        { g.defineTemplateAlias(alias.text, target.text) }
    ;

args[st]
    :    arg[st] ( COMMA arg[st] )*
    ;

arg[st]
{
    defaultValue = None
}
    :   name:ID
        ( ASSIGN s:STRING
          {
              defaultValue = stringtemplate3.StringTemplate(
                    template="$_val_$"
                    )
              defaultValue["_val_"] = s.text
              defaultValue.defineFormalArgument("_val_")
              defaultValue.name = ("<" + st.name + "'s arg " +
                                   name.text +
                                   " default value subtemplate>")
          }
        | ASSIGN bs:ANONYMOUS_TEMPLATE
          {
              defaultValue = stringtemplate3.StringTemplate(
                    group=st.group,
                    template=bs.text
                    )
              defaultValue.name = ("<" + st.name + "'s arg " +
                                   name.text +
                                   " default value subtemplate>")
          }
        )?
        { st.defineFormalArgument(name.text, defaultValue) }
    ;

// suffix returns [int cardinality=FormalArgument.REQUIRED]
//     :   OPTIONAL {cardinality=FormalArgument.OPTIONAL;}
//     |   STAR     {cardinality=FormalArgument.ZERO_OR_MORE;}
//     |   PLUS     {cardinality=FormalArgument.ONE_OR_MORE;}
//     |
//     ;

mapdef[g]
{
    m = None
}
    :   name:ID
        DEFINED_TO_BE m=map
        {
            if g.getMap(name.text):
                g.error("redefinition of map: " + name.text)
            elif g.isDefinedInThisGroup(name.text):
                g.error("redefinition of template as map: " + name.text)
            else:
                g.defineMap(name.text, m)
        }
    ;

map returns [mapping = {}]
    :   LBRACK mapPairs[mapping] RBRACK
    ;

mapPairs[mapping]
    : keyValuePair[mapping] ( COMMA keyValuePair[mapping] )*
        (COMMA defaultValuePair[mapping])?
    | defaultValuePair[mapping]
    ;

defaultValuePair[mapping]
    : "default" COLON v=keyValue
        { mapping[stringtemplate3.language.ASTExpr.DEFAULT_MAP_VALUE_NAME] = v }
    ;

keyValuePair[mapping]
    : key:STRING COLON v=keyValue { mapping[key.text] = v }
    ;

keyValue returns [value = None]
    :   s1:STRING
        { 
            value = stringtemplate3.StringTemplate(
                group=self.group_, template=s1.text
                )
        }
    |   s2:BIGSTRING
        {
            value = stringtemplate3.StringTemplate(
                group=self.group_,
                template=s2.text
                )
        }
    |   k:ID { k.text == "key" }?
        { 
            value = stringtemplate3.language.ASTExpr.MAP_KEY_VALUE
        }
    |    
    ;

class GroupLexer extends Lexer;

options {
    k=2;
    charVocabulary = '\u0000'..'\uFFFE';
    testLiterals=false;
}

ID 
options {
    testLiterals=true;
}
    :   ('a'..'z'|'A'..'Z'|'_') ('a'..'z'|'A'..'Z'|'0'..'9'|'-'|'_')*
    ;

STRING
    :   '"'! ( '\\'! '"' | '\\' ~'"' | ~'"' )* '"'!
    ;

BIGSTRING
    :   "<<"!
        ( options { greedy = true; }
          : NL! { $newline } )?       // consume 1st newline
        ( options { greedy = false; } // stop when you see the >>
        : { self.LA(3) == '>' and self.LA(4) == '>' }?
          '\r'! '\n'! { $newline }  // kill last \r\n
        | { self.LA(2) == '>' and self.LA(3) == '>' }?
          '\n'! { $newline }        // kill last \n
        | { self.LA(2) == '>' and self.LA(3) == '>' }?
          '\r'! { $newline }        // kill last \r
        | NL { $newline }           // else keep
        | '\\'! '>'                 // \> escape
        | .
        )*
        ">>"!
    ;

ANONYMOUS_TEMPLATE
{
    args = None
    t = None
}
    :   '{'!
        ( options { greedy = false; }   // stop when you see the >>
        : ( '\r' )? '\n' { $newline }   // else keep
        | '\\'! '>'                     // \> escape
        | .
        )*
        '}'!
    ;

AT:     '@' ;
LPAREN: '(' ;
RPAREN: ')' ;
LBRACK: '[' ;
RBRACK: ']' ;
COMMA:  ',' ;
DOT:    '.' ;
DEFINED_TO_BE: "::=" ;
SEMI:   ';' ;
COLON:  ':' ;
STAR:   '*' ;
PLUS:   '+' ;
ASSIGN: '=' ;
OPTIONAL: '?' ;

// Single-line comments
SL_COMMENT
    :   "//"
        (~('\n'|'\r'))* (NL)?
        { $skip; $newline }
    ;

// multiple-line comments
ML_COMMENT
    :   "/*"
        (   
            options {
                greedy=false;
            }
        :   NL    { $newline }
        |   .
        )*
        "*/"
        { $skip }
    ;

protected
NL
options {
    generateAmbigWarnings=false; // single '\r' is ambig with '\r' '\n'
}
        : '\r'
        | '\n'
        | '\r' '\n'
    ;

// Whitespace -- ignored
WS  :   (   ' '
        |   '\t'
        |   '\f'
        |   NL { $newline }
        )+
        { $skip }
    ;
