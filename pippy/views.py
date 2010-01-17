#    This file is part of le(n)x.

#    le(n)x is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    le(n)x is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with le(n)x.  If not, see <http://www.gnu.org/licenses/>.

# (C) 2009-2010 by Stefan Marsiske, <stefan.marsiske@gmail.com>

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django import forms
from brain.document import MatchDb, Doc

class PippiForm(forms.Form):
    doc1 = forms.CharField(required=True)
    doc2 = forms.CharField(required=True)

class XpippiForm(forms.Form):
    doc = forms.CharField(required=True)

def pippi(request):
    form = PippiForm(request.GET)
    if form.is_valid():
        db=MatchDb()
        d1=Doc(form.cleaned_data['doc1'])
        d2=Doc(form.cleaned_data['doc2'])
        db.analyze(d1,d2)
        db.addDoc(d1)
        db.addDoc(d2)
        result=db.htmlLongFrags()

        return HttpResponse('%s' % (unicode(str(result),'utf8')))
    else:
        return render_to_response('pippi.html', { 'form': form, })

def xpippi(request):
    form = XpippiForm(request.GET)
    if form.is_valid():
        db=MatchDb()
        db.load()
        doc=form.cleaned_data['doc'].strip('\t\n')
        if doc in db.docs.keys():
            result=db.docs[doc].htmlRefs(db.docs)
        else:
            d=Doc(doc)
            if d:
                db.insert(d)
            result=d.htmlRefs(db.docs)
        return HttpResponse('%s' % (unicode(str(result),'utf8')))
    return render_to_response('xpippi.html', { 'form': form, })

