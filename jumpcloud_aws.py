# -*- coding: utf-8 -*-
# !/usr/bin/python

import os
import sys
import boto3
import requests
import configparser
import base64
import xml.etree.ElementTree as ET
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import click
import yaml


CFG = {}
with open("config.yml", 'r') as ymlfile:
    CFG = yaml.load(ymlfile)
regions = '\n'.join(
    ["%s) %s" % (i, x['name']) for i, x in enumerate(CFG.get('regions', []))]
)


def saml_assertion(username, password):
    # Initiate session handler
    session = requests.Session()
    url = CFG.get('url_sso_aws')

    # Programmatically get the SAML assertion
    # Opens the initial IdP url and follows all of the HTTP302 redirects, and
    # gets the resulting login page
    formresponse = session.get(url, verify=True)
    # Capture the idpauthformsubmiturl, which is the final url after all the 302s
    idpauthformsubmiturl = formresponse.url

    # Parse the response and extract all the necessary values
    # in order to build a dictionary of all of the form values the IdP expects
    formsoup = BeautifulSoup(formresponse.text, "html.parser")
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
            # Simply populate the parameter with the existing value
            # (picks up hidden fields
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
            parsedurl = urlparse(url)
            idpauthformsubmiturl = '%s://%s/%s' % (
                parsedurl.scheme,
                parsedurl.netloc,
                action
            )
    # Performs the submission of the IdP login form with the above post data
    response = session.post(
        idpauthformsubmiturl,
        data=payload,
        verify=True
    )

    # Decode the response and extract the SAML assertion
    soup = BeautifulSoup(response.text, "html.parser")
    assertion = ''

    # Look for the SAMLResponse attribute of the input tag (determined by
    # analyzing the debug print lines above)
    for inputtag in soup.find_all('input'):
        if(inputtag.get('name') == 'SAMLResponse'):
            assertion = inputtag.get('value')

    # Better error handling is required for production use.
    if (assertion == ''):
        # TODO: Insert valid error checking/handling
        print('Response did not contain a valid SAML assertion')
        sys.exit(0)

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

    # TODO
    # If I have more than one role, ask the user which one they want,
    # otherwise just proceed
    # print ("")
    # if len(awsroles) > 1:
    #     i = 0
    #     print ("Please choose the role you would like to assume:")
    #     for awsrole in awsroles:
    #         print ('[', i, ']: ', awsrole.split(',')[0])
    #         i += 1
    #     print ("Selection: ",)
    #     selectedroleindex = raw_input()

    #     # Basic sanity check of input
    #     if int(selectedroleindex) > (len(awsroles) - 1):
    #         print ('You selected an invalid role index, please try again')
    #         sys.exit(0)

    #     role_arn = awsroles[int(selectedroleindex)].split(',')[0]
    #     principal_arn = awsroles[int(selectedroleindex)].split(',')[1]
    # else:
    #     role_arn = awsroles[0].split(',')[0]
    #     principal_arn = awsroles[0].split(',')[1]
    role_arn = awsroles[0].split(',')[0]
    principal_arn = awsroles[0].split(',')[1]
    client = boto3.client('sts')
    token = client.assume_role_with_saml(
        RoleArn=role_arn,
        PrincipalArn=principal_arn,
        SAMLAssertion=assertion
    )
    return token


@click.command()
@click.option('--email', prompt=True, help="Your email")
@click.option('--password', prompt=True, hide_input=True, help="Your Password")
@click.option('--region',
    prompt=regions + "\nSelected Region",
    help="Selected a region:\n\n" + regions
)
def cli(email, password, region):

    token = saml_assertion(email, password)
    path_filename = os.path.join(
        os.path.expanduser(CFG.get('path_file')),
        CFG.get('filename')
    )

    config = configparser.RawConfigParser()
    config.read(path_filename)
    config.set(configparser.DEFAULTSECT, 'output', CFG.get('outputformat'))
    config.set(
        configparser.DEFAULTSECT,
        'region',
        CFG['regions'][int(region)]['id']
    )
    config.set(
        configparser.DEFAULTSECT,
        'aws_access_key_id',
        token['Credentials']['AccessKeyId']
    )
    config.set(
        configparser.DEFAULTSECT,
        'aws_secret_access_key',
        token['Credentials']['SecretAccessKey']
    )
    config.set(
        configparser.DEFAULTSECT,
        'aws_session_token',
        token['Credentials']['SessionToken']
    )
    if not os.path.exists(os.path.expanduser(CFG.get('path_file'))):
        os.mkdir(os.path.expanduser(CFG.get('path_file')))

    # Write the updated config file
    with open(path_filename, 'w+') as configfile:
        config.write(configfile)
    # Give the user some basic info as to what has just happened
    print ('\n----------------------------------------------------------------')
    print ("""Your new access key pair has been stored in the AWS configuration file {0} under the saml profile.""".format(path_filename))
    print ('Note that it will expire at {0}.'.format(token['Credentials']['Expiration']))
    print ('After this time, you may safely rerun this script to refresh your access key pair.')
    print ('To use this credential, call the AWS CLI with the --profile option (e.g. aws --profile saml ec2 describe-instances).')
    print ('----------------------------------------------------------------\n\n')
