


test:
	$(MAKE) -C stringtemplate3/test/ test

lint:	
	PYTHONPATH=~/Projects/antlr2/lib/python:. pylint --rcfile=pylintrc stringtemplate3

coverage:
	coverage.py -e
	coverage.py -x stringtemplate3/test/TestStringTemplate.py
	coverage.py -r

clean:
	$(MAKE) -C stringtemplate3/ clean

