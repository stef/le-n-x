from django import forms
from models import Posts, Comments, Tags
from datetime import datetime
from django.conf import settings

class XpippiForm(forms.Form):
    doc = forms.CharField(required=True)

class PippiForm(forms.Form):
    doc1 = forms.CharField(required=True)
    doc2 = forms.CharField(required=True)

class viewForm(forms.Form):
    doc = forms.CharField(required=True)
