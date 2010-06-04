#!/usr/bin/python
# program to gather link dependencies of ELF files for compliance analysis
# Stew Benedict <stewb@linux-foundation.org>
# copyright 2010 Linux Foundation

import sys
import os
import re
import string
version = '0.0.5'

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
    
def deps_check(target):
    deps = []
    # run the "file" command and see if it's ELF
    filetype = os.popen("file " + target).read()
    
    if re.search("ELF", filetype):
        if re.search("statically linked", filetype):
            # FIXME - eventually do something interesting here - in the GUI?
            deps.append("STATIC")
        else:
            elfcall = "readelf -d " + target
            for elfdata in os.popen(elfcall).readlines():
                # lines we want all have "NEEDED"
                if re.search("NEEDED", elfdata):
                    # library is the 5th field
                    dep = string.split(elfdata)[4]
                    dep = dep.replace("[","")
                    dep = dep.replace("]","")
                    deps.append(dep)

    return deps

def deps_print(title, parent, target, level, deps, do_csv, depth):
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

def print_parent(parent, dep, do_csv, depth):
    if not do_csv:
        print '[1]' + parent + ":"
    else:
        print '1,' + parent + "," + dep

def dep_loop(depth, parent, deps, do_csv):    
    for dep in deps:
        print_parent(parent, dep, do_csv, depth)

        if dep != "STATIC":
         
            childparent = parent            
            target = dep_path(childparent,dep)

            for level in range(1, depth):
                childdeps = deps_check(target)
                deps_print(dep, childparent, target, level, childdeps, do_csv, depth)
                if len(childdeps) > 0:
                    childparent = target            
                    target = dep_path(childparent,childdeps[0])                
                else:
                    # must be at the bottom of the chain, stop
                    break
        
def show_usage(argv):
    print argv[0] + ' version ' + version 
    print 'Usage: ' + argv[0]
    print '       -c output in csv format'
    print '       -s <directory tree to search>'
    print '       <directory tree or file to examine> [recursion depth]'
    print '       Specifying a directory without -s will report all ELF'
    print '       files in that directory tree'
    sys.exit(1)

def main(argv):
    if len(argv) < 2 or '-?' in argv or '-h' in argv:
        show_usage(argv)

    # prog_ndx_start is the offset in argv for the file/dir and recursion
    prog_ndx_start = 1
    do_search = 0
    do_csv = 0
    found = 0
    parent = ""

    if '-c' in argv:
        sloc = string.index(argv, "-c")
        if prog_ndx_start <= sloc:
            prog_ndx_start = sloc + 1;
        do_csv = 1

    if '-s' in argv:
        sloc = string.index(argv, "-s")
        target = argv[sloc + 1]
        if prog_ndx_start <= sloc:
            prog_ndx_start = sloc + 2;
        do_search = 1
        
    # sanity check on file/directory name
    if not(do_search):
        target = argv[prog_ndx_start]
        if not(os.path.isdir(target) or os.path.isfile(target)):
            print target + " does not appear to be a directory or file..."
    	    sys.exit(1)
    else:
        if len(argv) < 4:
            show_usage(argv)
        target_file = argv[prog_ndx_start]
        if not os.path.isdir(target):
            print target + " does not appear to be a directory..."
    	    sys.exit(1)

    # sanity check on recursion level
    if len(argv) == prog_ndx_start + 1:
        depth = 1
        
    else:
        try:
            recursion_arg = argv[prog_ndx_start + 1]
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
                        deps = deps_check(candidate)
                        if len(deps) > 0:
                            if depth == 1:
                                deps_print(parent, parent, candidate, 0, deps, do_csv, depth)
                            # do recursion if called for
                            else:
                                dep_loop(depth, candidate, deps, do_csv)
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
        deps = deps_check(target)
        if not deps:
            print "not an ELF file..."
            sys.exit(1)

        if depth == 1:
            deps_print(parent, parent, target, 0, deps, do_csv, depth)

        # do recursion if called for       
        else:
            dep_loop(depth, parent, deps, do_csv)
         
        sys.exit(0)

if __name__=='__main__':
    main(sys.argv)

