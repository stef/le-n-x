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
from django.shortcuts import render_to_response
from django.core.management import setup_environ
#from lenx import settings
#setup_environ(settings)
from forms import diffForm
from lenx.brain import lcs
from operator import itemgetter
from itertools import izip
from dmp import diff_match_patch as dmp
from pymongo import Connection
conn = Connection()
db=conn.pippi
Docs=db.diffs
threshold=5
PIPPI=0
TEXT=1
DIFF_DELETE = -1
DIFF_INSERT = 1
DIFF_EQUAL = 0

class Frag():
    def __init__(self,t1,t2,p1,p2,type=TEXT):
        self.__dict__={'text1': t1,
                       'text2': t2,
                       'pos1': p1,
                       'pos2': p2,
                       'type': type,
                       }

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            self.__dict__[name]=value
        else: raise AttributeError, name

    def __repr__(self):
        return repr((len(self.text1),self.pos1,self.pos2,self.type))

def html(diffs):
    old=[]
    new=[]
    i = 0
    for (op, data) in diffs:
        text = clean(data)
        if op == DIFF_INSERT:
            old.append("<INS CLASS=\"diff-hidden\">%s</INS>" % (text))
            new.append("<INS>%s</INS>" % (text))
        elif op == DIFF_DELETE:
            old.append('<DEL>%s</DEL>' % (text))
            new.append('<DEL CLASS=\"diff-hidden\">%s</DEL>' % (text))
        elif op == DIFF_EQUAL:
            old.append("<SPAN>%s</SPAN>" % (text))
            new.append("<SPAN>%s</SPAN>" % (text))
        if op != DIFF_DELETE:
            i += len(data)
    return ("".join(old),"".join(new))

def clean(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("\n", "<BR>"))

def getPippies(d1,d2):
    frag=lcs.LCS(d1,d2)
    frags=[]
    # create a list of pippies between the two docs
    for m in lcs.getACS(frag.str,frag.root,{}).values():
        stem=m['frag']
        if len(stem)<threshold: continue
        a=[]
        b=[]
        for p in m['pos']:
            if p<len(d1):
                a.append(p)
            else:
                b.append(p-len(d1))
        if len(a)==len(b)==1:
            frags.append((len(stem),a[0],b[0]))
    return frags

def splitDocs(D1,D2,frags):
    res=[Frag(D1,D2,0,0)]
    # break up the document according to the pippies
    for match in sorted(frags,reverse=True):
        i=0
        for frag in res:
            if frag.pos1>match[1] or frag.pos2>match[2]:
                break
            if frag.type==TEXT:
                if ((frag.pos1<=match[1]<match[1]+match[0]<=frag.pos1+len(frag.text1)) and
                    (frag.pos2<=match[2]<match[2]+match[0]<=frag.pos2+len(frag.text2))):
                    cut11=match[1]-frag.pos1
                    cut12=match[2]-frag.pos2
                    cut21=cut11+match[0]
                    cut22=cut12+match[0]
                    res.insert(i+1,Frag(frag.text1[cut21:],
                                 frag.text2[cut22:],
                                 frag.pos1+cut21,
                                 frag.pos2+cut22))
                    res[i]=Frag(frag.text1[cut11:cut21],
                                frag.text2[cut12:cut22],
                                frag.pos1+cut11,
                                frag.pos2+cut12,type=PIPPI)
                    res.insert(i,Frag(frag.text1[:cut11],
                                 frag.text2[:cut12],
                                 frag.pos1,
                                 frag.pos2))
                    break
            i=i+1
    return res

def markupDiff(frags):
    differ=dmp()
    olds=[]
    news=[]
    # color the fragmented document accordingly
    for frag in frags:
        if(frag.type==PIPPI):
            olds.append(clean(frag.text1))
            news.append(clean(frag.text2))
        else:
            diffarray=differ.diff_main(frag.text1.decode('utf8'),
                                       frag.text2.decode('utf8'))
            differ.diff_cleanupSemantic(diffarray)
            o,n=html(diffarray)
            olds.append(o)
            news.append(n)
    return (olds,news)

def pdiff(D1,D2):
    d1=D1.read()
    d2=D2.read()
    olds,news=markupDiff(splitDocs(d1,d2,getPippies(d1,d2)))
    return (u'<div class="diff-block"><span class="old"><h2>%s</h2>%s</span><span class="new"><h2>%s</h2>%s</span></div>' %
            (D1.name,
             "".join(olds),
             D2.name,
             "".join(news)))

def diff(request):
    error=''
    if request.method == 'POST':
        form = diffForm(request.POST, request.FILES)
        if form.is_valid():
            d1=request.FILES['doc1']
            d2=request.FILES['doc2']
            if d1.size < 1024*1024 and d2.size < 1024*1024:
                res=pdiff(d1,d2)
                return render_to_response('diff.html', { 'doc1': d1, 'doc2': d2, 'res': res})
            else:
                error="Files must be smaller than 1MByte"
    else:
        form = diffForm()
    return render_to_response('diffForm.html', { 'form': form, 'error': error,})
