DKUtils Guide
=============

This guide provides an overview of the various third-party tools that have been added
to this repository to aid in the development and maintenance of a clean, well tested, and
well documented python package.

Code formatting and standards
-----------------------------

To enforce uniform code and avoid unnecessary style checks, three tools
are utilized:

* :program:`pre-commit`
* :program:`flake8`
* :program:`yapf`

Code formatting guidelines are codified in the :program:`flake8` and :program:`yapf`
sections of the :file:`setup.cfg`. The :program:`pre-commit` framework is used to run
these tools and flag errors and warnings prior to each commit. Please install
:program:`pre-commit` to this project's local virtual environment and run
:command:`pre-commit install` in the project root directory. This will install
the requisite pre-commit hooks to run these backend formatting tools over all code on
commits. Code that does not adhere to standards will be automatically rejected by
the `CICD_DKUtils Recipe <https://cloud.datakitchen.io/dk/index.html#/variation/im/IM_Production/CICD_DKUtils/complete_cicd?tab=graph>`_
that is used to test, build, and publish this package.


.. _pre-commit-anchor:

`pre-commit <https://pre-commit.com/>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A framework for managing and maintaining multi-language pre-commit hooks.

Git hook scripts are useful for identifying simple issues before submission
to code review. We run our hooks on every commit to automatically point out
issues in code such as missing semicolons, trailing whitespace, and debug
statements. By pointing these issues out before code review, this allows a
code reviewer to focus on the architecture of a change while not wasting
time with trivial style nitpicks.


.. _flake8-anchor:

`Flake8 <http://flake8.pycqa.org/en/latest/>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A command-line utility for enforcing style consistency across Python projects. By
default it includes lint checks provided by the PyFlakes project, PEP-0008
inspired style checks provided by the PyCodeStyle project, and McCabe complexity
checking provided by the McCabe project. It will also run third-party extensions
if they are found and installed.


.. _yapf-anchor:

`YAPF <https://github.com/google/yapf>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
YAPF is based off of 'clang-format', developed by Daniel Jasper. In essence, the
algorithm takes the code and reformats it to the best formatting that conforms to
the style guide, even if the original code didn't violate the style guide. The
idea is also similar to the 'gofmt' tool for the Go programming language: end all
holy wars about formatting - if the whole codebase of a project is simply piped
through YAPF whenever modifications are made, the style remains consistent
throughout the project and there's no point arguing about style in every code
review.


.. _documentation-anchor:

Documentation Best Practices
----------------------------
`Sphinx <http://www.sphinx-doc.org/en/master/>`_ is a tool that makes it easy
to create intelligent and beautiful documentation, written by Georg Brandl and
licensed under the BSD license. The documentation and its configuration are
located in this project's :file:`docs` directory.


.. _versioning-anchor:

Versioning
----------
`Bumpversion <https://github.com/peritus/bumpversion>`_ is used to handle
project versioning. This is configured in :file:`.setup.cfg`.

.. _makefile-anchor:

Makefile
--------
A :file:`Makefile` is provided with a set of targets that are useful for managing this library. As shown below, it's
useful for cleaning your working directory, running tests, linting, generating :program:`Sphinx`
documentation, versioning, and building and pushing package archives to PyPI.

.. code-block:: none

    Add '-ext' to any target to run it inside a docker container

    Versioning:
        bump/major bump/minor bump/patch - bump the version

    Utilities:
        bash         run bash - typically used in conjunction with -ext to enter a docker container
        scan_secrets scan source code for sensitive information

    Linting:
        lint         run flake8 and yapf
        flake8       run flake8
        yapf         run yapf and correct issues in-place
        yapf-diff    run yapf and display diff between existing code and resolution if in-place is used

    Testing:
        test         run all unit tests
        test_unit    run all unit tests
        clean_unit   remove files from last test run (e.g. report_dir, .coverage, etc.)
        tox          run unit tests in python 2 and 3
        clean_tox    clean tox files (e.g. .tox)

    Documentation:
        docs         generate Sphinx documentation
        docs/html    generate Sphinx documentation
        docs/clean   remove generated Sphinx documentation

    Build and Upload:
        build        generate distribution archives (i.e. *.tar.gz and *.whl)
        upload       upload distribution archives to PyPI
        clean_build  remove all the build files (i.e. build, dist, *.egg-info)

    Cleanup:
        clean        run all the clean targets in one go
        clean_pyc    remove all *.pyc files

