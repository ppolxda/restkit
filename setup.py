# -*- coding: utf-8 -*-
"""
@create: 2019-09-30 13:01:54.

@author: setup

@desc:
"""
from setuptools import setup, find_packages, findall


setup(
    name="restkit",
    version="0.0.14",
    install_requires=[
        'six',
        'tornado',
        'sqlalchemy',
        'cryptography',
    ],
    packages=find_packages('.'),
    package_data={
        '': ['*.txt', '*.md', '*.tmpl', '*.tmlp',
             '*.jinja', '*.json', '*.csv', '*.ts', '*.sql'],
    },
    # entry_points={
    #     "console_scripts": [
    #         "restkit=pypplugins.protoc_gen_json:main",
    #     ]
    # },
    # scripts=bin_list_build(),
    python_requires=">=3.7",
    author="",
    author_email="sa@sa.com",
    description="",
    license="",
    keywords="",
    # url="http://example.com/HelloWorld/",
)
