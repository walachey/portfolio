#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages
try: # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
    from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]
dep_links = [str(req_line.url) for req_line in install_reqs]


setup(
    name='portfolio',
    version='0.1',
    description='Simple portfolio visualization',
    author='David Dormagen',
    author_email='david.dormagen@fu-berlin.de',
    url='https://github.com/walachey/portfolio/',
    install_requires=reqs,
    dependency_links=dep_links,
    packages=find_packages(),
    package_dir={'portfolio': 'portfolio/'}
)
