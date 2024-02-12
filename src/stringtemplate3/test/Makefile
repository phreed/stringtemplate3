
test: testTestStringTemplate $(subst .py,,$(wildcard test*.py))

testTestStringTemplate:
	$(MAKE) -C ../language all
	PYTHONPATH=../.. python2.4 TestStringTemplate.py --verbose

test%: test%.py
	$(MAKE) -C ../language all
	PYTHONPATH=../.. python2.4 $@.py --verbose

clean:
	rm -f *.pyc *~ *,cover


lint:
	$(MAKE) -C ../.. lint


lint%: %.py
	PYTHONPATH=~/Projects/antlr2/lib/python:$(CURDIR)/../.. pylint --rcfile=../../pylintrc $<
