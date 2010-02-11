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
from BeautifulSoup import BeautifulSoup, Tag
import re, urllib
import stopwords
from lenx.view.models import Doc, Frag, Location

CSSHEADER="""<head>
<script type="text/javascript" charset="utf-8" src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.0/jquery.min.js"></script>
<link href="http://www.ctrlc.hu/~stef/pippi.css" media="screen" rel="stylesheet" title="" type="text/css"  />
<script type="text/javascript">
         $(document).ready(function() {
               $('.right .header').click(function() { $(this).siblings().toggle('slow'); return false; }).siblings().hide();
               });
      </script></head>"""

#CSSHEADER='<head><link href="http://www.ctrlc.hu/~stef/pippi.css" media="screen" rel="stylesheet" title="" type="text/css"  /></head>'

class PippiForm(forms.Form):
    doc1 = forms.CharField(required=True)
    doc2 = forms.CharField(required=True)

class XpippiForm(forms.Form):
    doc = forms.CharField(required=True)

class viewForm(forms.Form):
    doc = forms.CharField(required=True)

""" template to format a pippi (doc, match_pos, text) """
def htmlPippi(doc,matches,frag):
    return u'<span class="doc">in %s</span>: <span class="pos">%s</span><div class="txt">%s</div>' % (doc, matches, frag.decode('utf8'))

def getNote(docs,soup,cutoff):
    note = Tag(soup, "span", [("class","right")])
    ul=Tag(soup,"ul")
    note.insert(0,ul)
    for doc in docs:
        link=Tag(soup,"a", [("href","/view/%s/%s/" % (cutoff,doc))])
        link.insert(0,doc)
        li=Tag(soup,"li")
        li.insert(0,link)
        ul.insert(0,li)
    span=Tag(soup,'span', [("class","header")])
    span.insert(0,'Matches in (%s)' % len(docs))
    note.insert(0,span)
    return note

def pippify(match,refs,soup,cutoff,regex):
    container = []
    segments=re.split(regex, match)
    for text in segments:
        if(re.match(regex,text)):
            container.append(getNote(refs,soup,cutoff))
            markedmatch = Tag(soup, "span", [("class","pippi"),('title','Matches in: %s' % ", ".join(refs))])
            markedmatch.insert(0,text)
            container.append(markedmatch)
        else:
            container.append(text)
    return container

def viewPippiDoc(request,doc=None,cutoff=7):
    form = viewForm(request.GET)
    if not doc and form.is_valid():
        doc=form.cleaned_data['doc'].strip('\t\n')
    if not doc in db.docs.keys() or not int(cutoff):
        return render_to_response('viewPippiDoc.html', { 'form': form, })
    result=""
    d=db.docs[doc]
    soup = BeautifulSoup(d.raw)
    # TexteOnly is the id used on eur-lex pages containing distinct docs
    meat=soup.find(id='TexteOnly')
    for (stem,ref) in sorted(d.refs.items(),cmp=lambda x,y: cmp(len(x[0]),len(y[0])),reverse=True):
        if stem in stopwords.stopfrags or len(stem)<int(cutoff): continue
        for (start,length) in ref['matches']:
            regex=re.compile('('+"\s*".join(
                map(lambda x: re.escape(x),
                    d.gettokens[start:start+length]))+')',
                re.I | re.M)
            try:
                node=meat.find(text=regex)
            except:
                # all matches possibly eaten by greedy pippifying below
                continue
            while node:
                nodeidx=node.parent.contents.index(node)
                pippies=pippify(node,ref['refs'],soup,cutoff,regex)
                for pippi in reversed(pippies):
                    node.parent.insert(nodeidx,pippi)
                n=node
                node=node.findNextSibling(text=regex)
                n.extract()
    #for match in meat.findAll(text=re.compile("^[Aa]rticle [0-9.,]*$")):
    #    # TODO better article naming
    #    parent=match.parent
    #    if not parent.string: continue
    #    a=Tag(soup,'a',[('name',urllib.quote(unicode(match)))])
    #    a.insert(0,parent.string)
    #    parent.insert(0,a)
    # TODO add header with all relevant documents
    # TODO add header tagcloud fo this document
    #result+='<div><ul class="right">'
    #result+="".join([ "<li>%s%s</li>" % (len(x),d.refs[x]['refs'])
    #                    for x in sorted(d.refs.keys(),reverse=True,cmp=lambda x,y: cmp(len(x),len(y)))
    #                    if len(x)>cutoff])
    #result+="</ul></div>"
    result+='<div class="doc">'
    result+=str(meat)
    result+='</div>'
    return HttpResponse('%s\n%s' % (CSSHEADER,unicode(result,'utf8')))

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

def htmlRefs(d):
    res=[]
    D=Doc.objects.select_related().get(eurlexid=d)
    for frag in list(Frag.objects.select_related().filter(docs__doc=D).order_by('-l')):
        if frag.l < 5: break
        columns=(int(100)/(frag.docs.exclude(doc=D).count()+1))
        etalon=frag.docs.filter(doc=D).values()[0]
        start=etalon['idx']
        origfrag=eval(etalon['txt'])
        res.append(u'<table class="frag" width="100%"><tr>')
        res.append(u'<td style="width:%d%%;">' % columns)
        res.append(htmlPippi(d,
                             # BUG display all idx, not just the first
                             # in the reference document
                             unicode(etalon['idx']),
                             " ".join(origfrag)))
        res.append(u'</td>')
        for loc in list(frag.docs.select_related().exclude(doc=D)):
            res.append(u'<td style="width:%d%%;">' % columns)
            f=eval(loc.txt)
            f=" ".join(diffFrag(origfrag,f)).encode("utf8")
            res.append(htmlPippi(loc.doc.eurlexid, unicode(loc.idx), f))
            res.append(u'</td>')
        res.append(u'</tr></table><hr />')
    return '\n'.join(res).encode('utf8')

def xpippi(request):
    form = XpippiForm(request.GET)
    if form.is_valid():
        doc=unicode(form.cleaned_data['doc'].strip('\t\n'))
        import cProfile
        #result=cProfile.runctx('htmlRefs(doc)',globals(),locals(),'/tmp/htmlrefs.prof')
        result=htmlRefs(doc)
        return HttpResponse('%s\n%s' % (CSSHEADER,unicode(str(result),'utf8')))
    else:
        return render_to_response('xpippi.html', { 'form': form, })

