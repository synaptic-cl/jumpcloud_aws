# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys
import boto.sts
import boto.s3
import requests
import getpass
import ConfigParser
import base64
import logging
import xml.etree.ElementTree as ET
import re
from bs4 import BeautifulSoup
from os.path import expanduser
from urlparse import urlparse

##########################################################################
# Variables

# region: The default AWS region that this script will connect
# to for all API calls
region = 'us-west-2'

# output format: The AWS CLI output format that will be configured in the
# saml profile (affects subsequent CLI calls)
outputformat = 'json'

# awsconfigfile: The file where this script will store the temp
# credentials under the saml profile
awsconfigfile = '/.aws/credentials'

# SSL certificate verification: Whether or not strict certificate
# verification is done, False should only be used for dev/test
sslverification = True

# idpentryurl: The initial url that starts the authentication process.
idpentryurl = 'https://sso.jumpcloud.com/saml2/aws'

# Uncomment to enable low level debugging
logging.basicConfig(level=logging.INFO)

##########################################################################

# Get the federated credentials from the user
print "Email:",
username = raw_input()
password = getpass.getpass()

print("1) us-east-1 / US East (N. Virginia)")
print("2) us-east-2 / US East (Ohio)")
print("3) us-west-1 / US West (N. California)")
print("4) us-west-2 / US West (Oregon)")
print("5) ca-central-1 / Canada (Central)")
print("6) eu-west-1 / EU (Ireland)")
print("7) eu-central-1 / EU (Frankfurt)")
print("8) eu-west-2 / EU (London)")
print("9) ap-northeast-1 / Asia Pacific (Tokyo)")
print("10) ap-northeast-2 / Asia Pacific (Seoul)")
print("11) ap-southeast-1 / Asia Pacific (Singapore)")
print("12) ap-southeast-2 / Asia Pacific (Sydney)")
print("13) ap-south-1 / Asia Pacific (Mumbai)")
print("14) sa-east-1 / South America (São Paulo)")
print("Select Region:"),
num_region = raw_input()
if not num_region or not num_region.isdigit():
    num_region = 1
    print("Region default: us-east-1 / US East (N. Virginia)")
else:
    num_region = int(num_region)

# Initiate session handler
session = requests.Session()

# Programmatically get the SAML assertion
# Opens the initial IdP url and follows all of the HTTP302 redirects, and
# gets the resulting login page
formresponse = session.get(idpentryurl, verify=sslverification)
# Capture the idpauthformsubmiturl, which is the final url after all the 302s
idpauthformsubmiturl = formresponse.url

# Parse the response and extract all the necessary values
# in order to build a dictionary of all of the form values the IdP expects
formsoup = BeautifulSoup(formresponse.text.decode('utf8'), "html.parser")
payload = {}

for inputtag in formsoup.find_all(re.compile('(INPUT|input)')):
    name = inputtag.get('name', '')
    value = inputtag.get('value', '')
    if "user" in name.lower():
        # Make an educated guess that this is the right field for the username
        payload[name] = username
    elif "email" in name.lower():
        # Some IdPs also label the username field as 'email'
        payload[name] = username
    elif "pass" in name.lower():
        # Make an educated guess that this is the right field for the password
        payload[name] = password
    else:
        # Simply populate the parameter with the existing value (picks up hidden fields
        # in the login form)
        payload[name] = value

# Debug the parameter payload if needed
# Use with caution since this will print sensitive output to the screen

# Some IdPs don't explicitly set a form action, but if one is set we should
# build the idpauthformsubmiturl by combining the scheme and hostname
# from the entry url with the form action target
# If the action tag doesn't exist, we just stick with the
# idpauthformsubmiturl above
for inputtag in formsoup.find_all(re.compile('(FORM|form)')):
    action = inputtag.get('action')
    if action:
        parsedurl = urlparse(idpentryurl)
        idpauthformsubmiturl = '%s://%s/%s' % (parsedurl.scheme, parsedurl.netloc, action)

# Performs the submission of the IdP login form with the above post data
response = session.post(
    idpauthformsubmiturl, data=payload, verify=sslverification)

