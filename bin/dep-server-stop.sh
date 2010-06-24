#!/bin/sh
ps ax | grep manage.py | grep -v grep | awk '{print $1}' | xargs kill
