from django.db import models
from django.forms import ModelForm, forms
import os

# Create your models here.

# setup some defaults/choices
rchoices = tuple(enumerate(range(0, 100)))
RECURSION_CHOICES = rchoices[1:]
DEFAULT_USER = os.environ['USER']

class Test(models.Model):
    do_search = models.BooleanField('Search for target file in target directory')
    recursion = models.IntegerField('Recursion level for analysis', 
                                    default = '1', choices = RECURSION_CHOICES)
    target = models.CharField('File/Path to test', max_length=200)
    target_dir = models.CharField('Target Directory', max_length=200, blank=True)
    test_date = models.DateTimeField('test date', auto_now=True)
    user = models.CharField(max_length=200, blank=True, default = DEFAULT_USER)
    project = models.CharField(max_length=200, blank=True)
    comments = models.CharField(max_length=200, blank=True)
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

class Dep(models.Model):
    file = models.ForeignKey(File)
    lib = models.ForeignKey(Lib)
    #def __unicode__(self):
    #    return self.lib

class TestForm(ModelForm):   
    class Meta:
        model = Test

class FileForm(ModelForm):
    class Meta:
        model = File

class LibForm(ModelForm):
    class meta:
        model = Lib


