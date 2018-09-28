FROM python:2.7

EXPOSE 8000

WORKDIR /app

RUN apt update
RUN apt install -y gettext curl

ADD requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
ADD anytask /app/anytask
ADD dependencies /app/dependencies
ADD configs/docker/settings_local.py /app/anytask/settings_local.py
ADD configs/docker/initial_migrate.sh /app/initial_migrate.sh

RUN python anytask/manage.py compilemessages