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

import re
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.management import setup_environ
from lenx import settings
setup_environ(settings)
from BeautifulSoup import BeautifulSoup, Tag, NavigableString
from lenx.brain import tagcloud
from lenx.view.models import Doc, Pippi, Docs, Pippies
from lenx.view.forms import XpippiForm, viewForm
from operator import itemgetter

""" template to format a pippi (doc, match_pos, text) """
def htmlPippi(doc,matches,frag):
    return u'<span class="doc">in %s</span>: <span class="pos">%s</span><div class="txt">%s</div>' % (doc, matches, frag)

def index(request):
    return render_to_response('index.html')

def anchorArticles(txt):
    # find all textnodes starting with Article, wrapping this in a named <a> and prepending a hoverable link to this anchor
    aregex=re.compile('^\s*Article\s+[0-9][0-9.,]*', re.I)
    nsoup = BeautifulSoup(unicode(txt))
    node=nsoup.find(text=aregex)
    while node:
        nodeidx=node.parent.contents.index(node)
        match=str(re.match(aregex,node).group())
        # create named <a>
        name=match.replace(' ','_')
        a=Tag(nsoup,'a',[('name',name)])
        a.insert(0,match)
        # create a link that is displayed if the <a> is hovered
        link=Tag(nsoup,'a', [('class',"anchorLink"), ('href','#'+name)])
        link.insert(0,"#")
        # create a container for the a and the link
        hover=Tag(nsoup,'span',[('class','hover')])
        hover.insert(0,a)
        hover.insert(0,link)
        node.parent.insert(nodeidx,hover)
        # cut the newly wrapped from the original node.
        newNode=NavigableString(node[len(match):])
        node.replaceWith(newNode)
        node=newNode.findNext(text=aregex)
    return unicode(str(nsoup),'utf8')

def getPippiRelateddocs(d,pippi):
    return [Doc('',oid=doc['doc'])
            for doc
            in Pippi('',oid=pippi['frag']).docs
            if doc['doc']!=d._id]

def annotatePippi(d,pippi,cutoff=7):
    itemtpl='<li><a href="/doc/%s?cutoff=%d">%s</a><hr /></li>'
    docs=set(getPippiRelateddocs(d,pippi))
    return '\n'.join([
        '<div class="pippiNote">',
        '<b>also appears in</b>',
        '<ul>',
        '\n'.join([(itemtpl % (doc.eurlexid, cutoff, doc.title)) for doc in docs]),
        '</ul>',
        '</div>',
        ])

def docView(request,doc=None,cutoff=20):
    if request.GET.get('cutoff', 0):
        cutoff = int(request.GET['cutoff'])
    if not doc or not cutoff:
        return render_to_response('error.html', {'error': 'Missing document or wrong cutoff!'})
    try:
        d = Doc(doc)
    except:
        return render_to_response('error.html', {'error': 'Wrong document: %s!' % doc})
    cont = unicode(str(BeautifulSoup(d.raw).find(id='TexteOnly')), 'utf8')
    relDocs = d.getRelatedDocs(cutoff=cutoff)
    ls = []
    matches = 0
    for l in sorted(d.pippies,reverse=True,key=itemgetter('l')):
        if( l['l'] < cutoff): break
        # for unique locset - optimalization?!
        if l['txt'] in ls:
            continue
        ls.append(l['txt'])
        t = l['txt']
        # for valid matches
        btxt = ''
        etxt = ''
        if t[0][0].isalnum():
            btxt = '\W'
        if t[-1][-1].isalnum():
            etxt = '\W'
        rtxt = btxt+'\s*(?:<[^>]*>\s*)*'.join([re.escape(x) for x in t])+etxt
        regex=re.compile(rtxt, re.I | re.M | re.U)
        i=0
        offset = 0
        #print "[!] Finding: %s\n\tPos: %s\n\t%s\n" % (' '.join(t), l['pos'], rtxt)
        for r in regex.finditer(cont):
            #print '[!] Match: %s\n\tStartpos: %d\n\tEndpos: %d' % (r.group(), r.start(), r.end())
            span = (('<span class="highlight %s">') % l['frag'], '</span>'+annotatePippi(d,l,cutoff))
            start = r.start()+offset
            if btxt:
                start += 1
            end = r.end()+offset
            if etxt:
                end -= 1
            match, n = re.compile(r'(<[^>highlight]*>)').subn(r'%s\1%s' % (span[1], span[0]), cont[start:end])
            cont = cont[:start]+span[0]+match+span[1]+cont[end:]
            offset += (n+1)*(len(span[0])+len(span[1]))
            matches += 1
            #print '_'*60
        #print '-'*120
    cont=anchorArticles(cont)
    #print "[!] Rendering\n\tContent length: %d" % len(cont)
    return render_to_response('docView.html', {'doc': d, 'content': cont, 'related': relDocs, 'cutoff': cutoff, 'len': len(ls), 'matches': matches})

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
    for frag in d.getDocFrags(cutoff=cutoff):
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
    docslen=Docs.count()
    docs=[{'id': doc.eurlexid,
           'indexed': doc.pippiDocsLen,
           'title': doc.title or doc.eurlexid,
           'subject': doc.subject or "",
           #'tags': tagcloud.logTags(doc.stems,l=25)}
           'tags': tagcloud.logTags('',tags=dict([(t,w*100000) for (t, w) in doc.tfidf.items() if t not in tagcloud.stopwords]),l=25)}
          for doc in (Doc('',d=data) for data in Docs.find({ "pippiDocsLen" : {"$gt": docslen/10 }}))]
    return render_to_response('corpus.html', { 'docs': docs, 'stats': getOverview(), })

def stats(request):
    return render_to_response('stats.html', { 'stats': getOverview(), })