# Debug the response if needed

# Overwrite and delete the credential variables, just for safety
username = '##############################################'
password = '##############################################'
del username
del password

# Decode the response and extract the SAML assertion
soup = BeautifulSoup(response.text.decode('utf8'), "html.parser")
assertion = ''

# Look for the SAMLResponse attribute of the input tag (determined by
# analyzing the debug print lines above)
for inputtag in soup.find_all('input'):
    if(inputtag.get('name') == 'SAMLResponse'):
        assertion = inputtag.get('value')

# Better error handling is required for production use.
if (assertion == ''):
    # TODO: Insert valid error checking/handling
    print 'Response did not contain a valid SAML assertion'
    sys.exit(0)

# Debug only
# print(base64.b64decode(assertion))

# Parse the returned assertion and extract the authorized roles
awsroles = []
root = ET.fromstring(base64.b64decode(assertion))
for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
    if (saml2attribute.get('Name') == 'https://aws.amazon.com/SAML/Attributes/Role'):
        saml2attribute = saml2attribute.iter(
            '{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'
        )
        for saml2attributevalue in saml2attribute:
            awsroles.append(saml2attributevalue.text)

# Note the format of the attribute value should be role_arn,principal_arn
# but lots of blogs list it as principal_arn,role_arn so let's reverse
# them if needed
for awsrole in awsroles:
    chunks = awsrole.split(',')
    if'saml-provider' in chunks[0]:
        newawsrole = chunks[1] + ',' + chunks[0]
        index = awsroles.index(awsrole)
        awsroles.insert(index, newawsrole)
        awsroles.remove(awsrole)

# If I have more than one role, ask the user which one they want,
# otherwise just proceed
print ""
if len(awsroles) > 1:
    i = 0
    print "Please choose the role you would like to assume:"
    for awsrole in awsroles:
        print '[', i, ']: ', awsrole.split(',')[0]
        i += 1
    print "Selection: ",
    selectedroleindex = raw_input()

    # Basic sanity check of input
    if int(selectedroleindex) > (len(awsroles) - 1):
        print 'You selected an invalid role index, please try again'
        sys.exit(0)

    role_arn = awsroles[int(selectedroleindex)].split(',')[0]
    principal_arn = awsroles[int(selectedroleindex)].split(',')[1]
else:
    role_arn = awsroles[0].split(',')[0]
    principal_arn = awsroles[0].split(',')[1]

# Use the assertion to get an AWS STS token using Assume Role with SAML
regions = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "ca-central-1",
    "eu-west-1",
    "eu-central-1",
    "eu-west-2",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-south-1",
    "sa-east-1"
]
region_selected = regions[num_region - 1]
conn = boto.sts.connect_to_region(region_selected)
token = conn.assume_role_with_saml(role_arn, principal_arn, assertion)

# Write the AWS STS token into the AWS credential file
home = expanduser("~")
filename = home + awsconfigfile

# Read in the existing config file
config = ConfigParser.RawConfigParser()
config.read(filename)

# Put the credentials into a saml specific section instead of clobbering
# the default credentials
if not config.has_section('default'):
    config.add_section('default')

config.set('default', 'output', outputformat)
config.set('default', 'region', region_selected)
config.set('default', 'aws_access_key_id', token.credentials.access_key)
config.set('default', 'aws_secret_access_key', token.credentials.secret_key)
config.set('default', 'aws_session_token', token.credentials.session_token)

# Write the updated config file
with open(filename, 'w+') as configfile:
    config.write(configfile)

# Give the user some basic info as to what has just happened
print '\n\n----------------------------------------------------------------'
print """Your new access key pair has been stored in the AWS configuration file {0} under the saml profile.""".format(filename)
print 'Note that it will expire at {0}.'.format(token.credentials.expiration)
print 'After this time, you may safely rerun this script to refresh your access key pair.'
print 'To use this credential, call the AWS CLI with the --profile option (e.g. aws --profile saml ec2 describe-instances).'
print '----------------------------------------------------------------\n\n'
