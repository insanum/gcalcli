#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst', 'md')
except:
    long_description = ''

setup(name='gcalcli',
      version='3.2-dev',
      maintainer='Eric Davis, Brian Hartvigsen',
      maintainer_email='edavis@insanum.com, brian.andrew@brianandjenny.com',
      description='Google Calendar Command Line Interface',
      long_description=long_description,
      url='https://github.com/insanum/gcalcli',
      license='MIT',
      scripts=['gcalcli'],
      install_requires=[
          'dateutils',
          'python-gflags',
          'httplib2',
          'google-api-python-client',
      ],
      extras_require={
          'vobject':  ["vobject"],
          'parsedatetime': ["parsedatetime"],
      },
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "Intended Audience :: End Users/Desktop",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
      ])
