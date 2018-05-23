from setuptools import setup

setup(
    name='jumpcloud_aws',
    version='0.1',
    packages=['jumpcloud_aws'],
    package_data={
        'jumpcloud_aws': ['config.yml']
    },
    install_requires=[
        'beautifulsoup4==4.5.3',
        'boto3==1.7.22',
        'bs4==0.0.1',
        'requests==2.13.0',
        'six==1.10.0',
        'click==6.7',
        'PyYAML==3.12'
    ],
    entry_points='''
        [console_scripts]
        jumpcloud_aws=jumpcloud_aws.app:cli
    ''',
    python_requires=">==3.6",
    include_package_data=True
)
