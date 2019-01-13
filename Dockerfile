FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /pyano
WORKDIR /pyano
ADD requirements.txt /pyano
RUN pip install -r requirements.txt
ADD . /pyano
