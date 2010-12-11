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
from lenx import settings
setup_environ(settings)
from BeautifulSoup import BeautifulSoup, Tag, NavigableString
from lenx.view.models import Pippi, TfIdf, tfidf
from lenx.view.doc import Doc
from lenx.view.db import Pippies, Frags, Docs, DocTexts, DocStems, DocTokens, fs
from lenx.view.forms import UploadForm, ImportForm
from operator import itemgetter
import re, pymongo, cgi
import tidy
import nltk.tokenize # get this from http://www.nltk.org/
from lenx.brain import hunspell # get pyhunspell here: http://code.google.com/p/pyhunspell/
from lenx.brain import lcs
import httplib
import re, htmlentitydefs

""" template to format a pippi (doc, match_pos, text) """
def htmlPippi(doc,matches,frag):
    return u'<span class="doc">in %s</span>: <span class="pos">%s</span><div class="txt">%s</div>' % (doc, matches, frag)

def index(request):
    return render_to_response('index.html')

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

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

def annotatePippi(d,pippi,cutoff=7):
    itemtpl='<li><a href="/doc/%s?cutoff=%d">%s</a><hr /></li>'
    docs=Pippi('',oid=pippi['pippi']).getDocs(d,cutoff=cutoff)
    return '\n'.join([
        '<div class="pippiNote" id="%s">' % pippi['pippi'],
        '<b>also appears in</b>',
        '<ul>',
        '\n'.join([(itemtpl % (doc.docid, cutoff, doc.title)) for doc in docs]).encode('utf8'),
        '</ul>',
        '</div>',
        ])

def docView(request,doc=None,cutoff=20):
    if request.GET.get('cutoff', 0):
        cutoff = int(request.GET['cutoff'])
    if not doc or not cutoff:
        return render_to_response('error.html', {'error': 'Missing document or wrong cutoff!'})
    try:
        d = Doc(docid=doc)
    except:
        form = UploadForm({'docid': doc})
        return render_to_response('upload.html', { 'form': form, })
    tooltips={}
    cont = d.body
    relDocs = Docs.find({'_id': { '$in': list(d.getRelatedDocIds(cutoff=cutoff))} }, ['docid','title'])
    ls = []
    matches = 0
    for l in d.getFrags(cutoff=cutoff):
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
        if not l['pippi'] in tooltips:
            tooltips[l['pippi']]=annotatePippi(d,l,cutoff)
        for r in regex.finditer(cont):
            #print '[!] Match: %s\n\tStartpos: %d\n\tEndpos: %d' % (r.group(), r.start(), r.end())
            span = (('<span class="highlight %s">') % l['pippi'], '</span>')
            start = r.start()+offset
            if btxt:
                start += 1
            end = r.end()+offset
            if etxt:
                end -= 1
            match, n = re.compile(r'((?:\s*<[^>]+>)+)', re.M | re.U).subn(r'%s\1%s' % (span[1], span[0]), cont[start:end])
            cont = cont[:start]+span[0]+match+span[1]+cont[end:]
            offset += (n+1)*(len(span[0])+len(span[1]))
            matches += 1
            #print '_'*60
        #print '-'*120
    cont=anchorArticles(cont)
    #print "[!] Rendering\n\tContent length: %d" % len(cont)
    return render_to_response('docView.html', {'doc': d,
                                               'content': cont,
                                               'related': relDocs,
                                               'cutoff': cutoff,
                                               'len': len(ls),
                                               'tooltips': '\n'.join(tooltips.values()),
                                               'matches': matches})

def diffFrag(frag1,frag2):
    if not frag1 and frag2:
        return frag2
    if not frag2 and frag1:
        return frag1
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

def getOverview():
    stats=[]
    stats.append({'title': 'Total documents', 'value': Docs.count(), 'text': "%s Documents" % Docs.count()})
    stats.append({'title': 'Total Pippies', 'value': Pippies.count(), 'text': "with %s Pippies" % Pippies.count()})
    stats.append({'title': 'Locations', 'value': Frags.count(), 'text': "in %s Locations" % Frags.count()})
    return stats

