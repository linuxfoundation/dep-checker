from django.db import models
from django.forms import ModelForm, forms
from django import forms
import os
import re

# Create your models here.

# setup some defaults/choices
rchoices = tuple(enumerate(range(0, 100)))
RECURSION_CHOICES = rchoices[1:]
DEFAULT_USER = os.environ['USER']
REL_CHOICES = (('Static','Static'), ('Dynamic','Dynamic'), ('Both', 'Both'))
RANK_CHOICES = (('Low','Low'), ('Normal','Normal'), ('Critical', 'Critical'))
STAT_CHOICES = (('', 'Unknown'), ('A', 'Approve'), ('D','Disapprove'))

def license_choices():
    # get the available licenses to populated the form drop-downs
    licenses = License.objects.all().order_by('longname')
    # need a tuple for the drop-down
    choices = []
    # no default
    choices.append(('',''))
    for lic in licenses:
        selector = lic.license
        if lic.version:
            selector += " " + lic.version
        choices.append((selector, selector))

    return choices

def library_choices():
    # get the available libraries to populated the form drop-downs
    libraries = Lib.objects.exclude(library__contains='(static)').values('library').distinct()
    # need a tuple for the drop-down
    choices = []
    # no default
    choices.append(('',''))
    for lib in libraries:
        selector = lib['library']
        choices.append((selector, selector))

    return choices

def file_choices():
    # get the available targets to populated the form drop-downs
    files = File.objects.filter(level = 1).values('file').distinct()
    # need a tuple for the drop-down
    choices = []
    # no default
    choices.append(('',''))
    for f in files:
        choices.append((f['file'], f['file']))

    return choices

class Test(models.Model):
    do_search = models.BooleanField('Identify dependencies for a specific target file in a target directory')
    disable_static = models.BooleanField('Disable checking for static dependencies')
    recursion = models.IntegerField('Recursion level for dependency checking analysis', 
                                    default = '1', choices = RECURSION_CHOICES)
    target = models.CharField('File/Path to run through the dependency check', max_length=200)
    target_dir = models.CharField('Target Directory', max_length=200, blank=True)
    test_date = models.DateTimeField('Test Date', auto_now=True)
    user = models.CharField('User Name (optional)', max_length=200, blank=True, default = DEFAULT_USER)
    project = models.CharField('Project Name (optional)', max_length=200, blank=True)
    comments = models.CharField('Comments (optional)', max_length=200, blank=True)
    def __unicode__(self):
        return self.target

class File(models.Model):
    test = models.ForeignKey(Test)
    file = models.CharField(max_length=200)
    license = models.CharField(max_length=200, blank=True)
    level = models.IntegerField()
    parent_id = models.IntegerField()
    def __unicode__(self):
        return self.file

class Lib(models.Model):
    test = models.ForeignKey(Test)
    file = models.ForeignKey(File)
    library = models.CharField(max_length=200)
    license = models.CharField(max_length=200, blank=True)
    level = models.IntegerField()
    parent_id = models.IntegerField()
    def __unicode__(self):
        return self.library

class License(models.Model):
    longname = models.CharField('License', max_length=200)
    license = models.CharField('License', max_length=200)
    version = models.CharField('Version', max_length=20, blank=True)
    def __unicode__(self):
        return self.license

class Aliases(models.Model):
    license = models.CharField('License', max_length=200)
    alias = models.CharField('Alias', max_length=20, unique=True)
    def __unicode__(self):
        return self.license

class LibLicense(models.Model):
    library = models.CharField('Library', max_length=200, unique=True)
    license = models.CharField('License', max_length=200)

class FileLicense(models.Model):
    file = models.CharField('Library', max_length=200, unique=True)
    license = models.CharField('License', max_length=200)

class Policy(models.Model):
    tlicense = models.CharField('Target License', max_length=200)
    dlicense = models.CharField('Dependency License', max_length=200)
    relationship = models.CharField('Relationship', max_length=20,
                                    default = 'Static', choices = REL_CHOICES)
    rank = models.CharField('Rank', max_length=20,
                            default = 'Low', choices = RANK_CHOICES)
    status = models.CharField('Status', max_length=1,
                            blank = True, choices = STAT_CHOICES)
    edit_date = models.DateTimeField('test date', auto_now=True)
    def __unicode__(self):
        return self.tlicense

class TestForm(ModelForm):   
    class Meta:
        model = Test

class FileForm(ModelForm):
    class Meta:
        model = File

class LibForm(ModelForm):
    class Meta:
        model = Lib

class LicenseForm(ModelForm):
    class Meta:
        model = License

class PolicyForm(ModelForm):
    class Meta:
        model = Policy

    tlicense = forms.ChoiceField()
    dlicense = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(PolicyForm, self).__init__(*args, **kwargs)
        self.fields['tlicense'].choices = license_choices()
        self.fields['dlicense'].choices = license_choices()

class LibLicenseForm(ModelForm):
    class Meta:
        model = LibLicense

    license = forms.ChoiceField()
    library = forms.ChoiceField()
 
    def __init__(self, *args, **kwargs):
        super(LibLicenseForm, self).__init__(*args, **kwargs)
        self.fields['license'].choices = license_choices()
        self.fields['library'].choices = library_choices()

class FileLicenseForm(ModelForm):
    class Meta:
        model = FileLicense

    license = forms.ChoiceField()
    file = forms.ChoiceField()
 
    def __init__(self, *args, **kwargs):
        super(FileLicenseForm, self).__init__(*args, **kwargs)
        self.fields['license'].choices = license_choices()
        self.fields['file'].choices = file_choices()

class AliasesForm(ModelForm):
    class Meta:
        model = Aliases

    license = forms.ChoiceField()
 
    def __init__(self, *args, **kwargs):
        super(AliasesForm, self).__init__(*args, **kwargs)
        self.fields['license'].choices = license_choices()

class StaticSymbol(models.Model):
    symbol = models.CharField('Symbol', max_length=200, db_index=True)
    libraryname = models.CharField('Library', max_length=80)
