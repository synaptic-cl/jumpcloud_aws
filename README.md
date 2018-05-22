# Saml with to AWS Used JumpCloud Api
Script to generate credential for aws-cli when you have SAML authentication with JumpCloud
Command to generate credentials for aws-cli when you have SAML authentication with JumpCloud

Source : https://s3.amazonaws.com/awsiammedia/public/sample/SAMLAPICLIADFS/samlapi_formauth.py
Referenced from : https://aws.amazon.com/blogs/security/how-to-implement-a-general-solution-for-federated-apicli-access-using-saml-2-0

#### Requirements

 * python 3.6
 * pip

## Install

```bash

```



# User With Docker

```bash
# Build
docker build -t saml .
# Run
docker run --rm -it -v $(pwd)/:/src -v $HOME/.aws/credentials:/root/.aws/credentials saml
```



## Developer

#### Requirements

* Docker > 18.03

```bash
# Build
docker build -t saml .
# Run
docker run --rm -it -v $(pwd)/:/src -v $HOME/.aws/credentials:/root/.aws/credentials saml
```

## Install aws-cli

```
# macOS
brew install awscli
```

### Config

Add in your file ~/.aws/credentials the next configs:

```
[default]
output =
region =
aws_access_key_id =
aws_secret_access_key =
aws_session_token =
```

# python

```
pip install requirements.txt
python saml_jumpcloud_api.py
# Then enter your email, password and aws region
```
