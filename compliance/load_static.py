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

from django.db import transaction

from compliance.linkage.models import StaticSymbol

def get_library_list():
    lib_list = []
    for libpath in ("/lib", "/usr/lib"):
        for libfile in os.listdir(libpath):
            if re.search(r'\.so\.\d+$', libfile):
                lib_list.append(os.path.join(libpath, libfile))

    return lib_list

def get_symbols(lib_fn):
    sym_list = []
    objdump = os.popen("objdump -T " + lib_fn)
    for line in objdump:
        if line.find(".text") < 0:
            continue
        sym_list.append(line.strip().split()[-1])

    return sym_list

@transaction.commit_on_success
def load_symbols(lib_fn):
    lib_name = os.path.basename(lib_fn)
    for symbol in get_symbols(lib_fn):
        sym_db = StaticSymbol(symbol=symbol, libraryname=lib_name)
        sym_db.save()

def main():
    for lib in get_library_list():
        sys.stdout.write("Loading symbols from " + lib + "...")
        sys.stdout.flush()
        load_symbols(lib)
        sys.stdout.write("\r")
        sys.stdout.write(" " * 79)
        sys.stdout.write("\r")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
