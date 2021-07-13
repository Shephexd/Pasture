FROM python:3.7

RUN apt-get update && \
apt-get install -y libgeos-c1v5 libgeos-3.7.1 && \
mkdir -p /webapp/server

ADD . /webapp/server
WORKDIR /webapp/server
RUN pip install -r requirements.txt
CMD ['python3']
