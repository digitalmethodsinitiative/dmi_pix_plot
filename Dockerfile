FROM continuumio/conda-ci-linux-64-python3.7

WORKDIR /usr/src/app

COPY . /usr/src/app/

RUN pip install -r requirements.txt
