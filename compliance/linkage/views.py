# Create your views here.
from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from compliance.linkage.models import Test, File, Lib, License, LibLicense, FileLicense, Policy, TestForm, LicenseForm, PolicyForm, LibLicenseForm, FileLicenseForm
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from django.conf import settings
from django.db.models import Q

import os
import re
import urllib

# used for binding and policy
is_static = '(static)'

### each of these views has a corresponding html page in ../templates/linkage

# main page
def index(request):
    from site_settings import gui_name, gui_version
    return render_to_response('linkage/index.html', {'name': gui_name, 'version': gui_version})

# test run detail page
def detail(request, test_id):
    t, masterlist = render_detail(test_id)
    return render_to_response('linkage/detail.html', {'test': t, 'master': masterlist, 'tab_results': True})
  
# results list page - this is also a form, for test deletions
def results(request):
    if request.method == 'POST': # If the form has been submitted...
        testlist = request.POST.get('testlist', '')
        if testlist != '':
            tests = testlist.split(",")

            # delete all the selected tests from the database
            for test in tests:
                if test != '':
                    q = Test.objects.filter(id = test)
                    q.delete()
                    q = File.objects.filter(test = test)
                    q.delete()
                    q = Lib.objects.filter(test = test)
                    q.delete()

    latest_test_list = Test.objects.all().order_by('-test_date')
    return render_to_response('linkage/results.html', {'latest_test_list': latest_test_list, 'tab_results': True})

# licenses entry/maintenance page
def licenses(request):
    if request.method == 'POST': # If the form has been submitted...
        mode = urllib.unquote(request.POST.get('submit'))

        if re.search("^Add", mode):   
            licenseform = LicenseForm(request.POST) # A form bound to the POST data
            # request to add data
            if licenseform.is_valid(): # All validation rules pass
                licenseform.save()

        else:
            # delete request
            licenselist = request.POST.get('licenselist', '')
            if licenselist != '':
                delete_records(License, licenselist)

    licenseform = LicenseForm() # An unbound form

    latest_license_list = License.objects.all().order_by('license')
    return render_to_response('linkage/licenses.html', {
                              'latest_license_list': latest_license_list, 
                              'licenseform': licenseform,
                              'tab_licenses': True })

# policy list page - this is also a form, for policy deletions/updates
def policy(request):
    from site_settings import show_rank

    if request.method == 'POST': # If the form has been submitted...
        mode = urllib.unquote(request.POST.get('submit'))

        if re.search("^Add", mode):
            policyform = PolicyForm(request.POST) # A form bound to the POST data
            # request to add data
            if policyform.is_valid(): # All validation rules pass
                policyform.save()
       
        else:
            # delete request       
            policylist = request.POST.get('policylist', '')
            if policylist != '':
                delete_records(Policy, policylist)

    policyform = PolicyForm() # An unbound form

    latest_policy_list = Policy.objects.all().order_by('-edit_date')

    return render_to_response('linkage/policy.html', {
                              'show_rank': show_rank,
                              'latest_policy_list': latest_policy_list, 
                              'policyform': policyform, 
                              'tab_policy': True })

# library/license binding page
def liblicense(request):

    if request.method == 'POST': # If the form has been submitted...
        mode = urllib.unquote(request.POST.get('submit'))

        if re.search("^Add", mode):
            liblicenseform = LibLicenseForm(request.POST) # A form bound to the POST data
            # request to add data
            if liblicenseform.is_valid(): # All validation rules pass
                liblicenseform.save()
       
        elif re.search("^Update", mode):
            update_lib_bindings()

        else:
            # delete request       
            liblicenselist = request.POST.get('liblicenselist', '')
            if liblicenselist != '':
                delete_records(LibLicense, liblicenselist)

    liblicenseform = LibLicenseForm() # An unbound form

    latest_liblicense_list = LibLicense.objects.all().order_by('library')

    return render_to_response('linkage/liblicense.html', {
                              'latest_liblicense_list': latest_liblicense_list, 
                              'liblicenseform': liblicenseform, 
                              'tab_liblicense': True })

