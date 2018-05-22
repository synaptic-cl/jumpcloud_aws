from python:3.6

WORKDIR /src
ADD setup.py .
RUN pip install -e . --src /python/libs

ENTRYPOINT [ "jumpcloud_aws" ]
