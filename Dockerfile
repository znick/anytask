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
RUN apk update \
    && apk add postgresql-dev gcc python-dev musl-dev \
        libxml2-dev libxslt-dev \
        freetype-dev libpng-dev libjpeg-turbo-dev \
        build-base libzmq zeromq-dev

# RUN apt update
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .

# copy project
COPY . .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

