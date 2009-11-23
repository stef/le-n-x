# Create your views here.

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django import forms

class FetchForm(forms.Form):
    url = forms.CharField(required=True)
    xpath = forms.CharField(required=False)

def handler(request):
    form = FetchForm(request.GET)
    if form.is_valid():
        url=form.cleaned_data['url']
        xpath=form.cleaned_data['xpath']
        #return HttpResponse("%s<br>%s" % (url,xpath))
        #return HttpResponseRedirect('/thanks/')
        import urllib2
        from urllib import urlencode 
        from BeautifulSoup import BeautifulSoup
        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page)
        text=soup.find(id=xpath)

        params = urlencode({"text": text,
                            "uploaded_file": "",
                            "url_file": "",
                            "language": "English",
                            "topTags": 50,
                            "minFreq": 1,
                            "showFreq": "no",
                            "blacklist": "none",
                            "doStemming": "yes",
                            ".cgifields": "showFreq",
                            ".cgifields": "doStemming",
                            ".cgifields": "fullscreen",
                            })
        tagcrowd = urllib2.urlopen("http://www.tagcrowd.com/", params)
        return HttpResponse("%s" % tagcrowd)
        soup = BeautifulSoup(tagcrowd)
        text=soup.find(id="htmltagcloud")
        return HttpResponse("%s" % text.encode('utf8'))
    else:
        return render_to_response('fetch.html', { 'form': form, })
