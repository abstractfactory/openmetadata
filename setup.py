# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

f = open('README.md')
readme = f.read().strip()

f = open('LICENSE.md')
license = f.read().strip()

setup(
    name='openmetadata',
    version='0.5.0',
    description='Open Metadata ',
    long_description=readme,
    author='Marcus Ottosson',
    author_email='marcus@abstractfactory.com',
    url='https://github.com/abstractfactory/openmetadata',
    license=license,
    packages=find_packages(exclude=('tests',)),
    include_package_data=True,
    zip_safe=False,
)