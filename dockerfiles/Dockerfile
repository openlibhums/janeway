FROM birkbeckctp/janeway-base:latest
ADD . /vol/janeway
WORKDIR /vol/janeway
RUN apt-get update
RUN apt-get install -y pylint
RUN apt-get install -y gettext
RUN pip3 install -r requirements.txt --src /tmp/src
RUN pip3 install -r dev-requirements.txt --src /tmp/src
RUN if [ -n "$(ls -A ./lib)" ]; then pip3 install -e lib/*; fi
RUN cp src/core/janeway_global_settings.py src/core/settings.py

EXPOSE 8000
STOPSIGNAL SIGINT
ENTRYPOINT ["python", "src/manage.py"]
CMD ["runserver", "0.0.0.0:8000"]
