# Copyright 2014 Cirruspath, Inc. 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: James Horey
# Email: jhorey@cirruspath.com
#

import json
import os
import requests
from requests.exceptions import ConnectionError

class Poster(object):

    def __init__(self):
        self.service_uri = os.environ['POM_RELAY_URI']

    def consume_access_key(self, response):
        if self.service_uri:
            try:
                print "Relaying to " + self.service_uri
                requests.post(self.service_uri, data = response)
            except:
                print "Could not relay access token"
                
