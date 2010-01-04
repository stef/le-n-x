# Create your views here.

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django import forms
import stem

class FetchForm(forms.Form):
    url = forms.CharField(required=True)

def handler(request):
    form = FetchForm(request.GET)
    if form.is_valid():
        url=form.cleaned_data['url']
        import urllib2
        text = urllib2.urlopen(url)
        cloud=stem.tagcloud(text,25)

        return HttpResponse('<link href="style.css" type="text/css" rel="stylesheet">\n%s' % (unicode(str(cloud),'utf8')))
    else:
        return render_to_response('fetch.html', { 'form': form, })
