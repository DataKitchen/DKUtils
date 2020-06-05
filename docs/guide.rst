DKUtils Guide
=============

This guide provides an overview of the various third-party tools that have been added
to this repository to aid in the development and maintenance of a clean, well tested, and
well documented python package. In addition, it provides a checklist of items a developer
should follow when adding content to this package.

Development Process
---------------------
Multiple steps must be followed to update this package. First, create a branch with a
name indicating the change you intend to make. When your changes are ready for review, run
the 4 main :program:`Makefile` targets locally (i.e. test, lint, scan_secrets, and docs) to ensure they pass.
Please note, fixing one target may break another, so ensure that all four targets pass after
making any changes. Next, create a Pull Request (PR) in `GitHub <https://ghe.datakitchen.io/DataKitchen/DKUtils>`_
and assign it to one or more Implementation engineers. Once the PR is approved, run the
`branch_ci <https://cloud.datakitchen.io/dk/index.html#/variation/im/IM_Production/CICD_DKUtils/branch_ci?tab=graph>`_
recipe variation of the ``CICD_DKUtils`` recipe in the ``IM_Production`` kitchen - be sure to override the
``branch`` variable with the name of your branch. Once this variation is passing and your PR is approved,
merge your changes to master.

To deploy your new package to PyPI, run the
`complete_cicd <https://cloud.datakitchen.io/dk/index.html#/variation/im/IM_Production/CICD_DKUtils/complete_cicd?tab=graph>`_
variation in the same recipe - be sure to specify the appropriate ``semantic_version_increment``.
Afterward, check `PyPI <https://pypi.org/project/DKUtils/>`_ to ensure your version was uploaded.
Finally, :command:`pip install` the new package and test to ensure your updates are as expected and verify the latest
documentation is updated on the `DKUtils Website <http://dkutils.dk.io/>`_.

These details are listed in greater detail in the checklist below. This checklist should be referenced
any time you intend to update this library.

Deployment Checklist
^^^^^^^^^^^^^^^^^^^^
Ensure all of these items are performed and passing prior to running the
`complete_cicd <https://cloud.datakitchen.io/dk/index.html#/variation/im/IM_Production/CICD_DKUtils/complete_cicd?tab=graph>`_
to build and deploy a new library version:

* Run :command:`make test`

  * Ensure all tests pass
  * Ensure code coverage is adequate and not significantly different than before your change and no less than 80%

* Run :command:`make lint`

  * Fix any issues reported by Flake8
  * Commit any changes made automatically by YAPF

* Run :command:`make scan_secrets`

  * Remove any secrets that have been added
  * Add output lines that don't contain secrets to the ignored_secrets.txt file and commit

* Run :command:`make docs`

  * Ensure you added an entry to the release notes (:file:`/docs/release_notes.rst`) with the
    appropriate semantic version increment
  * Resolve any warnings or errors (i.e. red text in output) except for the following warning
    which is a known bug in Sphinx: ``WARNING: html_static_path entry '_static' does not exist``
  * Review your documentation updates (i.e. open :file:`/docs/_build/html/index.html` in your browser)

* Create a PR (Pull Request) of your branch

  * Assign it to one or more Implementation team members
  * Address any PR feedback - approval is required prior to a merge

*  Run `branch_ci <https://cloud.datakitchen.io/dk/index.html#/variation/im/IM_Production/CICD_DKUtils/branch_ci?tab=graph>`_
   recipe variation

  * Make sure you override the ``branch`` variable with the name of your current branch
  * Ensure this recipe passes before merging your PR to master

* Merge your branch into master
* Run `complete_cicd <https://cloud.datakitchen.io/dk/index.html#/variation/im/IM_Production/CICD_DKUtils/complete_cicd?tab=graph>`_
  recipe variation

  * Tags current master with the new semantic version (e.g. v0.5.0)
  * Scans the code for secrets by running :command:`make scan_secrets`
  * Lints the code by running :command:`make lint`
  * Runs the tests by running :command:`make test`
  * Bumps the version by running :command:`make bump/<semantic_version_increment>`
  * Builds and uploads the distribution archives by running :command:`make build` and :command:`make upload`
  * Builds and uploads the documentation by running :command:`make docs`

    * Docs and test & coverage results are published to `DKUtils Website <http://dkutils.dk.io/>`_
    * You must be on the VPN to view the documentation and may need to add ``3.225.225.176  dkutils.dk.io`` to
      your :file:`/etc/hosts` file

* Ensure a new package version was uploaded to `PyPI <https://pypi.org/project/DKUtils/>`_

  * Pip install your new package and run some smoke tests to ensure your new changes are working as expected

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

