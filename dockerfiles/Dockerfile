FROM birkbeckctp/janeway-base
ADD . /vol/janeway
WORKDIR /vol/janeway
RUN apt-get update
RUN apt-get install -y pylint
RUN pip3 install -r requirements.txt --src /tmp/src
RUN pip3 install -r dev-requirements.txt --src /tmp/src
RUN cp src/core/janeway_global_settings.py src/core/settings.py

EXPOSE 8000
STOPSIGNAL SIGINT
ENTRYPOINT ["python", "src/manage.py"]
CMD ["runserver", "0.0.0.0:8000"]