# target/license binding page
def targetlicense(request):

    if request.method == 'POST': # If the form has been submitted...
        mode = urllib.unquote(request.POST.get('submit'))

        if re.search("^Add", mode):
            targetlicenseform = FileLicenseForm(request.POST) # A form bound to the POST data
            # request to add data
            if targetlicenseform.is_valid(): # All validation rules pass
                targetlicenseform.save()
       
        elif re.search("^Update", mode):
            update_file_bindings()

        else:
            # delete request       
            targetlicenselist = request.POST.get('targetlicenselist', '')
            if targetlicenselist != '':
                delete_records(FileLicense, targetlicenselist)

    targetlicenseform = FileLicenseForm() # An unbound form

    latest_targetlicense_list = FileLicense.objects.all().order_by('file')

    return render_to_response('linkage/targetlicense.html', {
                              'latest_targetlicense_list': latest_targetlicense_list, 
                              'targetlicenseform': targetlicenseform, 
                              'tab_targetlicense': True })

# process test form - this is where the real work happens
def test(request):
    cli_command = settings.CLI_COMMAND + " -c"
    if request.method == 'POST': # If the form has been submitted...
        testform = TestForm(request.POST) # A form bound to the POST data
        if testform.is_valid(): # All validation rules pass
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

            # capture the output and push to the database
            lastdepth = 1
            lastfile = ''
            errmsg = ''
            dbdata = ''           
            for dbdata in os.popen(cli_command).readlines():
                # check for no result - these are known exit messages from the cli
                if not re.search("(does not|was not found|not an ELF)", dbdata):
                    dbdata = dbdata.rstrip("\r\n")
                    # format for level 1 is: depth, parent, dep
                    # format for level 1 + N is: depth, child path, child, dep, dep...
                    deps = dbdata.split(",")

                    # write the file record
                    depth = int(deps[0])
                    testfile = deps[1]
                    # the top level file may show multiple times, only get the first one
                    if depth == 1 and testfile != lastfile:
                        filedata = File(test_id = testid, file = testfile, level = depth, parent_id = 0)
                        filedata.save()
                        fileid = filedata.id
                        lastfile = testfile
                        parentid = fileid
                        filedata.parent_id = parentid
                        filedata.save()
                    elif depth != 1:
                        # FIXME - right now we're not really doing anything with these
                        filedata = File(test_id = testid, file = testfile, level = depth, parent_id = 0)
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
                    for lib in deps[offset:len(deps)]:
                        # we link file_id to parent_id of the file for recursion
                        libdata = Lib(test_id = testid, file_id = parentid, library = lib, level = depth, parent_id = 0)
                        libdata.save()
                        libid = libdata.id
                        
                        # the 'child' libs get the parent's id
                        if depth == 1:
                            parentlibid = libid
                        libdata.parent_id = parentlibid
                        libdata.save()
                        
                else:
                    # do feedback in the gui from here
                    errmsg += dbdata

            # cli didn't return anything
            if not dbdata:
                errmsg = "no result..."

            # if we got an error, delete the test entry
            if errmsg:
                    q = Test.objects.filter(id = testid)
                    q.delete()
                    t = []
                    masterlist = []

            else:
                # update the license bindings
                update_file_bindings()
                update_lib_bindings()
             
                # render the results
                t, masterlist = render_detail(testid)

            return render_to_response('linkage/detail.html', 
                {'test': t, 'master': masterlist, 'error_message': errmsg })
            
    else:
        testform = TestForm() # An unbound form

    return render_to_response('linkage/test.html', {
        'testform': testform,
        'tab_test': True,
    })

### these are all basically documentation support

# doc page
def documentation(request):
    from site_settings import gui_name, gui_version

    # Read the standalone docs, and reformat for the gui
    try:
        f = open(settings.STATIC_DOC_ROOT + "/docs/index.html", 'r')
        doc_index = []
        for line in f:
            #replace the div styles for embedded use
            line = line.replace('<div id="lside">', '<div id="lside_e">')
            line = line.replace('<div id="main">', '<div id="main_e">')
            doc_index.append(line)
        f.close()
    
        # drop the first 11 lines
        docs = ''.join(doc_index[11:])

    except:
        docs = "<b>Error, no index.html in compliance/media/docs.</b><br>"
        docs += "If working with a git checkout or tarball, please type 'make' in the top level directory."

    return render_to_response('linkage/documentation.html', 
                              {'name': gui_name, 
                               'version': gui_version, 
                               'gui_docs': docs })

