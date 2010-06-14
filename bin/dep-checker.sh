#!/bin/sh
su - compliance -c 'cd /opt/linuxfoundation/compliance;python manage.py runserver &' 

sleep 10
xdg-open "http://127.0.0.1:8000/linkage"

