from setuptools import setup

setup(
    name='jumpcloud_aws',
    version='0.1',
    py_modules=['jumpcloud_aws'],
    install_requires=[
        'beautifulsoup4==4.5.3',
        'boto3==1.7.22',
        'bs4==0.0.1',
        'requests==2.13.0',
        'six==1.10.0',
        'awscli==1.15.25',
        'click==6.7'
    ],
    entry_points='''
        [console_scripts]
        jumpcloud_aws=jumpcloud_aws:cli
    ''',
)
