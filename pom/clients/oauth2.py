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
import yaml

class OAuth2(object):

    def __init__(self, name, config_file, key_file):
        self.name = name
        self._read_key_info(config_file)
        self._read_secrets(key_file)

    def _read_key_info(self, config_file):
        yaml_file = open(config_file, 'r')
        config = yaml.load(yaml_file)        
        self.access_token_url = config["access"]
        self.authorize_url = config["authorize"]
        self.token_url = config["token"]
        self.scopes = config["scopes"]
        self.name = os.path.basename(os.path.splitext(config_file)[0])

    def _read_secrets(self, key_file):
        yaml_file = open(key_file, 'r')
        config = yaml.load(yaml_file)        
        self.consumer_key = config[self.name]["consumerkey"]
        self.consumer_secret = config[self.name]["consumersecret"]
