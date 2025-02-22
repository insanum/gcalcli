#!/usr/bin/env python
from setuptools import setup
from gcalcli import __version__

try:
    import pypandoc
    long_description = pypandoc.convert_file(
        'README.md',
        'rst',
        format='markdown_github',
        extra_args=("--wrap=none",)
    )
except ImportError:
    import sys
    print('Warning: No long description generated.', file=sys.stderr)
    long_description = ''

author_emails = ['edavis@insanum.com',
                 'brian.andrew@brianandjenny.com',
                 'jcrowgey@uw.edu']

setup(name='gcalcli',
      version=__version__,
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
      python_requires='>=3',
      install_requires=[
          'python-dateutil',
          'google-api-python-client>=1.4',
          'httplib2',
          'oauth2client',
          'parsedatetime',
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
          "Programming Language :: Python :: 3",
      ])
