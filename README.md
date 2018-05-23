# Saml with to AWS Used JumpCloud
Command to generate credentials for aws-cli when you have SAML authentication with JumpCloud

Source : https://s3.amazonaws.com/awsiammedia/public/sample/SAMLAPICLIADFS/samlapi_formauth.py
Referenced from : https://aws.amazon.com/blogs/security/how-to-implement-a-general-solution-for-federated-apicli-access-using-saml-2-0

#### Requirements

 * python 3.6
 * pip
 * awscli

## Install

```bash
pip3 install git+git://github.com/synaptic-cl/jumpcloud_aws.git@v0.1.4#egg=jumpcloud_aws
```

## Reinstall
```bash
pip3 install git+git://github.com/synaptic-cl/jumpcloud_aws.git@v0.1.4#egg=jumpcloud_aws --upgrade
```

### Use Command

```bash
jumpcloud_aws
# or add params
jumpcloud_aws --email [EMAIL] --password [PASSWORD] --region 0
```

for know the available regions:

```
jumpcloud_aws --help
```



### Use With Docker

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

## TODO
* Tests
* Add validation when not exist the selected region
