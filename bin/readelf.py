#!/usr/bin/python
# program to gather link dependencies of ELF files for compliance analysis
# Stew Benedict <stewb@linuxfoundation.org>
# Jeff Licquia <licquia@linuxfoundation.org>
# copyright 2010 Linux Foundation

import sys
import os
import re
import string
import sqlite3
import optparse
version = '0.0.7'

# Custom exceptions.

class NotELFError(StandardError):
    pass

# Globals.

usage_line = "usage: %prog [options] <file/dir tree to examine> [recursion depth]"

command_line_options = [
    optparse.make_option("-c", action="store_true", dest="do_csv", 
                         default=False, help="output in csv format"),
    optparse.make_option("-s", action="store", type="string", dest="target",
                         metavar="DIR", help="directory tree to search"),
    optparse.make_option("--no-static", action="store_false", dest="do_static",
                         default=True, help="don't look for static deps")
]

database_search_path = [ '/opt/linuxfoundation/share/dep-checker',
                         './staticdb', '../staticdb' ]
depth = 1
do_csv = False
do_static = True

def bad_depth():
    print "Recursion depth must be a positive number"
    sys.exit(1)

def dep_path(target, dep):
    # readelf gives us the lib, but not the path to check during recursion
    ldcall = "ldd " + target
    for lddata in os.popen(ldcall).readlines():
        if re.search("statically linked", lddata):
            return "NONE"

        elif re.search(dep, lddata):
            ldlist = string.split(lddata)
            if len(ldlist) > 2:
                # path is the 3rd field, usually...
                dpath = ldlist[2]
            else:
                dpath = ldlist[0]
            # but this may be a symlink
            dpath = os.path.realpath(dpath)
            break

    return dpath        

def find_static_library(func):
    "Given a symbol, return the most likely static library it's from."

    found_libs = []
    dbpath = None
    for dp in database_search_path:
        if os.path.exists(os.path.join(dp, "staticdb.sqlite")):
            dbpath = dp
            break

    if dbpath:
        staticdb = sqlite3.connect(os.path.join(dbpath, "staticdb.sqlite"))
        cursor = staticdb.cursor()
        cursor.execute("SELECT library FROM static WHERE symbol=?", (func,))
        results = cursor.fetchall()
        if len(results) == 1:
            found_libs.append(results[0][0])
        elif len(results) > 1:
            found_libs = [ x[0] for x in results ]

    return found_libs

def static_deps_check(target):
    "Look for statically linked dependencies."

    # State enumeration for debug parser.
    FIND_NEXT = 1
    FIND_NAME = 2

    # The algorithm here is pretty basic.  We grab a complete symbol list
    # and debug information.  Any symbols that aren't covered by debug
    # information are considered to be source from static libraries.

    # Read the functions from the symbol list.
    symlist = [ x.split() for x in os.popen("readelf -s " + target) ]
    symlist = [ x for x in symlist if len(x) == 8 ]
    sym_funcs = set([ x[7] for x in symlist if x[3] == "FUNC" ])

    # Read the functions from the debug information.
    debuginfo = os.popen("readelf -wi " + target)
    debug_funcs = set()
    debugstate = FIND_NEXT
    for line in debuginfo:
        if len(line) < 2:
            continue

        if debugstate == FIND_NAME:
            if line[1] == "<":
                debugstate = FIND_NEXT
            else:
                match = re.match(r'\s+<.+>\s+(.+?)\s+:\s+\(.+\):\s+(.+)$', line)
                if match:
                    (field, value) = match.group(1, 2)
                    if field == "DW_AT_name":
                        debug_funcs.add(value.strip())
                        debugstate = FIND_NEXT

        if debugstate == FIND_NEXT and line[1] == "<":
            match = re.search(r'\((.+)\)$', line)
            if match and match.group(1) == "DW_TAG_subprogram":
                found_name = None
                debugstate = FIND_NAME

    # Get the functions in the symbol list that have no debug info.
    staticsym_funcs = sym_funcs - debug_funcs

    # For each function, figure out where it came from.
    staticlib_list = []
    for func in staticsym_funcs:
        libs = find_static_library(func)
        for lib in libs:
            if lib not in staticlib_list:
                staticlib_list.append(lib)

    # Format and return the list.
    staticlib_list.sort()
    staticlib_results = [ x + " (static)" for x in staticlib_list ]
    return staticlib_results

