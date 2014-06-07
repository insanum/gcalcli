# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Setup script for oauth2client.

Also installs included versions of third party libraries, if those libraries
are not already installed.
"""
from setuptools import setup

packages = [
  'oauth2client',
  'uritemplate',
]

install_requires = [
    'httplib2>=0.8',
    ]

needs_json = False
try:
  import json
except ImportError:
  try:
    import simplejson
  except ImportError:
    needs_json = True

if needs_json:
  install_requires.append('simplejson')

long_desc = """The oauth2client is a client library for OAuth 2.0."""

import oauth2client
version = oauth2client.__version__

setup(name="oauth2client",
      version=version,
      description="OAuth 2.0 client library",
      long_description=long_desc,
      author="Joe Gregorio",
      author_email="jcgregorio@google.com",
      url="http://code.google.com/p/google-api-python-client/",
      install_requires=install_requires,
      packages=packages,
      license="Apache 2.0",
      keywords="google oauth 2.0 http client",
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: Apache Software License',
                   'Operating System :: POSIX',
                   'Topic :: Internet :: WWW/HTTP'])
