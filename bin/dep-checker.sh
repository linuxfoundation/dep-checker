#!/bin/sh

pathlist=". .. /opt/linuxfoundation"

# Find the path to the project.

for path in $pathlist; do
    if [ -e "$path/bin/readelf.py" ]; then
	depchecker_path="$path"
    fi
done

if [ \! -e "$depchecker_path/bin/readelf.py" ]; then
    echo "could not find path to dep-checker" >&2
    exit 1
fi

# Determine if we need to switch users.

if [ $(whoami) == "root" ]; then
    SU_CMD="su - compliance -c"
else
    SU_CMD="/bin/sh -c"
fi

$SU_CMD "cd $depchecker_path/compliance; python manage.py runserver &" 

sleep 10
xdg-open "http://127.0.0.1:8000/linkage"

