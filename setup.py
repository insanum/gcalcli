#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst',
                                        format='markdown_github',
                                        extra_args=("--no-wrap",))
except:
    long_description = ''

setup(name='gcalcli',
      version='3.4.0',
      maintainer='Eric Davis, Brian Hartvigsen',
      maintainer_email='edavis@insanum.com, brian.andrew@brianandjenny.com',
      description='Google Calendar Command Line Interface',
      long_description=long_description,
      url='https://github.com/insanum/gcalcli',
      license='MIT',
      scripts=['gcalcli'],
      install_requires=[
          'python-dateutil',
          'python-gflags',
          'httplib2',
          'google-api-python-client',
          'oauth2client<=1.4.12'
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
