FROM python:3.8

ADD . /docs
RUN apt-get update && apt-get install -y -q sphinx-doc sphinx-common texlive texlive-latex-extra pandoc build-essential
RUN pip install -r /docs/requirements.txt

WORKDIR /docs

CMD ["/bin/bash"]