def deps_check(target):
    deps = []
    # run the "file" command and see if it's ELF
    filetype = os.popen("file " + target).read()
    
    if re.search("ELF", filetype):
        if not re.search("statically linked", filetype):
            elfcall = "readelf -d " + target
            for elfdata in os.popen(elfcall).readlines():
                # lines we want all have "NEEDED"
                if re.search("NEEDED", elfdata):
                    # library is the 5th field
                    dep = string.split(elfdata)[4]
                    dep = dep.strip("[]")
                    deps.append(dep)

        if do_static:
            deps.extend(static_deps_check(target))

    else:
        raise NotELFError, "not an ELF file"

    return deps

# non-recursive case
def print_deps(target, deps):
    csvstring = ''
    spacer = ''

    if len(deps) < 1:
        return

    if do_csv:
        csvstring += str(1) + "," + target
        for dep in deps:
            csvstring += "," + dep
        print csvstring

    else:
        print spacer + "[" + str(1) + "]" + target + ":"
        spacer += "  "
        for dep in deps:
            print spacer + dep

def print_dep(dep, indent):
    spacer = 2 * indent * " "
    if not do_csv:
        print spacer + dep

def print_path_dep(parent, soname, dep, indent):
    csvstring = ''
    spacer = (indent - 1) * "  "
    token = "[" + str(indent) + "]"
    if not do_csv:
        print spacer + token + parent + ":"
    else:
        csvstring += str(indent) + "," + parent + ","
        # indent = level, treat level 1 slightly differently
        if indent != 1 and soname:
            csvstring += soname + ","
        csvstring += dep
        print csvstring

def dep_loop(parent, soname, dep, level):
    if level > depth:
        return

    if level == 1:
        print_path_dep(parent, soname, dep, level)
        print_dep(dep, level)
    else:
        print_path_dep(parent, soname, dep, level)
        print_dep(dep, level)

    target = dep_path(parent, dep)
    childdeps = deps_check(target)

    if len(childdeps) > 0:
        for childdep in childdeps:
            dep_loop(target, dep, childdep, level + 1)
        
def main():
    opt_parser = optparse.OptionParser(usage=usage_line, 
                                       version="%prog version " + version,
                                       option_list=command_line_options)
    (options, args) = opt_parser.parse_args()

    if len(args) == 0 or len(args) > 2:
        opt_parser.error("improper number of non-option arguments")

    # prog_ndx_start is the offset in argv for the file/dir and recursion
    prog_ndx_start = 1
    found = 0
    parent = ""
    global do_csv, depth, do_static

    do_static = options.do_static

    do_csv = options.do_csv
    if options.target:
        do_search = True
        target = options.target
        target_file = args[0]
        if not os.path.isdir(target):
            print target + " does not appear to be a directory..."
    	    sys.exit(1)
    else:
        do_search = False
        target = args[0]
        if not(os.path.isdir(target) or os.path.isfile(target)):
            print target + " does not appear to be a directory or file..."
    	    sys.exit(1)

    # sanity check on recursion level
    if len(args) == 1:
        depth = 1
        
    else:
        try:
            recursion_arg = args[1]
            depth = int(recursion_arg)
        except:
            bad_depth()

        if depth < 1:
            bad_depth()

    if os.path.isdir(target):
        # walk the directory tree and find ELF files to process
        for path, dirs, files in os.walk(target):
            for filename in files:
                if (do_search and (filename == target_file)) or not(do_search):
                    candidate = os.path.join(path, filename)
                    if os.path.isfile(candidate):
                        try:
                            deps = deps_check(candidate)
                        except NotELFError:
                            deps = []    
                        
                        if len(deps) > 0:
                            if depth == 1:
                                print_deps(candidate, deps)
                            # do recursion if called for
                            else:
                                for dep in deps:
                                    dep_loop(candidate, None, dep, 1)
                    if do_search and (filename == target_file):
                        found = 1                   
                        break

        if do_search and not found:
            print target_file + " was not found in " + target + " ..."
            sys.exit(1)

    else:
	    # single file, just check it and exit
        # top level deps
        parent = target

        try:
            deps = deps_check(target)
        except NotELFError:
            print "not an ELF file..."
            sys.exit(1)

        if depth == 1:
            print_deps(target, deps)

        # do recursion if called for       
        else:
            for dep in deps:
                dep_loop(parent, None, dep, 1)
        
        sys.exit(0)

if __name__=='__main__':
    main()

