

clean:
	$(MAKE) -C test/ clean
	$(MAKE) -C language/ clean
	rm -f *.pyc *~ *,cover


lint:
	$(MAKE) -C .. lint

lint%: %.py
	PYTHONPATH=~/Projects/antlr2/lib/python:$(CURDIR)/.. pylint --rcfile=../pylintrc $<
