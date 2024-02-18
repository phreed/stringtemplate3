

ANTLR=CLASSPATH=~/projects/antlr2/antlr.jar java antlr.Tool

all: ActionParser.py TemplateParser.py AngleBracketTemplateLexer.py ActionEvaluator.py GroupParser.py InterfaceParser.py

clean:
	rm -f *.pyc *~ *,cover
	rm -f ActionParser.py ActionLexer.py AngleBracketTemplateLexer.py GroupParser.py GroupLexer.py TemplateParser.py DefaultTemplateLexer.py ActionEvaluator.py InterfaceParser.py InterfaceLexer.py
	rm -f *.txt


ActionParser.py: action.g
	./openfiles.sh ActionParser.py ActionLexer.py
	$(ANTLR) $<
	touch $@

AngleBracketTemplateLexer.py: angle.bracket.template.g TemplateParser.py
	./openfiles.sh AngleBracketTemplateLexer.py
	$(ANTLR) angle.bracket.template.g
	touch $@

GroupParser.py: group.g
	./openfiles.sh GroupParser.py GroupLexer.py
	$(ANTLR) $<
	touch $@

TemplateParser.py: template.g
	./openfiles.sh TemplateParser.py DefaultTemplateLexer.py
	$(ANTLR) $<
	touch $@

ActionEvaluator.py: eval.g ActionParser.py
	./openfiles.sh ActionEvaluator.py
	$(ANTLR) eval.g
	touch $@

InterfaceParser.py: interface.g
	./openfiles.sh InterfaceParser.py InterfaceLexer.py
	$(ANTLR) $<
	touch $@

lint:
	$(MAKE) -C ../.. lint


lint%: %.py
	PYTHONPATH=~/Projects/antlr2/lib/python:$(CURDIR)/../.. pylint --rcfile=../../pylintrc $<
