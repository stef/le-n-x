# Create your views here.

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django import forms
import httplib, mimetypes, tidy

def post_multipart(host, selector, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTPConnection(host)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    #errcode, errmsg, headers = h.getreply()
    reply=h.getresponse()
    return reply.read()

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

class FetchForm(forms.Form):
    url = forms.CharField(required=True)
    xpath = forms.CharField(required=False)

def handler(request):
    form = FetchForm(request.GET)
    if form.is_valid():
        url=form.cleaned_data['url']
        xpath=form.cleaned_data['xpath']
        import urllib2
        text = urllib2.urlopen(url)

        from BeautifulSoup import BeautifulSoup
        if(xpath):
            soup = BeautifulSoup(text)
            text=soup.find(id=xpath)

        params = [("text", str(text)),
                  ("url_file", ""),
                  ("language", "English"),
                  ("topTags", "50"),
                  ("minFreq", "1"),
                  ("showFreq", "no"),
                  ("blacklist", "none"),
                  ("doStemming", "yes"),
                  (".cgifields", "showFreq"),
                  (".cgifields", "doStemming"),
                  (".cgifields", "fullscreen"),
                  ]
        files = [("uploaded_file", "", "") ]
        tagcrowd = post_multipart("www.tagcrowd.com","/", params, files)
        options = dict(output_xhtml=1, add_xml_decl=0, indent=0, tidy_mark=0, doctype="strict", wrap=0)
        tagcrowd=str(tidy.parseString(tagcrowd, **options))
        soup = BeautifulSoup(tagcrowd)
        cloud=soup.find(id="htmltagcloud")
        return HttpResponse('<link href="http://www.tagcrowd.com/style.css" type="text/css" rel="stylesheet">\n%s\nsource: <a href="%s">%s</a>\n<br />fragment id: %s\n<br />Original text follows:\n<br />%s' % (unicode(str(cloud),'utf8'), url, url, xpath, unicode(str(text),'utf8')))
    else:
        return render_to_response('fetch.html', { 'form': form, })
