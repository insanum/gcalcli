#!/usr/bin/env python
from __future__ import print_function
from setuptools import setup

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst',
                                        format='markdown_github',
                                        extra_args=("--wrap=none",))
except ImportError:
    import sys
    print('Warning: No long description generated.', file=sys.stderr)
    long_description = ''

author_emails = ['edavis@insanum.com',
                 'brian.andrew@brianandjenny.com',
                 'jcrowgey@uw.edu']

setup(name='gcalcli',
      version='4.1.0',
      author='Eric Davis, Brian Hartvigsen, Joshua Crowgey',
      author_email=', '.join(author_emails),
      maintainer='Joshua Crowgey',
      maintainer_email='jcrowgey@uw.edu',
      description='Google Calendar Command Line Interface',
      long_description=long_description,
      url='https://github.com/insanum/gcalcli',
      license='MIT',
      packages=['gcalcli'],
      data_files=[('share/man/man1', ['docs/man1/gcalcli.1'])],
      install_requires=[
          'python-dateutil',
          'google-api-python-client>=1.4',
          'httplib2',
          'oauth2client',
          'parsedatetime',
          'six'
      ],
      extras_require={
          'vobject': ["vobject"],
      },
      entry_points={
          'console_scripts':
              ['gcalcli=gcalcli.cli:main'],
      },
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "Intended Audience :: End Users/Desktop",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
      ])
