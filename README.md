# Python OAuth2 Middleware

A simple web server that initiates an OAuth2 request and saves the access token.  

## Installation

```bash
   $ python setup.py install
```

## Start the server

You will need to configure your application client IDs and keys and store it a YAML
file. It should look something like this: 

```yaml
github:
   consumerkey: GH_CLIENTID
   consumersecret: GH_CLIENTSECRET
salesforce:
   consumerkey: SF_CLIENTID
   consumersecret: SF_CLIENTID
```

Then we just need to tell the server where to find these credentials and start
the webserver. 

```bash
   $ export POM_SSL=/certificatedir (this step is optional)
   $ export POM_APPS=/myapps/keys.yaml
   $ pomserver 0.0.0.0 8000
```

## Usage

Just point your browser to the web server and specify an authentication source. It
should automatically redirect you. 

- "https://localhost:8000?source=salesforce"
- "https://localhost:8000?source=github"

After authenticating yourself, it will print out your session information. 

## Roadmap

1. Store refresh token in user-configurable data store (i.e., Redis)
2. Additional data sources (InsideSales, LinkedIn, Facebook, Twitter)