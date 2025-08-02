# pull official base image
FROM python:3.10-slim as base

# set work directory
WORKDIR /usr/paperglobe_web

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apt-get update && apt-get install -y libmagickwand-dev imagemagick tmpreaper && apt-get clean
RUN printf "TMPREAPER_DIRS='/tmp/. /usr/paperglobe_web/app/export/.'\nTMPREAPER_DELAY='256'\nTMPREAPER_TIME=7d\nSHOWWARNING=true\n" > /etc/tmpreaper.conf
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/paperglobe_web/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY ./ /usr/paperglobe_web/

FROM base as web

RUN ./scripts/download_libs.py

FROM base as worker

