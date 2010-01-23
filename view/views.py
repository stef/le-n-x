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
from brain.document import MatchDb, Doc

CSSHEADER="""<head>
<script type="text/javascript" charset="utf-8" src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.0/jquery.min.js"></script>
<link href="http://www.ctrlc.hu/~stef/pippi.css" media="screen" rel="stylesheet" title="" type="text/css"  />
<script type="text/javascript">
         $(document).ready(function() {
               /*$(".pippi").tooltip({cssClass: "",});*/
               $('.right').click(function() { $(this).children().toggle('slow'); return false; }).children().hide();
               });
      </script></head>"""

#CSSHEADER='<head><link href="http://www.ctrlc.hu/~stef/pippi.css" media="screen" rel="stylesheet" title="" type="text/css"  /></head>'

db=MatchDb()
db.load()

class pippiForm(forms.Form):
    doc = forms.CharField(required=True)

def viewPippiDoc(request,doc=None,cutoff=7):
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
        start=ref['matches'][0][0]
        end=start+ref['matches'][0][1]
        regex=" ?".join(map(lambda x: (x[0] in ['(',')','\\','?','.','*','['] and '['+x+']') or x,d.tokens[start:end]))
        for match in meat.findAll(text=re.compile(regex)):
            parent=match.parent
            if not parent.string: continue
            (pre,m,post)=parent.string.partition(match)
            parent.string.extract()
            #br=Tag(soup, "br", [("style","clear: both;")] )
            #parent.insert(0,br)
            parent.insert(0,post)
            markedmatch = Tag(soup, "span", [("class","pippi"),('title','Matches in: %s' % ", ".join(ref['refs']))])
            markedmatch.insert(0,m)
            parent.insert(0,markedmatch)
            parent.insert(0,pre)
            note = Tag(soup, "div", [("class","right")])
            ul=Tag(soup,"ul")
            note.insert(0,ul)
            for odoc in ref['refs']:
                link=Tag(soup,"a", [("href","/view/%s/%s/" % (cutoff,odoc))])
                link.insert(0,odoc)
                li=Tag(soup,"li")
                li.insert(0,link)
                ul.insert(0,li)
            note.insert(0,'Matches in (%s)' % len(ref['refs']))
            parent.insert(0,note)
    for match in meat.findAll(text=re.compile("^[Aa]rticle [0-9.,]*$")):
        parent=match.parent
        if not parent.string: continue
        a=Tag(soup,'a',[('name',urllib.quote(unicode(match)))])
        a.insert(0,parent.string)
        parent.insert(0,a)
    #result='<ul class="topfrags">'
    #result+=", ".join(["<li>%s%s</li>" % (len(x),"<ul>"+d.refs[x]['refs'])+"</ul>") for x in sorted(d.refs.keys(),reverse=True,cmp=lambda x,y: cmp(len(x),len(y))) if len(x)>cutoff])
    #result+="</ul>"
    result='<div class="doc">'
    result+=str(meat)
    result+='</div>'
    return HttpResponse('%s\n%s' % (CSSHEADER,unicode(str(result),'utf8')))
