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

from flask import Flask, request, redirect, url_for
import json
import os
from pom.triggers.poster import Poster
from pom.triggers.github import GitHub
from pom.triggers.salesforce import Salesforce
from pom.clients.oauth2 import OAuth2
import requests
from requests.exceptions import ConnectionError
import sys
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import urllib
from uuid import uuid4
import yaml

app = Flask(__name__)

# 
# Read in all the known oauth providers. 
# 
CONFIG_DIR = os.path.dirname(os.path.dirname(__file__)) + "/config"
providers = {}
for f in os.listdir(CONFIG_DIR + "/providers"):
    n, e = os.path.splitext(f)
    print "Source: " + n
    providers[n] = OAuth2(n, CONFIG_DIR + "/providers/" + f, os.environ['POM_APPS'])

#
# Instantiate all the triggers. 
# 
triggers = []
yaml_file = open(CONFIG_DIR + "/pom.yaml", 'r')
config = yaml.load(yaml_file)        
redirect_uri = config["callback"]

if 'triggers' in config:
    trigger_list = config["triggers"].split(",")
    for t in trigger_list:
        if t == "github": 
            triggers.append(GitHub())
        elif t == "salesforce": 
            triggers.append(Salesforce())
        elif t == "poster": 
            triggers.append(Poster())
else:
    trigger_list = []
#
# Responses store the oauth state machine. 
#
responses = {}

#
# The default page redirects the user to the source OAuth page. 
#
@app.route('/', methods=['GET'])
def authorize():
    state = str(uuid4())
 
    if 'session' in request.args:
        session = request.args['session']
    else:
        session = state

    if 'source' in request.args:
        source = providers[request.args['source']]
        print "Using the %s OAuth server" % source
    else:
        print "Using the Salesforce OAuth server"
        source = providers["salesforce"]

    payload = { 'scope' : source.scopes,
                'state' : state, 
                'redirect_uri' : redirect_uri + '/' + source.name,
                'response_type' : 'code', 
                'client_id' : source.consumer_key,
                'access_type' : 'offline'}

    url = source.authorize_url + "?" + urllib.urlencode(payload)
    responses[state] = { 'stage' : 'authorize',
                         'session' : session }

    if 'redirect' in request.args:
        responses[state]['redirect'] = request.args['redirect']
        print "Using the %s user redirect" % responses[state]['redirect']
    
    return redirect(url)

#
# Fetch a new access token using a refresh token. 
#
@app.route('/refresh', methods=['DELETE'])
def revoke_access_token():
    refresh_token = request.args['refresh']
    source = providers[request.args['source']]
    payload = { 'token' : refresh_token }

    resp = requests.post(source.revoke_url, params = payload)
    return resp.text

#
# Fetch a new access token using a refresh token. 
#
@app.route('/refresh', methods=['GET'])
def refresh_access_token():
    refresh_token = request.args['refresh']
    source = providers[request.args['source']]

    print "refreshing with " + refresh_token
    payload = { 'client_id' : source.consumer_key,
                'client_secret' : source.consumer_secret, 
                'grant_type' : 'authorization_code', 
                'refesh_token' : refresh_token }

    resp = requests.post(source.token_url, params = payload)
    return resp.text
                        
def _get_access_token(source, auth_code, state, session, redirect=None):
    try:
        payload = { 'client_id' : source.consumer_key,
                    'client_secret' : source.consumer_secret,
                    'grant_type' : 'authorization_code', 
                    'code' : auth_code,
                    'redirect_uri' : redirect_uri + '/' + source.name} 

        headers = {'Accept' : 'application/json'}
        # headers = {'content-type': 'application/x-www-form-urlencoded',
        #            'content-length' : 256}

        res = requests.post(source.access_token_url, 
                            data = payload,
                            headers = headers) 

        if res.status_code == requests.codes.ok:
            resp_json = res.json()
            print "JSON response: " + str(resp_json)

            if 'access_token' in resp_json:
                resp = None

                if redirect:
                    resp_json['_user_redirect'] = redirect

                for t in triggers:
                    resp = t.consume_access_key(resp_json)

                responses[state] = { 'stage' : 'authorized',
                                     'resp' : resp_json }

                if resp:
                    return resp.text
                else:
                    return json.dumps( {'status' : 'authorized',
                                        'session' : session } )
            else:
                error_msg = "unauthorized"
        else:
            error_msg = "unreachable"

        return json.dumps( {"status" : "failed",
                            "error" : error_msg,
                            "session" : session } )

    except ConnectionError as e:
        print str(e)

#
# The generic callback method. Should be supplemented with the provider source
# name so that we know what to do. 
#                            
@app.route('/callback/<source_name>', methods=['GET'])
def callback(source_name):
    source = providers[source_name]
    if 'code' in request.args:
        auth_code = request.args["code"]
        state = request.args["state"]
        session = responses[state]['session']

        if 'redirect' in responses[state]:
            redirect = responses[state]['redirect']
        else:
            redirect = None

        responses[state]['stage'] = 'callback'
        return _get_access_token(source, auth_code, state, session, redirect)
    else:
        return json.dumps( {'status' : 'failed',
                            'error' : 'authentication' } )

#
# Retrieve the access & refresh keys. 
#
@app.route('/key', methods=['GET'])
def key():
    if 'session' in request.args and request.args['session'] in responses:
        resp = responses[request.args['session']]
        if resp['stage'] == 'authorized':
            return resp['resp']['access_key']

    return json.dumps( {'status' : 'failed',
                        'error' : 'could not find access key' } )

def main():
    if 'POM_SSL' in os.environ:
        key_dir = os.environ['POM_SSL']
    else:
        key_dir = os.path.dirname(os.path.dirname(__file__)) + "/keys"

    if not 'POM_APPS' in os.environ:
        print "POM_APPS should be set to a directory with our application OAuth credentials"
        exit(1)

    print "Using SSL certificate in " + key_dir
    try:
        http_server = HTTPServer(WSGIContainer(app),
                                 ssl_options={
                                     "certfile": key_dir + "/server.crt",
                                     "keyfile": key_dir + "/server.key",
                                 })
        http_server.listen(port=int(sys.argv[2]),
                           address=sys.argv[1])
        IOLoop.instance().start()
    except:
        pass
