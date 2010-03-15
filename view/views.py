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
import re, urllib, itertools
from brain import stopwords
import nltk.tokenize # get this from http://www.nltk.org/
from view.models import Doc, Frag, Location
from view.forms import XpippiForm, viewForm

CSSHEADER="""<head>
<script type="text/javascript" charset="utf-8" src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.0/jquery.min.js"></script>
<link href="http://www.ctrlc.hu/~stef/pippi.css" media="screen" rel="stylesheet" title="" type="text/css"  />
<script type="text/javascript">
         $(document).ready(function() {
               $('.right .header').click(function() { $(this).siblings().toggle('slow'); return false; }).siblings().hide();
               });
      </script></head>"""

#CSSHEADER='<head><link href="http://www.ctrlc.hu/~stef/pippi.css" media="screen" rel="stylesheet" title="" type="text/css"  /></head>'


""" template to format a pippi (doc, match_pos, text) """
def htmlPippi(doc,matches,frag):
    return u'<span class="doc">in %s</span>: <span class="pos">%s</span><div class="txt">%s</div>' % (doc, matches, frag)

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

def getMarkedFrag(soup,refs,text):
    markedmatch = Tag(soup, "span", [("class","pippi"),('title','Matches in: %s' % ", ".join(refs))])
    markedmatch.insert(0,text)
    return markedmatch

def markMatch(node,regex,soup,refs,cutoff,head=True):
    nodeidx=node.parent.contents.index(node)
    # handle full frags in text nodes,
    # this also handles multiple matches in a text node
    segments=re.split(regex, node)
    if len(segments)>1:
        for txt in reversed(segments):
            print "txt", txt
            if(re.match(regex,txt)):
                print "matched regex", regex.pattern
                node.parent.insert(nodeidx,getMarkedFrag(soup,refs,txt))
                if head: node.parent.insert(nodeidx,getNote(refs,soup,cutoff))
            else:
                print "non matching regex", txt
                node.parent.insert(nodeidx,txt)
            last=node.parent.contents[nodeidx]
        # delete split node
        node.extract()
        return last
    else:
        return node

def pippify(match,refs,soup,cutoff,regex,stem,tokens):
    fullregex=re.compile("\s*".join(
        map(lambda x: re.escape(x), tokens)),
        re.I | re.M)
    # handle full frags in text nodes,
    # this also handles multiple matches in a text node
    match=markMatch(match,fullregex,soup,refs,cutoff)
    #print 'full regex',fullregex.pattern
    print 'match parent after smallpippies',match.parent
    # handle frags spanning multiple elements
    #print 'match',match.string
    print 'tail match',re.findall(regex,match.string)
    span=zip(re.findall(regex,match.string),itertools.repeat(match))
    print 'head span',span
    if span:
        nodes=match.findAllNext(text=True)
        print 'next nodes',nodes
        tailr=re.compile(tailRe(tokens))
        for node in nodes:
            if node in ['','\n']:
                continue
            m=re.match(tailr,node)
            words=nltk.tokenize.wordpunct_tokenize(unicode(node))
            # check if current node is contained in the middle of a pippi
            if u"".join(words) in u"".join(tokens):
                print "inner span match",node
                span.append((str(node),node))
            # check if current node is the tail of a pippi
            elif m:
                print 'nodenex', m.string
                print 'tailmatch', m.group()
                span.append((m.group(),node))
                if len(m.group())<len(node.string):
                    break
            else:
                break
        sspan=u' '.join([x[0] for x in span])
        print 'sspan', sspan
        print 'fr',fullregex.pattern
        fm=re.search(fullregex,sspan)
        if fm:
            print 'yay! fragmatch', fm.group()
            head=span[0][1]
            print 'multi head1',head
            head=markMatch(head,regex,soup,refs,cutoff)
            print 'multi head2',head
            for text,node in span[1:-1]:
                nodeidx=node.parent.contents.index(node)
                node.parent.insert(nodeidx,getMarkedFrag(soup,refs,text))
                node.extract()
            tail=span[-1][1]
            match=markMatch(tail,tailr,soup,refs,cutoff,head=False)
            print "after multi",match
    return match

def headRe(tokens):
    if not tokens: return ''
    return r'\s*(?:(?:\s*'+re.escape(tokens[0])+headRe(tokens[1:])+')|$)'

def tailRe(tokens):
    return r'(^\s*'+reduce(lambda x,y: r'(?:'+x+re.escape(y)+r')?\s*',tokens[:-1])+re.escape(tokens[-1])+')'

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
    for (stem,ref) in sorted(d.refs.items(),
                             reverse=True,
                             cmp=lambda x,y: cmp(len(x[0]),len(y[0]))):
        if stem in stopwords.stopfrags or len(stem)<int(cutoff): continue
        print "-------------\n" #,ref['matches']
        print [(x[0],x[1],d.tokens[x[0]:x[0]+x[1]]) for x in ref['matches']]
        for (start,length, tokens) in set([(x[0],x[1],tuple(d.tokens[x[0]:x[0]+x[1]])) for x in ref['matches']]):
            regex=re.compile('('+re.escape(tokens[0])+headRe(tokens[1:])+')', re.I|re.M)
            #try:
            node=meat.find(text=regex)
            #except:
            #    # all matches possibly eaten by greedy pippifying below
            #    continue
            print 'pattern',regex.pattern
            print 'tokens', tokens
            print '1st match', re.findall(regex,node.string)
            while node:
                node=pippify(node,ref['refs'],soup,cutoff,regex,stem,tokens)
                node=node.findNext(text=regex)
                print 'next node',node
    #try:
    aregex=re.compile('^\s*Article\s+[0-9][0-9.,]*', re.I)
    nsoup = BeautifulSoup(str(meat))
    node=nsoup.find(text=aregex)
    while node:
        nodeidx=node.parent.contents.index(node)
        name=str(re.match(aregex,node).group()).replace(' ','_')
        a=Tag(nsoup,'a',[('name',name)])
        node.parent.insert(nodeidx,a)
        node=node.findNext(text=aregex)
    # TODO add header with all relevant documents
    # TODO add header tagcloud fo this document
    #result+='<div><ul class="right">'
    #result+="".join([ "<li>%s%s</li>" % (len(x),d.refs[x]['refs'])
    #                    for x in sorted(d.refs.keys(),reverse=True,cmp=lambda x,y: cmp(len(x),len(y)))
    #                    if len(x)>cutoff])
    #result+="</ul></div>"
    result+='<div class="doc">'
    result+=str(nsoup)
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
        if frag.l < 3: break
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
            f=" ".join(diffFrag(origfrag,f))
            res.append(htmlPippi(loc.doc.eurlexid, unicode(loc.idx), f))
            res.append(u'</td>')
        res.append(u'</tr></table><hr />')
    return '\n'.join(res).encode('utf8')

def xpippiFormView(request):
     if request.method == 'POST':
         form = XpippiForm(request.POST)
         if form.is_valid():
             return HttpResponseRedirect(settings.ROOT_URL+"/xpippi/%s" % form.cleaned_data['doc'])
     else:
        form = XpippiForm()
     return render_to_response('xpippi.html', { 'form': form, })

def xpippi(request, doc):
    try:
        result=htmlRefs(doc)
    except:
        return render_to_response('error.html', {'error': '%s does not exist!' % doc})
    return HttpResponse('%s\n%s' % (CSSHEADER,unicode(str(result),'utf8')))

