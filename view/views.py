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

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings
from BeautifulSoup import BeautifulSoup, Tag
import re
from lenx.brain import stopwords, tagcloud
from lenx.view.models import Doc, Pippi, Docs, Pippies
from lenx.view.forms import XpippiForm, viewForm
from operator import itemgetter

""" template to format a pippi (doc, match_pos, text) """
def htmlPippi(doc,matches,frag):
    return u'<span class="doc">in %s</span>: <span class="pos">%s</span><div class="txt">%s</div>' % (doc, matches, frag)

def getRelatedDocs(d, cutoff=7):
    df = d.frags.filter(l__gte=cutoff).distinct()
    pk=[]
    for frag in df:
        pk.append(frag.pk)
    # TODO: mongofy
    return Doc.objects.filter(frags__pk__in=pk).distinct().exclude(eurlexid=d.eurlexid)

def getDocFrags(d, cutoff=7):
    # returns the doc, with only the frags which are filtered by the cutoff and disctinct ordered by their location.
    return sorted(
        filter(lambda x: x['l']>cutoff,
               d.pippies),
        key=itemgetter('pos'))

def docView(request,doc=None,cutoff=7):
    if request.method == 'GET':
        if request.GET['cutoff']:
            cutoff = request.GET['cutoff']
    if not doc or not int(cutoff):
        return render_to_response('error.html', {'error': 'Missing document or wrong cutoff!'})
    try:
        d = Doc(doc)
    except:
        return render_to_response('error.html', {'error': 'Wrong document: %s!' % doc})
    soup = BeautifulSoup(d.raw)
    c=soup.find(id='TexteOnly')
    relDocs = getRelatedDocs(d, cutoff)
    #origfrags = d.getstems()
    # TODO: mongofy
    for frag in list(Frag.objects.filter(l__gte=cutoff).filter(doc__eurlexid__in=[x for x in relDocs]).distinct().order_by('-l')):
        tokens = []
        for t in eval(frag.frag):
            if t:
                tokens.append(t[0])
            else:
                tokens.append('')
        tokenr = "\s*".join( map(lambda x: re.escape(x), tokens))
        regex=re.compile(tokenr, re.I | re.M)
        #regex = re.compile('*'.join(tokens), re.I|re.M)
        rr = c.find(text=regex)
        while rr:
            print tokenr
            print rr
            rr = rr.findNext(text=regex)
    #    relDocs.append(frag.doc_set.exclude(eurlexid=doc))
    return render_to_response('docView.html', {'doc': d, 'content': c, 'related': relDocs})

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

def htmlRefs(d, cutoff=7):
    res=[]
    f=[]
    i=0
    #for frag in list(Frag.objects.filter(l__gte=cutoff).filter(doc__eurlexid=d).distinct().order_by('-l')):
    for frag in getDocFrags(d, cutoff):
        start=frag['pos']
        origfrag=frag['txt']
        res.append([])
        res[i].append(htmlPippi(d,
                             # BUG display all idx, not just the first
                             # in the reference document
                             unicode(start),
                             " ".join(origfrag)))
        for loc in filter(lambda x: x['doc'] != d._id, Pippi('', oid = frag['frag']).docs):
            f=loc['txt']
            f=" ".join(diffFrag(origfrag,f))
            doc=Doc('',oid=loc['doc']).eurlexid
            res[i].append(htmlPippi(doc, unicode(loc['pos']), f))
        i+=1
    return res

def xpippiFormView(request):
     if request.method == 'POST':
         form = XpippiForm(request.POST)
         if form.is_valid():
             return HttpResponseRedirect(settings.ROOT_URL+"/xpippi/%s" % form.cleaned_data['doc'])
     else:
        form = XpippiForm()
     return render_to_response('xpippiForm.html', { 'form': form, })

def xpippi(request, doc):
    d=Doc(doc)
    result=htmlRefs(d)
    return render_to_response('xpippi.html', { 'frags': result, 'doc': d })

def getOverview():
    stats=[]
    stats.append({'title': 'Total documents', 'value': Docs.count()})
    stats.append({'title': 'Total Pippies', 'value': Pippies.count()})
    return stats

def listDocs(request):
    docs=[{'id': doc.eurlexid,
           'title': doc.title or doc.eurlexid,
           'subject': doc.subject or "",
           'tags': tagcloud.logTags(doc.stems,l=25)}
           for doc in [Doc('',d=data) for data in Docs.find()]]
    return render_to_response('corpus.html', { 'docs': docs, 'stats': getOverview(), })

def stats(request):
    return render_to_response('stats.html', { 'stats': getOverview(), })
