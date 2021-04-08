# https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/

# pull official base image
FROM python:2.7-alpine

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
# install psycopg2 dependencies
RUN apk update alpine-sdk \
    && apk add gcc postgresql-dev python-dev musl-dev \
        libxml2-dev libxslt-dev \
        freetype-dev libpng-dev libjpeg-turbo-dev \
        build-base libzmq zeromq-dev \
        git \
    && apk add --no-cache mariadb-dev  # for MySQL

# RUN apt update
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .

# copy project
COPY . .
RUN git submodule update --init --recursive

# cd to anytask
WORKDIR /usr/src/app/anytask

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

