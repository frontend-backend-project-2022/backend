#!/bin/bash
docker build . --file images/python:3.8/Dockerfile --tag web-ide/python:3.8
docker build . --file images/python:3.9/Dockerfile --tag web-ide/python:3.9
docker build . --file images/python:3.10/Dockerfile --tag web-ide/python:3.10
docker build . --file images/clang:14/Dockerfile --tag web-ide/clang:14
docker build . --file images/gcc:8.3/Dockerfile --tag web-ide/gcc:8.3
docker build . --file images/node:16.17/Dockerfile --tag web-ide/node:16.17
docker build . --file images/node:18.7/Dockerfile --tag web-ide/node:18.7