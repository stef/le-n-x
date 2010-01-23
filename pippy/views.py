#!/usr/bin/env python
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

CSSHEADER='<head><link href="http://www.ctrlc.hu/~stef/pippi.css" media="screen" rel="stylesheet" title="" type="text/css"  /></head>'

class PippiForm(forms.Form):
    doc1 = forms.CharField(required=True)
    doc2 = forms.CharField(required=True)

class XpippiForm(forms.Form):
    doc = forms.CharField(required=True)

""" template to format a pippi (doc, match_pos, text) """
def htmlPippi(doc,matches,frag):
    return u'<span class="doc">in %s</span>: <span class="pos">%s</span><div class="txt">%s</div>' % (doc, matches, frag.decode('utf8'))

def diffFrag(frag1,frag2):
    match=True
    i=0
    while i<len(frag2):
        if frag1[i].lower()!=frag2[i].lower() and match:
            frag2[i]=u'<span class="diff">'+frag2[i]
            match=False
        elif frag1[i].lower()==frag2[i].lower() and not match:
            frag2[i-1]=frag2[i-1]+u'</span>'
            match=True
        elif i==len(frag2)-1 and not match:
            frag2[i-1]=frag2[i-1]+u'</span>'
        i=i+1
    return frag2

def htmlRefs(this,docs):
    refs=sorted(this.refs.items(),
                reverse=True,
                cmp=lambda x,y: cmp(len(x[0]), len(y[0])))
    res=[]
    for (stem,ref) in refs:
        if len(stem) < 5: break
        columns=(int(100)/(len(ref['refs'])+1))
        start=ref['matches'][0][0]
        length=ref['matches'][0][1]
        res.append(u'<table class="frag" width="100%"><tr>')
        res.append(u'<td style="width:%d%%;">' % columns)
        res.append(htmlPippi(this.id,
                    ref['matches'],
                    this.getFrag(start,length)))
        res.append(u'</td>')
        origfrag=this.tokens[start:start+length]
        for doc in ref['refs']:
            d=docs[doc]
            m=d.refs[stem]['matches']
            res.append(u'<td style="width:%d%%;">' % columns)
            frag=d.tokens[m[0][0]:m[0][0]+m[0][1]]
            frag=" ".join(diffFrag(origfrag,frag)).encode("utf8")
            res.append(htmlPippi(doc, m, frag))
            res.append(u'</td>')
        res.append(u'</tr></table><hr />')
    return '\n'.join(res).encode('utf8')

def htmlLongFrags(this):
    frags=this.longestFrags()
    res=[]
    for (k,docs) in frags:
        start=docs[0][1]
        length=docs[0][2]
        origfrag=this.docs[docs[0][0]].tokens[start:start+length]
        res.append(u'<table width="100%" class="frag"><tr>')
        for d in docs:
            res.append((u'<td style="width: %d%%;">' % (int(100)/len(docs))))
            frag=this.docs[d[0]].tokens[d[1]:d[1]+d[2]]
            frag=" ".join(diffFrag(origfrag,frag)).encode("utf8")
            res.append(htmlPippi(d[0],d[1:],frag))
            res.append(u'</td>')
        res.append(u'</tr></table><hr />')
    return '\n'.join(res).encode('utf8')

def pippi(request):
    form = PippiForm(request.GET)
    if form.is_valid():
        db=MatchDb()
        d1=Doc(form.cleaned_data['doc1'])
        d2=Doc(form.cleaned_data['doc2'])
        db.analyze(d1,d2)
        db.addDoc(d1)
        db.addDoc(d2)
        result=htmlLongFrags(db)

        return HttpResponse('%s\n%s' % (CSSHEADER,unicode(str(result),'utf8')))
    else:
        return render_to_response('pippi.html', { 'form': form, })

def xpippi(request):
    form = XpippiForm(request.GET)
    if form.is_valid():
        db=MatchDb()
        db.load()
        doc=form.cleaned_data['doc'].strip('\t\n')
        if doc in db.docs.keys():
            result=htmlRefs(db.docs[doc],db.docs)
        else:
            d=Doc(doc)
            if d:
                db.insert(d)
            result=htmlRefs(d,db.docs)
        return HttpResponse('%s\n%s' % (CSSHEADER,unicode(str(result),'utf8')))
    else:
        return render_to_response('xpippi.html', { 'form': form, })