# this does not have a corresponding dirlist.html
# this is dynamic filetree content fed to jqueryFileTree for the test.html file/dir selection
# script for jqueryFileTree points to /linkage/dirlist/
def dirlist(request):
    # filter out some directories that aren't useful from "/"
    not_wanted = [ '/proc', '/dev', '/sys', '/initrd' ]
    r=['<ul class="jqueryFileTree" style="display: none;">']
    try:
        d=urllib.unquote(request.POST.get('dir'))
        content = os.listdir(d)
        # slows things a little, but looks more like 'ls'
        for f in sorted(content, key=unicode.lower):
            ff=os.path.join(d,f)
            if ff not in not_wanted and f != 'lost+found':
                if os.path.isdir(ff): 
                    r.append('<li class="directory collapsed"><a href="#" rel="%s/">%s</a></li>' % (ff,f))
                else:
                    e=os.path.splitext(f)[1][1:] # get .ext and remove dot
                    r.append('<li class="file ext_%s"><a href="#" rel="%s">%s</a></li>' % (e,ff,f))
        r.append('</ul>')
    except Exception,e:
        r.append('Could not load directory: %s' % str(e))
    r.append('</ul>')
    return HttpResponse(''.join(r))

### utility functions

# delete table records requested by id from one of the input forms
def delete_records(table, rlist):
            
    records = rlist.split(",")

    for record in records:
        if record != '':
            q = table.objects.filter(id = record)
            q.delete()

# update Lib records for license bindings
def update_lib_bindings():
    llist = LibLicense.objects.all().order_by('library')
    # bind both the dynamic and static version
    for ll in llist:
        Lib.objects.filter(Q(library = ll.library) | Q(library = ll.library + is_static)).update(license = ll.license)

# update File records for license bindings
def update_file_bindings():
    flist = FileLicense.objects.all().order_by('file')
    for fl in flist:
        File.objects.filter(file = fl.file).update(license = fl.license)

# check a target/library pair for policy violations
def check_policy(flicense, llicense, library, issue):
    ltype = 'Dynamic'
    if re.search(is_static, library):
        ltype = 'Static'
    policyset = Policy.objects.filter(tlicense = flicense, dlicense = llicense)
    policyset = policyset.filter(Q(relationship = ltype) | Q(relationship = 'Both'))
    if policyset:
        issue = issue or True
        llicense = flag_policy_issue(llicense)

    return issue, llicense
        
# flag a policy issue for the test results rendering
def flag_policy_issue(value):
    # to highlight the issues
    tag_red = '<font color="red">'
    tag_end = '</font><img src="/site_media/images/red_flag.png">'
    value = tag_red + value + tag_end
    return value

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
        if file.license:
            llist.append(file.license)
        else:
            llist.append("TBD")

    lastid = ''
    masterlist = []
    liblist = ''
    # this gets incremented before the first record is complete
    counter = -1
    spacer = "&nbsp;&nbsp;"
    
    policy_issue = False
    for lib in libset:
        fileid = lib.file_id
        # no indent for level 1
        level = lib.level - 1
        # we don't use this at the moment
        parent = lib.parent_id
        if lib.license:
            policy_issue, llicense = check_policy(llist[counter], lib.license, lib.library, policy_issue)
        else:
            llicense = 'TBD'
        if fileid != lastid:
            if liblist != '':
                if policy_issue:
                    llist[counter] = flag_policy_issue(llist[counter]) 
                masterlist.append({'file': flist[counter], 'license': llist[counter], 'libs': liblist, 'licenses': liclist})
            liblist = lib.library
            counter += 1
            # reset and check against the new binary, if we have a license
            policy_issue = False
            if lib.license:
                policy_issue, llicense = check_policy(llist[counter], lib.license, lib.library, policy_issue)
            liclist = llicense
        else:
            liblist += '<BR>' + spacer * level + lib.library
            liclist += '<BR>' + llicense
        lastid = fileid

    # add the last record
    if policy_issue:
        llist[counter] = flag_policy_issue(llist[counter]) 
    masterlist.append({'file': flist[counter], 'license': llist[counter], 'libs': liblist, 'licenses': liclist})
    
    return t, masterlist

