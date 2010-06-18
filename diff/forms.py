from django import forms
from datetime import datetime
from django.conf import settings

class diffForm(forms.Form):
    doc1 = forms.FileField(required=True)
    doc2 = forms.FileField(required=True)
