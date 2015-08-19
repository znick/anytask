#!/bin/bash

/usr/share/python/anytask/bin/python manage.py runfcgi method=prefork host=127.0.0.1 port=8882 daemonize=false