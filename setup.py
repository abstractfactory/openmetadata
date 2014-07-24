# -*- coding: utf-8 -*-
import os
import sys

path = os.path.dirname(__file__)
sys.path.insert(0, path)

import openmetadata
from setuptools import setup, find_packages

version = openmetadata.version

with open('README.txt') as f:
    readme = f.read()

classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Utilities'
]

setup(
    name='openmetadata',
    version=version,
    description='Open Metadata',
    long_description=readme,
    author='Marcus Ottosson',
    author_email='marcus@abstractfactory.com',
    url='https://github.com/abstractfactory/openmetadata',
    license="LICENSE.txt",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': ['openmetadata = openmetadata.cli:main',
                            'om = openmetadata.cli:main']
    },
    classifiers=classifiers
)
