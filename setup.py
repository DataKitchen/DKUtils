import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="DKUtils",
    version="2.8.0",
    author="DataKitchen",
    author_email="info@datakitchen.io",
    description="DataKitchen Utils Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DataKitchen/DKUtils",
    project_urls={
        'Documentation': 'https://datakitchen.github.io/DKUtils',
        'Source Code': 'https://github.com/DataKitchen/DKUtils',
        'Download': 'https://pypi.org/project/DKUtils'
    },
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.8',
    install_requires=[
        "dataclasses>=0.6",
        "events_ingestion_client>=0.0.5",
        "jira>=2.0.0",
        "pandas>=1.1.2",
        "paramiko>=2.10.4",
        "scp>=0.13.2",
        "Sphinx>=4.5.0",
        "sphinx-rtd-theme>=0.4.3",
        "google-api-python-client>=1.10.1",
        "google-auth-httplib2>=0.0.4",
        "google-auth-oauthlib>=0.4.2",
        "sqlalchemy>=1.4.27",
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
