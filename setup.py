#!/usr/bin/env python
from distutils.core import setup

setup(name='gcalcli',
      version='3.1',
      description='Google Calendar Command Line Interface',
      url='https://github.com/insanum/gcalcli',
      license='MIT',
      scripts=['gcalcli'],
      install_requires = [
        'dateutils',
        'gdata',
        'python-gflags',
        'httplib2',
        'google-api-python-client',
      ],
      extras_require = {
        'vobject':  ["vobject"],
        'parsedatetime': ["parsedatetime"],
      }
)
