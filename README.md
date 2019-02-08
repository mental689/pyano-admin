PYANO-admin
====

![PYANO](./static/images/favicon.ico)

## Introduction

This enhanced version of [PYANO framework](http://github.com/mental689/pyano) is to implement a `many-to-many` model to data collection and annotation process using PYANO.
The old PYANO framework only supports `one-to-many` models (`one` project owner versus `many` workers).
PYANO-admin enables PYANO to have `many` project owners with fundamental operations such as adding, maintaining topics, jobs, tasks (keyword search, QBE search, web-based surveys and space-time annotations) with large degree of automation in mind.
PYANO-amdin is similar to PYANO, it is a semi-automatic framework.


## Installation

* You need to build [`pyvision`](https://github.com/cvondrick/pyvision.git).

* Then install the package using
```bash
$ python3 setup.py install
```
All dependencies will be downloaded and installed with this single command.
However, as recommended by [CVAT developers](https://github.com/opencv/cvat/issues/229#issuecomment-446593986), you should take a look at our docker branch, which provide a more easy-to-use and trouble-free solution for almost all situations.
We have a plan to release a docker to DockerHub when all features are in a good condition.