def listDocs(request):
    docslen=Docs.count()
    docs=[{'id': doc.docid,
           'oid': doc._id,
           'indexed': doc.pippiDocsLen,
           'title': doc.title,
           'frags': doc.getFrags().count(),
           'pippies': len(doc.pippies),
           'docs': len(doc.getRelatedDocIds()),
           'tags': doc.autoTags(25) }
          for doc in (Doc(d=data) for data in Docs.find({ "pippiDocsLen" : {"$gt": docslen/10 }}))]
    return render_to_response('corpus.html', { 'docs': docs, 'stats': getOverview(), })

def createDoc(request):
    form = UploadForm(request.POST)
    if not form.is_valid():
        return render_to_response('upload.html', { 'form': form, })
    doc=form.cleaned_data['doc']
    docid=form.cleaned_data['docid']
    raw=unicode(str(tidy.parseString(doc, **{'output_xhtml' : 1,
                                  'add_xml_decl' : 0,
                                  'indent' : 0,
                                  'tidy_mark' : 0,
                                  'doctype' : "strict",
                                  'wrap' : 0})),'utf8')
    d=Doc(raw=raw.encode('utf8'),docid=docid.encode('utf8'))
    if not 'stems' in d.__dict__ or not d.stems:
        # let's calculate and cache the results
        tfidf.add_input_document(d.termcnt.keys())
        d.save()
    return HttpResponseRedirect('/doc/%s' % (d.docid))

def importDoc(request):
    if request.method == 'POST':
        form = ImportForm(request.POST)
        if form.is_valid():
            url=form.cleaned_data['url']
            docid=form.cleaned_data['docid']
            hostValidator = re.compile('^\W*https?:\/\/(.+\.co-ment.com)(\/text\/[a-zA-Z0-9]+\/).+\/?\W*$', re.I | re.U).search(url)
            if not hostValidator or hostValidator.group(0) != url:
                return render_to_response('error.html', {'error': 'Wrong co-ment URL: %s!' % (url)})
            HOSTNAME = hostValidator.group(1)
            # /text/JplAuXN9be2/comments
            try:
                conn = httplib.HTTPSConnection(HOSTNAME)
                conn.putrequest('GET', hostValidator.group(2)+'comments/')
                conn.endheaders()
                response = conn.getresponse()
                html = response.read()
                soup = BeautifulSoup(html)
            except:
                return render_to_response('error.html', {'error': 'Cannot download URL, please try again!'})
            #print unicode(unescape(''.join(soup.find(attrs={'id' : 'textcontainer'}))))
            # TODO DC.subject parse
            raw = u'<html><head><title>%s</title><meta name="DC.subject" content="%s" /> <meta http-equiv="content-type" content="text/html; charset=utf-8" /> </head><body>%s</body></html>' % (docid, url, unescape(unicode(soup.find(attrs={'id' : 'textcontainer'}))))
            d=Doc(raw=raw.encode('utf8'),docid=docid.encode('utf8'))
            if not 'stems' in d.__dict__ or not d.stems:
                # let's calculate and cache the results
                tfidf.add_input_document(d.termcnt.keys())
                d.save()
            return HttpResponseRedirect('/doc/%s' % (d.title))
    else:
        form = ImportForm()
    return render_to_response('import.html', { 'form': form, })

def job(request):
    d1=request.GET.get('d1','')
    d2=request.GET.get('d2','')
    try:
        D1=Doc(docid=d1)
    except:
        return render_to_response('error.html', {'error': 'wrong document: "%s"!' % d1})
    try:
        D2=Doc(docid=d2)
    except:
        return render_to_response('error.html', {'error': 'specify document: "%s"!' % d2})
    lcs.pippi(D1,D2)
    return HttpResponseRedirect('/doc/%s' % (d1))

