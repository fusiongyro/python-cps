from setuptools import setup
from setuptools import find_packages

setup(
    name="pythoncps",
    version="1.0.0",
    description="pythoncps",
    author="Daniel K Lyons",
    author_email="dlyons@nrao.edu",
    license="GPL3",
    install_requires=[
        "asteval",
    ],
    tests_require=['pytest'],
    packages=find_packages('cps'),
)