FROM python:3.6
ENV PYTHONUNBUFFERED 1
ADD requirements.txt .gitignore LICENSE manage.py shoplifting_example.json comment/ common/ employer/ pyano_admin/ search/ static/ templates/ vatic/ worker/
WORKDIR .
RUN pip install -r requirements.txt
CMD ["python", "manage.py", "dumpdata", "shoplifting_example.json"]
RUN mkdir -p log/