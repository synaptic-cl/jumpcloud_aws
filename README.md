# saml_aws_jumpcloud_api
Script to generate credential for aws-cli when you have SAML authentication with JumpCloud

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
