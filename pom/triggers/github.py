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
import requests
from requests.exceptions import ConnectionError

class GitHub(object):

    def get_user_info(self):
        user_url = 'https://api.github.com/user'
        payload = { 'access_token' : self.access_token }
        res = requests.get(user_url, params=payload)
        return json.loads(res.text)
        
    def consume_access_key(self, response):
        print str(response)
        self.access_token = response["access_token"]

        user = self.get_user_info()
        print json.dumps(user, 
                         sort_keys=True,
                         indent=2,
                         separators=(',',':'))
        
