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
        cloud=stem.tagcloud(text)

        return HttpResponse('<link href="style.css" type="text/css" rel="stylesheet">\n%s<br />\nsource: <a href="%s">%s</a>' % (unicode(str(cloud),'utf8'), url, url))
    else:
        return render_to_response('fetch.html', { 'form': form, })
