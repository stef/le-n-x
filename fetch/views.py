#    This file is part of le-n-x.

#    utterson is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    utterson is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with utterson.  If not, see <http://www.gnu.org/licenses/>.

# (C) 2009-2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

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
