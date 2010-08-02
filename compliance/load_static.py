#!/usr/bin/python

# load_static.py - load static data into the database.
# Copyright 2010 Linux Foundation.
# Jeff Licquia <licquia@linuxfoundation.org>

import os
if __name__ == "__main__":
    os.environ["DJANGO_SETTINGS_MODULE"] = "compliance.settings"

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import datetime

from django.db import transaction
from django.core import exceptions

from compliance.linkage.models import StaticSymbol, StaticLibSearchPath, Meta

def get_library_list():
    lib_list = []
    search_paths = [x.path for x in StaticLibSearchPath.objects.all()]

    # Always load .so.[number] files (dynamic symbols)
    for libpath in search_paths:
        if os.path.isdir(libpath):
            for libfile in os.listdir(libpath):
                if re.search(r'\.so\.\d+$', libfile):
                    lib_list.append(os.path.join(libpath, libfile))

    # For .a files, only load them if a .so.[number] isn't already
    # being loaded.
    for libpath in search_paths:
        if os.path.isdir(libpath):
            for libfile in os.listdir(libpath):
                if re.search(r'\.a$', libfile):
                    solibfile = libfile.replace('.a', '.so')
                    solibpath = os.path.join(libpath, solibfile)

                    # Symlinked .so files.
                    if os.path.islink(solibpath):
                        dynlibpath = os.readlink(solibpath)
                        if dynlibpath in lib_list:
                            continue

                    # ld scripts.
                    elif os.path.exists(solibpath):
                        libtype = os.popen("file " + solibpath).read()
                        if libtype.find("ASCII"):
                            found_so = False
                            solib = open(solibpath)
                            for line in solib:
                                match = re.search(r'GROUP\s*\((.+)\)\s*$', line)
                                if match:
                                    for item in match.group(1).strip().split():
                                        if os.path.exists(item) and \
                                           item in lib_list:
                                            found_so = True
                                            break
                            if found_so:
                                continue

                    lib_list.append(os.path.join(libpath, libfile))

    return lib_list

def get_symbols(lib_fn):
    sym_list = []
    if re.search(r'\.a$', lib_fn):
        objdump = os.popen("objdump -t " + lib_fn)
        for line in objdump:
            if not re.search(r'^\d+', line):
                continue
            items = line.strip().split()
            if "F" in items:
                sym_list.append(items[-1])
    else:
        objdump = os.popen("objdump -T " + lib_fn)
        for line in objdump:
            if line.find(".text") < 0:
                continue
            sym_list.append(line.strip().split()[-1])

    return sym_list

@transaction.commit_on_success
def set_last_update_date():
    try:
        last_update = Meta.objects.get(name="last_staticdb_update")
        last_update.value = str(datetime.date.today())
    except exceptions.ObjectDoesNotExist:
        last_update = Meta(name="last_staticdb_update", 
                           value=str(datetime.date.today()))

    last_update.save()

def get_last_update_date():
    try:
        return Meta.objects.get(name="last_staticdb_update").value
    except (Meta.DoesNotExist, exceptions.ObjectDoesNotExist):
        return None

@transaction.commit_on_success
def load_symbols(lib_fn):
    lib_name = os.path.basename(lib_fn)
    for symbol in get_symbols(lib_fn):
        sym_db = StaticSymbol(symbol=symbol, libraryname=lib_name)
        sym_db.save()

@transaction.commit_manually
def main():
    sys.stdout.write("Clearing out old data...")
    sys.stdout.flush()

    try:
        StaticSymbol.objects.all().delete()
    except:
        transaction.rollback()
        sys.stdout.write("\n")
        raise
    else:
        transaction.commit()
        sys.stdout.write("\n")

    for lib in get_library_list():
        sys.stdout.write("Loading symbols from " + lib + "...")
        sys.stdout.flush()
        load_symbols(lib)
        sys.stdout.write("\r")
        sys.stdout.write(" " * 79)
        sys.stdout.write("\r")
        sys.stdout.flush()
    set_last_update_date()

if __name__ == "__main__":
    main()
