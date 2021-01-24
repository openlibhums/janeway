FROM birkbeckctp/janeway-base:latest
ADD . /vol/janeway
WORKDIR /vol/janeway
RUN apt-get update
RUN apt-get install -y pylint
RUN apt-get install -y libgirepository1.0-dev
RUN apt-get install -y gir1.2-poppler-0.18
RUN apt-get install -y gir1.2-gdkpixbuf-2.0
RUN apt-get install -y exiftool
RUN apt-get install -y gir1.2-rsvg-2.0
RUN apt-get install -y libimage-exiftool-perl
RUN apt-get install -y python3-gi-cairo
RUN pip3 install -r requirements.txt --src /tmp/src
RUN pip3 install -r dev-requirements.txt --src /tmp/src
RUN if [ -n "$(ls -A ./lib)" ]; then pip3 install -e lib/*; fi
RUN cp src/core/janeway_global_settings.py src/core/settings.py

EXPOSE 8000
STOPSIGNAL SIGINT
ENTRYPOINT ["python", "src/manage.py"]
CMD ["runserver", "0.0.0.0:8000"]
