PYTHON = python
BUILDOUT = bin/buildout
EXE = bin/log4tail
TEST = bin/py.test 
PYLINT = bin/pylint
COVERAGE = bin/coverage
ENV = ENV 
BIN = ENV/bin
ENV24 = ENV24
PATH := $(BIN):${PATH}

all: $(BUILDOUT)

env: $(ENV)

$(ENV):
	virtualenv --no-site-packages $(ENV)

env24: $(ENV24)

$(ENV24):
	virtualenv --no-site-packages --python=python2.4 $(ENV24)

runtests: $(TEST) 
	@echo "Running tests..."
	$(COVERAGE) run $(TEST) -v --junitxml=unittests.xml tests
	$(COVERAGE) xml src/log4tailer/*.py

pylint: $(PYLINT)
	$(PYLINT) -f parseable > report.txt

coverage: $(TEST)
	$(TEST) -v --with-coverage --cover-package=log4tailer 

$(EXE): $(BUILDOUT) 
	$(BUILDOUT) install log4tail

$(BUILDOUT): env bootstrap.py
	$(PYTHON) bootstrap.py
	$(BUILDOUT)

# just sdist
release: $(EXE)
	$(PYTHON) setup.py release

coberturasource: 
	$(PYTHON) cobpathfix.py

# sdist and tag into subversion
releasetag: $(EXE)
	$(PYTHON) setup.py release --rtag

$(TEST): $(BUILDOUT)
	$(BUILDOUT) install test

clean:
	@echo "clean ..."
	rm -f `find src -name "*.pyc"`
	rm -f `find tests -name "*.pyc"`
	rm -rf cover .coverage
	rm -rf htmlcov

distclean:
	@echo "distclean ..."
	rm -rf $(ENV)
	rm -rf build dist bin 
	rm -f `find src -name "*.pyc"`
	rm -f `find tests -name "*.pyc"`
	rm -rf cover .coverage
	rm -rf develop-eggs
	rm -rf parts
	rm -rf .installed.cfg


