PYANO-admin
====

![PYANO](./static/images/favicon.ico)

## Introduction

This enhanced version of [PYANO framework](http://github.com/mental689/pyano) is to implement a `many-to-many` model to data collection and annotation process using PYANO.
The old PYANO framework only supports `one-to-many` models (`one` project owner versus `many` workers).
PYANO-admin enables PYANO to have `many` project owners with fundamental operations such as adding, maintaining topics, jobs, tasks (keyword search, QBE search, web-based surveys and space-time annotations) with large degree of automation in mind.
PYANO-amdin is similar to PYANO, it is a semi-automatic framework.


## Usage

### Docker
To build a docker image, and then run the image:
```bash
$ sudo docker-compose up --build
``` 

After that, you can access the service website at [http://localhost:8000/](http://localhost:8000/)