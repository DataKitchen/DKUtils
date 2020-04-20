PATH:=bin/:${PATH}
.PHONY: \
    help \
    bump/patch bump/minor bump/major \
    bash scan_secrets \
    lint flake8 yapf yapf-diff \
    test test_unit clean_unit tox clean_tox \
    docs docs/html docs/clean \
    build upload clean_build \
    clean clean_pyc

# --- Environment ---

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(patsubst %/,%,$(dir $(MAKEFILE_PATH)))
UNITTESTS_DIR := $(MAKEFILE_DIR)/tests

PROJECT_SLUG = DKUtils
PACKAGE_NAME := $(shell echo $(PROJECT_SLUG) | tr A-Z a-z)
APP_HOME ?= /usr/src/datakitchen/$(PROJECT_SLUG)
BUILD_IMAGE = datakitchenprivate/$(PACKAGE_NAME):latest

# --- Help ---

help:
	@echo
	@echo "Add '-ext' to any target to run it inside a docker container"
	@echo
	@echo "Versioning:"
	@echo "    bump/major bump/minor bump/patch - bump the version"
	@echo
	@echo "Utilities:"
	@echo "    bash         run bash - typically used in conjunction with -ext to enter a docker container"
	@echo "    scan_secrets scan source code for sensitive information"
	@echo
	@echo "Linting:"
	@echo "    lint         run flake8 and yapf"
	@echo "    flake8       run flake8"
	@echo "    yapf         run yapf and correct issues in-place"
	@echo "    yapf-diff    run yapf and display diff between existing code and resolution if in-place is used"
	@echo
	@echo "Testing:"
	@echo "    test         run all unit tests"
	@echo "    test_unit    run all unit tests"
	@echo "    clean_unit   remove files from last test run (e.g. report_dir, .coverage, etc.)"
	@echo "    tox          run unit tests in python 2 and 3"
	@echo "    clean_tox    clean tox files (e.g. .tox)"
	@echo
	@echo "Documentation:"
	@echo "    docs         generate Sphinx documentation"
	@echo "    docs/html    generate Sphinx documentation"
	@echo "    docs/clean   remove generated Sphinx documentation"
	@echo
	@echo "Build and Upload:"
	@echo "    build        generate distribution archives (i.e. *.tar.gz and *.whl)"
	@echo "    upload       upload distribution archives to PyPI"
	@echo "    clean_build  remove all the build files (i.e. build, dist, *.egg-info)"
	@echo
	@echo "Cleanup:"
	@echo "    clean        run all the clean targets in one go"
	@echo "    clean_pyc    remove all *.pyc files"
	@echo


# --- External execution ---

MAKE_EXT = docker build -t $(BUILD_IMAGE) . && \
     docker run --rm -v $(MAKEFILE_DIR):$(APP_HOME) $(BUILD_IMAGE) \
     make -C $(APP_HOME)

# Generically execute make targets from outside the Docker container
%-ext:
	$(MAKE_EXT) $*


# --- Versioning ---

bump/patch bump/minor bump/major:
	bumpversion --no-tag $(@F)


# --- Utils ---

bash:
	bash

scan_secrets:
	@./scan_secrets.py $(PACKAGE_NAME) ignored_secrets.txt


# --- Linting ---

lint: flake8 yapf

flake8:
	flake8

yapf:
	yapf --in-place --recursive $(PACKAGE_NAME) tests

yapf-diff:
	yapf --diff --recursive $(PACKAGE_NAME) tests


# --- Testing ---

clean: clean_pyc clean_unit clean_tox clean_build docs/clean

test: test_unit

clean_pyc:
	@find $(MAKEFILE_DIR)/$(PACKAGE_NAME) -name '*.pyc' -delete
	@find $(MAKEFILE_DIR)/$(PACKAGE_NAME) -name '__pycache__' -delete

clean_unit:
	@rm -fr .coverage $(PACKAGE_NAME).egg-info
	@cd $(UNITTESTS_DIR) && rm -fr report_folder nosetests.xml *.pyc

test_unit: clean_unit
test_unit:
	nosetests

clean_tox:
	@rm -fr .tox

tox: clean_unit clean_tox
tox:
	tox -v


# --- Docs ---

docs: docs/html

docs/html docs/clean:
	$(MAKE) -C docs $(@F)


# --- Build and Upload ---

clean_build:
	@rm -fr build dist $(PROJECT_SLUG).egg-info

build: clean_build
	python3 setup.py sdist bdist_wheel

upload:
	twine upload dist/*
