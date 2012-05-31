#!/usr/bin/env python

from setuptools import setup, find_packages

tests_require = [
]

setup(
    name='nose-bisect',
    version='0.1.0',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    description='A Nose plugin which allows bisection of test failures.',
    url='http://github.com/dcramer/nose-bisect',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    zip_safe=False,
    install_requires=[
        'nose>=1.0,<2.0',
    ],
    entry_points={
       'nose.plugins.0.10': [
            'nose_bisect = nose_bisect.plugin:BisectPlugin'
        ]
    },
    license='Apache License 2.0',
    tests_require=tests_require,
    extras_require={'test': tests_require},
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
