#!/bin/sh

cd /opt/linuxfoundation/compliance
su - compliance -c 'python manage.py runserver &' 

xdg-open "http://127.0.0.1:8000/linkage"

