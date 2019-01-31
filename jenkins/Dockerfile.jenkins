FROM birkbeckctp/janeway-base:latest

ADD ./src /vol/janeway/src
ADD ./requirements.txt /vol/janeway/requirements.txt
ADD ./dev-requirements.txt /vol/janeway/dev-requirements.txt
ADD ./jenkins/entrypoint.sh /vol/janeway/entrypoint.sh
ADD ./jenkins/janeway_settings.py /vol/janeway/src/core/settings.py

WORKDIR /vol/janeway

RUN pip3 install -r requirements.txt --src /tmp/src
RUN pip3 install -r dev-requirements.txt --src /tmp/src

ENV DB_VENDOR=sqlite
ENV NOSE_INCLUDE_EXE=1

ENTRYPOINT ["./entrypoint.sh"]
