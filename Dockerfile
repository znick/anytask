FROM python:2.7-slim

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Install packages needed to run your application (not build deps):
#   mime-support -- for mime types when serving static files
#   postgresql-client -- for running database commands
# We need to recreate the /usr/share/man/man{1..8} directories first because
# they were clobbered by a parent image.
RUN set -ex \
    && RUN_DEPS=" \
        locales \
        libpcre3 \
        mime-support \
        default-mysql-client \
        libmariadb3 \
        libmagic1 \
        tar \
        gzip \
        bzip2 \
        p7zip-full \
        xz-utils \
        gettext \
    " \
    && seq 1 8 | xargs -I{} mkdir -p /usr/share/man/man{} \
    && apt-get update && apt-get install -y --no-install-recommends $RUN_DEPS \
    && rm -rf /var/lib/apt/lists/*

# Copy in your requirements file
ADD requirements.txt /requirements.txt
# ADD requirements_prod.txt /requirements_prod.txt

# OR, if you’re using a directory for your requirements, copy everything (comment out the above and uncomment this if so):
# ADD requirements /requirements

# Install build deps, then run `pip install`, then remove unneeded build deps all in a single step.
# Correct the path to your production requirements file, if needed.
RUN set -ex \
    && BUILD_DEPS=" \
        build-essential \
        libpcre3-dev \
        libpq-dev \
        default-libmysqlclient-dev \
        default-mysql-client \
    " \
    && apt-get update && apt-get install -y --no-install-recommends $BUILD_DEPS \
    && pip install -U virtualenv \
    && python2.7 -m virtualenv /venv \
    && /venv/bin/pip install -U pip \
    && /venv/bin/pip install --no-cache-dir -r /requirements.txt \
    && /venv/bin/pip install --no-cache-dir dj_database_url \
    && /venv/bin/pip install --no-cache-dir uwsgi \
#    && /venv/bin/pip install --no-cache-dir -r /requirements_prod.txt \
    \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false $BUILD_DEPS \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/log/anytask
RUN chmod a+w /var/log/anytask

# Copy your application code to the container (make sure you create a .dockerignore file if any large files or directories should be excluded)
RUN mkdir /code/
ADD . /code/
#ADD dependencies /
#ADD docker_entrypoint.sh /code/
WORKDIR /code/anytask

# uWSGI will listen on this port
EXPOSE 8000
EXPOSE 3031

# Add any static environment variables needed by Django or your settings file here:
ENV DJANGO_SETTINGS_MODULE=settings_docker

# Call collectstatic (customize the following line with the minimal environment variables needed for manage.py to run):
#RUN /venv/bin/python manage.py collectstatic --noinput
RUN DATABASE_URL='mysql://user:pass@db/app_db' /venv/bin/python manage.py collectstatic --settings=settings_docker --noinput --no-post-process
RUN DATABASE_URL='mysql://user:pass@db/app_db' /venv/bin/python manage.py compilemessages --settings=settings_docker

# Tell uWSGI where to find your wsgi file (change this):
ENV UWSGI_WSGI_FILE=wsgi.py

# Base uWSGI configuration (you shouldn't need to change these):
ENV UWSGI_VIRTUALENV=/venv UWSGI_HTTP=:8000 UWSGI_SOCKET=:3031 UWSGI_MASTER=1 UWSGI_HTTP_AUTO_CHUNKED=1 UWSGI_HTTP_KEEPALIVE=1 UWSGI_UID=1000 UWSGI_GID=2000 UWSGI_LAZY_APPS=1 UWSGI_WSGI_ENV_BEHAVIOR=holy

# Number of uWSGI workers and threads per worker (customize as needed):
ENV UWSGI_WORKERS=2 UWSGI_THREADS=4

# uWSGI static file serving configuration (customize or comment out if not needed):
ENV UWSGI_STATIC_EXPIRES_URI=".*\.(css|js|png|jpg|jpeg|gif|ico|woff|ttf|otf|svg|scss|map|txt) 315360000"

# Deny invalid hosts before they get to Django (uncomment and change to your hostname(s)):
# ENV UWSGI_ROUTE_HOST="^(?!localhost:8000$) break:400"

RUN rm -rf /var/log/anytask/*

# Uncomment after creating your docker-entrypoint.sh
ENTRYPOINT ["/code/docker_entrypoint.sh"]

# Start uWSGI
CMD ["/venv/bin/uwsgi", "--show-config", "--static-map", "/static/=/var/lib/anytask/static", "--static-map", "/media/=/var/lib/anytask/media", "--mime-file", "mime.types", "--mime-file", "/etc/mime.types"]