def pippi(request,refdoc=None):
    if not refdoc:
        return render_to_response('error.html', {'error': 'specify document: %s!' % refdoc})
    refdoc=Doc(docid=refdoc)
    docs=sorted([(doc['docid'],doc['_id']) for doc in Docs.find({},['_id','docid'])])
    docslen=Docs.count()
    docs=[{'id': doc.docid,
           'oid': doc._id,
           'indexed': doc.pippiDocsLen,
           'title': doc.title,
           'frags': doc.getFrags().count(),
           'pippies': len(doc.pippies),
           'job': not doc._id in refdoc.pippiDocs,
           'type': doc.type,
           'docs': len(doc.getRelatedDocIds()),
           'tags': doc.autoTags(25) }
          for doc in (Doc(oid=oid) for d,oid in docs if not oid == refdoc._id)]
    return render_to_response('pippi.html', { 'docs': docs, 'stats': getOverview(), 'refdoc': refdoc.docid })

def stats(request):
    return render_to_response('stats.html', { 'stats': getOverview(), })

def pager(request,data, orderBy, orderDesc):
    limit = int(cgi.escape(request.GET.get('limit','10')))
    if limit>100: limit=100
    elif limit<10: limit=10
    #Count the total items in the dataset
    totalinquery=data.count()
    upperbound=(totalinquery/limit)*limit
    #Grabs the remainder when you divide the total by the offset
    lowerbound=totalinquery%limit
    offset = int(cgi.escape(request.GET.get('offset','0')))
    pageaction = cgi.escape(request.GET.get('pageaction',""))
    #if the first page is requested...set the offset to zero
    if pageaction=='first':
        offset=0
    #if the last page is requested...set the offset to the total count - the number displayed
    if pageaction=='last':
        offset=upperbound
    #if the next page is requested...add limit to the offset
    if pageaction=='next':
        offset=offset+limit
        if offset>upperbound:
            offset=upperbound
    #if the prior page is requested....take limit away from the offset
    if pageaction=='prior':
        offset=offset-limit
    #if the requested offset is less than the lower bound..go ahead and reset to zero so that
    #ten items will always display on the first page
    if offset < lowerbound:
        offset=0
    #fetch the data according to where the new offset is set.
    res=list(data.limit(limit).skip(offset).sort([(orderBy, pymongo.DESCENDING if orderDesc else pymongo.ASCENDING)]))
    #pass the offset, the total in query, and all the data to the template
    return {'limit': limit,
            'offset':offset,
            'page':(offset/limit)+1,
            'totalpages':(totalinquery/limit)+1,
            'totalitems': len(res),
            'orderby':orderBy,
            'desc':orderDesc,
            'totalinquery':totalinquery,
            'data': res, }

def frags(request):
    filtr={}
    template_vars={}
    docfilter=None
    cutoff=None
    pippifilter=None
    try:
        docfilter =  pymongo.objectid.ObjectId(cgi.escape(request.GET.get('doc','')))
    except:
        pass
    if docfilter:
        filtr['doc']=docfilter
    try:
        pippifilter = pymongo.objectid.ObjectId(cgi.escape(request.GET.get('pippi','')))
    except:
        pass
    if pippifilter:
        filtr['pippi']=pippifilter
    else:
        try:
            cutoff = int(cgi.escape(request.GET.get('cutoff','7')))
        except:
            pass
    if cutoff: filtr['l']={ '$gte': cutoff }
    orderBy = 'l'
    orderDesc = True
    template_vars=pager(request,Frags.find(filtr),orderBy,orderDesc)
    prevDoc=None
    template_vars['frags']=[]
    for frag in template_vars['data']:
        p=Pippi('',oid=frag['pippi'])
        d=Doc(oid=frag['doc'])
        if pippifilter:
            frag['txt']=diffFrag(prevDoc,frag['txt'])
            prevDoc=frag['txt']
        template_vars['frags'].append({'_id': frag['_id'],
                                       'pos': frag['pos'],
                                       'txt': " ".join(frag['txt']),
                                       'len': frag['l'],
                                       'score': sum([d.tfidf.get(t,0) for t in p.pippi]),
                                       'pippi': p,
                                       'doc': d,
                                       })

    template_vars['pippi']=pippifilter
    template_vars['doc']=docfilter
    if docfilter: template_vars['docTitle']=Docs.find_one({'_id': docfilter},['docid'])['docid']
    if pippifilter: template_vars['pippiFilter']=1 #" ".join(Pippies.find_one({'_id': pippifilter},['pippi'])['pippi'])
    return render_to_response('frags.html', template_vars)

