FROM python:3.8

RUN apt-get update && apt-get install -y -q python-sphinx texlive texlive-latex-extra pandoc build-essential
RUN cp requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN mkdir docs

WORKDIR /docs
VOLUME /docs

CMD ["/bin/bash"]
