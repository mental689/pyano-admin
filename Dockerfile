FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /pyano
WORKDIR /pyano
ADD requirements.txt /pyano
RUN pip install -r requirements.txt
ADD . /pyano
RUN cd /pyano/thirdparty/pyvision && python3 setup.py install
RUN mkdir -p /pyano/log
RUN python3 manage.py makemigrations
RUN python3 manage.py migrate
#RUN python3 manage.py loaddata shoplifting_example.json