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

CSSHEADER="""<head>
<script type="text/javascript" charset="utf-8" src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.0/jquery.min.js"></script>
<link href="http://www.ctrlc.hu/~stef/pippi.css" media="screen" rel="stylesheet" title="" type="text/css"  />
<script type="text/javascript">
         $(document).ready(function() {
               $('.right .header').click(function() { $(this).siblings().toggle('slow'); return false; }).siblings().hide();
               });
      </script></head>"""

#CSSHEADER='<head><link href="http://www.ctrlc.hu/~stef/pippi.css" media="screen" rel="stylesheet" title="" type="text/css"  /></head>'

class pippiForm(forms.Form):
    doc = forms.CharField(required=True)

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

def viewPippiDoc(request,doc=None,cutoff=7,db=None):
    if not db:
        return HttpResponse('Error: db none')
    form = pippiForm(request.GET)
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
                    d.tokens[start:start+length]))+')',
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
