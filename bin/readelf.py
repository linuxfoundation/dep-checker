#!/usr/bin/python
# program to gather link dependencies of ELF files for compliance analysis
# Stew Benedict <stewb@linux-foundation.org>
# Jeff Licquia <licquia@linuxfoundation.org>
# copyright 2010 Linux Foundation

import sys
import os
import re
import string
import sqlite3
import optparse
version = '0.0.6'

# Custom exceptions.

class NotELFError(StandardError):
    pass

# Globals.

usage_line = "usage: %prog [options] <file/dir tree to examine> [recursion depth]"

command_line_options = [
    optparse.make_option("-c", action="store_true", dest="do_csv", 
                         default=False, help="output in csv format"),
    optparse.make_option("-s", action="store", type="string", dest="target",
                         metavar="DIR", help="directory tree to search")
]

database_search_path = [ '/opt/linuxfoundation/share/dep-checker',
                         './staticdb' ]
depth = 1
do_csv = False

def bad_depth():
    print "Recursion depth must be a positive number"
    sys.exit(1)

def dep_path(target, dep):
    #print target, dep
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

    found_lib = None
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
            found_lib = results[0][0] + " (static)"
        elif len(results) > 1:
            found_libs = [ x[0] for x in results ]
            found_lib = ",".join(found_libs) + " (static)"

    return found_lib

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
        lib = find_static_library(func)
        if lib and lib not in staticlib_list:
            staticlib_list.append(lib)

    # Return the list.
    staticlib_list.sort()
    return staticlib_list

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
                    dep = dep.replace("[","")
                    dep = dep.replace("]","")
                    deps.append(dep)

        deps.extend(static_deps_check(target))

    else:
        raise NotELFError, "not an ELF file"

    return deps

def deps_print(title, parent, target, level, deps):
    csvstring = ''
    spacer = ''
    nospace = ''

    if level > 0:
        nospace += spacer

    for space in range(0, level):
        spacer += "  "

    if len(deps) < 1:
        # FIXME - this blows up the recursion, just drop it?
        #deps.append("NONE")
        # at ld-linux - just suppress the output
        return

    if do_csv:
        if depth == 1:
            csvstring += str(level + 1) + "," + target
        else:
            csvstring += str(level + 1) + "," + target + "," + title
        if level > 0 or depth < 2:
            for dep in deps:
                csvstring += "," + dep
        print csvstring

    else:
        if level == 1:
            print spacer + title
        print spacer + "[" + str(level + 1) + "]" + target + ":"
        spacer += "  "
        if level > 0 or depth < 2:
            for dep in deps:
                print spacer + dep

def print_parent(parent, dep):
    if not do_csv:
        print '[1]' + parent + ":"
    else:
        print '1,' + parent + "," + dep

def dep_loop(parent, deps):    
    for dep in deps:
        print_parent(parent, dep)

        if dep != "STATIC":
         
            childparent = parent            
            target = dep_path(childparent,dep)

            for level in range(1, depth):
                childdeps = deps_check(target)
                deps_print(dep, childparent, target, level, childdeps)
                if len(childdeps) > 0:
                    childparent = target            
                    target = dep_path(childparent,childdeps[0])                
                else:
                    # must be at the bottom of the chain, stop
                    break
        
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
    global do_csv, depth

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
                                deps_print(parent, parent, candidate, 0, deps)
                            # do recursion if called for
                            else:
                                dep_loop(candidate, deps)
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

        # FIXME: for now, if no deps were found, assume the file
        # is statically linked.  Should rework the recursion so
        # we don't need this.
        if not deps:
            deps.append("STATIC")

        if depth == 1:
            deps_print(parent, parent, target, 0, deps)

        # do recursion if called for       
        else:
            dep_loop(parent, deps)
         
        sys.exit(0)

if __name__=='__main__':
    main()

