#!/bin/env python3

from setuptools import setup
from setuptools import find_packages

setup(
    name='pytest-loki',
    version='0.1.2',
    description='Report test metrics to a loki instance',
    author='Quentin Anglade',
    author_email='dev@easymile.com',
    packages=find_packages(),
    platforms='any',
    python_requires='>3.8',
    install_requires=[
        'requests',
        'pytest'
    ],
    entry_points={
        'pytest11': [
            'loki = pytest_loki'
        ]
    },
    classifiers=[
        "Framework :: Pytest",
    ]
)
