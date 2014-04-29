# -*- coding: utf-8 -*-
import os
import sys

path = os.path.dirname(__file__)
sys.path.insert(0, path)

import openmetadata
version = openmetadata.version

from setuptools import setup, find_packages

f = open('README.md')
readme = f.read().strip()

f = open('LICENSE.md')
license = f.read().strip()



setup(
    name='openmetadata',
    version=version,
    description='Open Metadata ',
    # long_description=readme,
    author='Marcus Ottosson',
    author_email='marcus@abstractfactory.com',
    url='https://github.com/abstractfactory/openmetadata',
    license=license,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)