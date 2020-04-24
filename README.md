# DKUtils


This python package is intended to house utility functions and classes that are used in DataKitchen recipes.

Building and testing this module is conveniently done using Make. Issue the `make` command to see a list
of available targets (shown below for convenience). Note that any target can be suffixed with `-ext` to 
run that target inside a Docker container. This allows testing and development in a standard and portable
environment. To develop inside a running docker container, use the `bash-ext` target. This will drop the 
user into a bash shell inside a running container.

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

[Pre-commit](https://pre-commit.com/) is also included to validate and flag commits that contain code 
that does not pass [Flake8](http://flake8.pycqa.org/en/latest/) and [YAPF](https://github.com/google/yapf). 
To use, first install the python package `pip install pre-commit` and then run `pre-commit install`. All 
future commits will run these tools and deny commits that don't pass. When running YAPF, `pre-commit` will
make in-place corrections to your code. Therefore, if it fails the YAPF validation on the first commit 
attempt, simply review the changed files, add, and commit again to resolve.  
