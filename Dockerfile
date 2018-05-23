from python:3.6

WORKDIR /src
ADD setup.py .
RUN mkdir jumpcloud_aws/
RUN pip install -e . --src /python/libs

ENTRYPOINT [ "jumpcloud_aws" ]
