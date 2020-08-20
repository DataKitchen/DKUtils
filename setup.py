import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="DKUtils",
    version="0.13.0",
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
    install_requires=["setuptools>=46.1.3", "twine>=3.1.1", "wheel>=0.34.2"],
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
