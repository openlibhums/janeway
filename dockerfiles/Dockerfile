FROM birkbeckctp/janeway-base:latest
ARG JANEWAY_SETTINGS_FILE
ENV JANEWAY_SETTINGS_FILE=$JANEWAY_SETTINGS_FILE

ADD . /vol/janeway
WORKDIR /vol/janeway

RUN apt-get update
RUN apt-get install -y pylint
RUN apt-get install -y gettext
RUN pip3 install -r requirements.txt --src /tmp/src
RUN pip3 install -r dev-requirements.txt --src /tmp/src
RUN find "/vol/janeway/src/plugins/" -print -iname "*requirements.txt" -exec pip3 install -r {} --src /tmp/src \;
RUN pip3 install mysqlclient
RUN if [ -n "$(ls -A ./lib)" ]; then pip3 install -e lib/*; fi

RUN mkdir -p /usr/code/janeway/src/core
RUN if [ -f "${JANEWAY_SETTINGS_FILE}" ]; then cp ${JANEWAY_SETTINGS_FILE} /usr/code/janeway/src/core/settings.py; else cp src/core/dev_settings.py /usr/code/janeway/src/core/settings.py; fi

EXPOSE 8000
STOPSIGNAL SIGINT
ENTRYPOINT ["python", "src/manage.py"]
CMD ["runserver", "0.0.0.0:8000"]
