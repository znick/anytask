#!/bin/bash

./manage.py import_cs_users  < ../cs_perltask/default.xml

./manage.py import_cs_perltask_students --year=2011 < ../cs_perltask/2011/students.xml
./manage.py import_perltask --year=2011 < ../cs_perltask/2011/perltask.xml

./manage.py import_cs_perltask_students --year=2010 < ../cs_perltask/2010/students.xml
./manage.py import_perltask --year=2010 < ../cs_perltask/2010/perltask.xml

./manage.py import_perltask --year=2009 < ../cs_perltask/2009/perltask.xml
