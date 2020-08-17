
# Copyright (c) 2014 Ahmed H. Ismail
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import json
import os

from spdx.version import Version

_base_dir = os.path.dirname(__file__)
_licenses = os.path.join(_base_dir, 'licenses.json')
_exceptions = os.path.join(_base_dir, 'exceptions.json')


def load_license_list(file_name):
    """
    Return the licenses list version tuple and a mapping of licenses
    name->id and id->name loaded from a JSON file
    from https://github.com/spdx/license-list-data
    """
    licenses_map = {}
    with codecs.open(file_name, 'rb', encoding='utf-8') as lics:
        licenses = json.load(lics)
        version = licenses['licenseListVersion'].split('.')
        for lic in licenses['licenses']:
            if lic.get('isDeprecatedLicenseId'):
                continue
            name = lic['name']
            identifier = lic['licenseId']
            licenses_map[name] = identifier
            licenses_map[identifier] = name
    return version, licenses_map


def load_exception_list(file_name):
    """
    Return the exceptions list version tuple and a mapping of exceptions
    name->id and id->name loaded from a JSON file
    from https://github.com/spdx/license-list-data
    """
    exceptions_map = {}
    with codecs.open(file_name, 'rb', encoding='utf-8') as excs:
        exceptions = json.load(excs)
        version = exceptions['licenseListVersion'].split('.')
        for exc in exceptions['exceptions']:
            if exc.get('isDeprecatedLicenseId'):
                continue
            name = exc['name']
            identifier = exc['licenseExceptionId']
            exceptions_map[name] = identifier
            exceptions_map[identifier] = name
    return version, exceptions_map


(_major, _minor), LICENSE_MAP = load_license_list(_licenses)
LICENSE_LIST_VERSION = Version(major=_major, minor=_minor)

(_major, _minor), EXCEPTION_MAP = load_exception_list(_exceptions)
EXCEPTION_LIST_VERSION = Version(major=_major, minor=_minor)