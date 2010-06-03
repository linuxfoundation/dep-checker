# Create your views here.
from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from compliance.linkage.models import Test, File, Lib, TestForm, FileForm, LibForm
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
# so we can run readelf.py
import os
import re
import urllib
import itertools

# each of these views has a corresponding html page in ../templates/linkage

# main page
def index(request):
    return render_to_response('linkage/index.html')

# test run detail page
def detail(request, test_id):
    t, masterlist = render_detail(test_id)
    return render_to_response('linkage/detail.html', {'test': t, 'master': masterlist })
  
# results list page - this is also a form, for test deletions
def results(request):
    if request.method == 'POST': # If the form has been submitted...
        testlist = request.POST.get('testlist', '')
        if testlist != '':
            tests = testlist.split(",")

            for test in tests:
                if test != '':
                    q = Test.objects.filter(id = test)
                    q.delete()
                    q = File.objects.filter(test = test)
                    q.delete()
                    q = Lib.objects.filter(test = test)
                    q.delete()

    latest_test_list = Test.objects.all().order_by('-test_date')
    return render_to_response('linkage/results.html', {'latest_test_list': latest_test_list})

# process test form
def test(request):
    if request.method == 'POST': # If the form has been submitted...
        testform = TestForm(request.POST) # A form bound to the POST data
        if testform.is_valid(): # All validation rules pass
            # use -c to get csv output from the command line tool
            cli_command = "/opt/linuxfoundation/bin/readelf.py -c "
            target = testform.cleaned_data['target']
            do_search = testform.cleaned_data['do_search']
            if do_search:
                target_dir = testform.cleaned_data['target_dir']
                cli_command += "-s " + target_dir
            cli_command += " " + target
            recursion = testform.cleaned_data['recursion']
            cli_command += " " + str(recursion)
            # form doesn't have the id, but we can get the db model and then get it
            testdata = testform.save(commit=False)       
            testdata.save()
            testid = testdata.id

            # FIXME - for debugging
            print cli_command, testid

            # capture the output and push to the database
            lastdepth = 1
            lastfile = ''            
            for dbdata in os.popen(cli_command).readlines():
                # check for no result
                if not re.search("(no deps|does not|files in that|was not found)", dbdata):
                    dbdata = dbdata.rstrip("\r\n")
                    #print dbdata
                    # format for level 1 is depth, parent, dep
                    # format for level 1 + N is depth, child path, child, dep, dep...
                    deps = dbdata.split(",")

                    # write the file record
                    depth = int(deps[0])
                    testfile = deps[1]
                    # FIXME - dummy license data for testing
                    flicense = "BSD" + str(testid)
                    # the top level file may show multiple times, only get the first one
                    if depth == 1 and testfile != lastfile:
                        filedata = File(test_id = testid, file = testfile, level = depth, license = flicense, parent_id = 0)
                        filedata.save()
                        fileid = filedata.id
                        lastfile = testfile
                        parentid = fileid
                        filedata.parent_id = parentid
                        filedata.save()
                    elif depth != 1:
                        # FIXME - right now we're not really doing anything with theses
                        filedata = File(test_id = testid, file = testfile, level = depth, license = flicense, parent_id = 0)
                        filedata.save()
                        fileid = filedata.id
                        # the 'child' files get the parent's id
                        filedata.parent_id = parentid
                        filedata.save()
                   
                    # now the lib records
                    offset = 2
                    # child records have the lib path and the parent dep
                    if depth > 1:
                        offset = 3
                    # FIXME - filler for testing
                    llicense = "Artistic" + str(testid)
                    for lib in deps[offset:len(deps)]:
                        # we link file_id to parent_id of the file for recursion
                        libdata = Lib(test_id = testid, file_id = parentid, library = lib, license = llicense, level = depth, parent_id = 0)
                        libdata.save()
                        libid = libdata.id
                        
                        # the 'child' libs get the parent's id
                        if depth == 1:
                            parentlibid = libid
                        libdata.parent_id = parentlibid
                        libdata.save()
                        
                else:
                    # FIXME - do feedback in the gui here...
                    print "bad result..."   
            
            # FIXME - show status, goto results, handle error condition             
            # and show the results
            t, masterlist = render_detail(testid)
            return render_to_response('linkage/detail.html', {'test': t, 'master': masterlist })
            
    else:
        testform = TestForm() # An unbound form

    return render_to_response('linkage/test.html', {
        'testform': testform
    })

# Just an "about" page
def about(request):
    return render_to_response('linkage/about.html')

# utility functions

# pre-render the table data for the detail page
def render_detail(test_id):
    t = get_object_or_404(Test, pk=test_id)
    # all we want is the level 1 files
    fileset = t.file_set.filter(level = 1)
    libset = t.lib_set.all()

    # the table renders too slow walking through the one-to-many of
    # files -> libs, prefill a list with file, license, libs, lib_license 
    # and indent the recursion level here, template just blobs out the table

    flist = []
    llist = []
    for file in fileset:
        flist.append(file.file)
        llist.append(file.license)

    lastid = ''
    masterlist = []
    liblist = ''
    # this gets incremented before the first record is complete
    counter = -1
    spacer = "&nbsp;&nbsp;"

    for lib in libset:
        fileid = lib.file_id
        # no indent for level 1
        level = lib.level - 1
        # we don't use this at the moment
        parent = lib.parent_id
        if fileid != lastid:
            if liblist != '':
                masterlist.append({'file': flist[counter], 'license': llist[counter], 'libs': liblist, 'licenses': liclist})
            liblist = lib.library
            liclist = lib.license
            counter += 1
        else:
            liblist += '<BR>' + spacer * level + lib.library
            liclist += '<BR>' + lib.license
        lastid = fileid

    # add the last record
    masterlist.append({'file': flist[counter], 'license': llist[counter], 'libs': liblist, 'licenses': liclist})

    return t, masterlist