def pippies(request):
    filtr={}
    template_vars={}
    docfilter=None
    relfilter=None
    cutoff=None
    try:
        cutoff = int(cgi.escape(request.GET.get('cutoff','7')))
    except:
        pass
    if cutoff: filtr['len']={ '$gte': cutoff }
    try:
        docfilter =  pymongo.objectid.ObjectId(cgi.escape(request.GET.get('doc','')))
    except:
        pass
    if docfilter:
        filtr['docs']=docfilter
    try:
        relfilter =  int(cgi.escape(request.GET.get('relevance','')))
    except:
        pass
    if relfilter: filtr['relevance']=relfilter
    # todo add sortable column headers ala http://djangosnippets.org/snippets/308/
    orderBy = cgi.escape(request.GET.get('orderby','relevance'))
    orderDesc = True if '1'==cgi.escape(request.GET.get('desc','1')) else False
    template_vars=pager(request,Pippies.find(filtr),orderBy,orderDesc)
    template_vars['pippies']=[{'id': pippi['_id'],
                               'pippi': ' '.join([p if p else '*' for p in pippi['pippi'].split(' ')]),
                               'docslen':len(pippi['docs']),
                               'relevance':pippi.get('relevance',0),}
                               for pippi in template_vars['data']]
    template_vars['doc']=docfilter
    if docfilter:
        doc=Docs.find_one({'_id': docfilter},['docid', 'title'])
        template_vars['docTitle']=doc['title'] if 'title' in doc else doc['docid']
    return render_to_response('pippies.html', template_vars)

def search(request):
    q = cgi.escape(request.GET.get('q',''))
    if not q:
        return render_to_response('error.html', {'error': 'Missing search query!'})

    orderBy = cgi.escape(request.GET.get('orderby',''))
    # TODO also order by docslen (need to add that to bulksaver)
    if not orderBy in ['relevance', 'docslen', 'len', ]: orderBy='len'
    # TODO also handle desc/asc via the tableheader on the web ui
    orderDesc = True
    engine = hunspell.HunSpell(settings.DICT+'.dic', settings.DICT+'.aff')
    filtr=[]
    for word in [token for token in nltk.tokenize.wordpunct_tokenize(unicode(q))]:
        # stem each word
        stem=engine.stem(word.encode('utf8'))
        if stem:
            filtr.append(stem[0])
        else:
            filtr.append('')
    template_vars=pager(request,Pippies.find({'pippi': re.compile(' '.join(filtr))}),orderBy,orderDesc)
    template_vars['pippies']=[{'id': pippi['_id'],
                               'pippi':'%s<span class="hilite-query">%s</span>%s' % ' '.join([p if p else '*' for p in pippi['pippi'].split(' ')]).partition(' '.join([p if p else '*' for p in filtr])),
                               'docslen':pippi['docslen'],
                               'len':len(pippi['pippi'].split(' ')),
                               'relevance':pippi.get('relevance',0),}
                               for pippi in template_vars['data']]
    template_vars['getparams']=request.GET.urlencode()
    template_vars['q']=q
    return render_to_response('search.html', template_vars)
