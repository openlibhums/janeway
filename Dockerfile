FROM python:3.5.4
ADD . /vol/janeway
WORKDIR /vol/janeway
RUN pip3 install -r requirements.txt --src /tmp/src
RUN pip3 install -r dev-requirements.txt --src /tmp/src


