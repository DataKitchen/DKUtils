import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="DKUtils",
    version="1.3.1",
    author="DataKitchen",
    author_email="info@datakitchen.io",
    description="DataKitchen Utils Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://ghe.datakitchen.io/DataKitchen/DKUtils",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.6',
    install_requires=[
        "dataclasses>=0.6",
        "jira>=2.0.0",
        "pandas>=1.0.4",
        "paramiko>=2.7.2",
        "scp>=0.13.2",
        "Sphinx>=3.0.1",
        "sphinx-rtd-theme>=0.4.3",
    ],
    tests_require=[
        'bumpversion>=0.5.3',
        'coverage>=5.1',
        'flake8>=3.7.9',
        'nose>=1.3.7',
        'pre-commit>=2.2.0',
        'tox>=3.14.6',
        'yapf>=0.29.0',
    ],
)
