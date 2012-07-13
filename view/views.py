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
from django.core.context_processors import csrf
from django.template import RequestContext
from lenx import settings
setup_environ(settings)
from lenx.view.models import Pippi, TfIdf, tfidf
from lenx.view.doc import Doc, getStemmer
from lenx.view.db import Pippies, Frags, Docs, DocTexts, DocStems, DocTokens, fs
from lenx.view.forms import UploadForm
from operator import itemgetter
import re, pymongo, cgi, json
from bson.objectid import ObjectId
from bson.code import Code
import tidy
import nltk.tokenize # get this from http://www.nltk.org/
import hunspell # get pyhunspell here: http://code.google.com/p/pyhunspell/
from lenx.brain import lcs, stopmap
from guess_language import guessLanguage

""" template to format a pippi (doc, match_pos, text) """
def htmlPippi(doc,matches,frag):
    return u'<span class="doc">in %s</span>: <span class="pos">%s</span><div class="txt">%s</div>' % (doc, matches, frag)

def index(request):
    return render_to_response('index.html', context_instance=RequestContext(request))


def docView(request,doc=None,cutoff=10):
    if request.GET.get('cutoff', 0):
        cutoff = int(request.GET['cutoff'])
    if not doc or not cutoff:
        return render_to_response('error.html',
                                  {'error': 'Missing document or wrong cutoff!'},
                                  context_instance=RequestContext(request))
    try:
        d = Doc(docid=doc, owner=request.user)
    except:
        form = UploadForm({'docid': doc})
        return render_to_response('upload.html',
                                  { 'form': form, },
                                  context_instance=RequestContext(request))
    cont = d.body
    relDocs = Docs.find({'_id': { '$in': list(d.getRelatedDocIds(cutoff=cutoff))} }, ['docid','title'])
    return render_to_response('docView.html', {'doc': d,
                                               'oid': d._id,
                                               'user': request.user,
                                               'content': cont,
                                               'related': relDocs,
                                               'cutoff': cutoff,
                                               'cutoffs': ','.join(cutoffSL(d,cutoff)),
                                               'len': d.getFrags(cutoff=cutoff).count()},
                              context_instance=RequestContext(request))

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
    stats.append({'title': 'Total documents',
                  'value': Docs.count(),
                  'text': "%s Documents" % Docs.count()})
    stats.append({'title':
                  'Total Pippies',
                  'value': Pippies.count(),
                  'text': "with %s Pippies" % Pippies.count()})
    stats.append({'title': 'Locations',
                  'value': Frags.count(),
                  'text': "in %s Locations" % Frags.count()})
    return stats

def starred(request):
    template_vars=pager(request,
                        Docs.find({'_id' :
                                   { '$in': [ObjectId(x)
                                             for x in request.session.get('starred',())] }},
                                  sort=[('docid',pymongo.ASCENDING)]),
                        'docid',False)
    template_vars['title']='Your starred documents'
    return _listDocs(request, template_vars)

def listDocs(request):
    template_vars=pager(request,Docs.find(sort=[('docid',pymongo.DESCENDING)]),'docid',False)
    template_vars['title']='Complete Corpus of pippi longstrings'
    return _listDocs(request, template_vars)

def _listDocs(request, template_vars, tpl='corpus.html'):
    template_vars['docs']=[{'id': doc.docid,
                            'oid': str(doc._id),
                            'indexed': doc.pippiDocsLen,
                            'title': doc.title,
                            'frags': doc.getFrags().count(),
                            'pippies': len(doc.pippies),
                            'type': doc.type,
                            'docs': len(doc.getRelatedDocIds()),
                            'tags': doc.autoTags(25) }
                           for doc in (Doc(d=d) for d in template_vars['data'])]
    template_vars['stats']=getOverview()
    template_vars['starred']=request.session.get('starred',set())
    return render_to_response(tpl, template_vars, context_instance=RequestContext(request))

def browseDocs(request):
    return render_to_response('browse.html', context_instance=RequestContext(request))

from bson.objectid import ObjectId
def jsonhandler(obj):
    if hasattr(obj, 'isoformat'):
        return unicode(obj.isoformat())
    elif type(obj)==ObjectId:
        return unicode(obj)
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

def jdump(d):
    # simple json dumper default for saver
    return json.dumps(d, indent=0, default=jsonhandler, ensure_ascii=False)

def filterDocs(request):
    q=request.GET.get('q')
    query={}
    if q:
        query={'title': re.compile(q, re.I)}
    mine=request.GET.get('mine')
    if mine=='true':
        query['owner']=unicode(request.user)
    res=pager(request,Docs.find(query, sort=[('_id',pymongo.DESCENDING)]),'docid',False)
    starred=request.session.get('starred',set())
    res['docs']=[{'id': doc.docid,
                  'starred': u'\u2605' if str(doc._id) in starred else u'\u2606',
                  'starclass': 'starred' if str(doc._id) in starred else '',
                  'title': doc.title,
                  'meta': doc.metadata,
                  'oid': str(doc._id),
                  'indexed': doc.pippiDocs,
                  'pippies': len(doc.pippies),
                  'type': doc.type,
                  'tags': doc.autoTags(25),
                  }
                 for doc in (Doc(d=d) for d in res['data'])]
    return HttpResponse(jdump(res),mimetype="application/json")

def setTitle(request, docid):
    try:
        d = Doc(docid=docid)
    except:
        return HttpResponse('')
    if request.user.is_authenticated() and request.user.username==d.owner:
        d.title=request.POST.get('value')
        d.save()
        return HttpResponse(d.title)
    return HttpResponse(d.title)

def createDoc(request):
    form = UploadForm(request.POST)
    if not form.is_valid():
        return render_to_response('upload.html', { 'form': form, }, context_instance=RequestContext(request))
    doc=form.cleaned_data['doc']
    if not "<html>" in doc:
       doc="<html><head></head><body>%s</body></html>" % form.cleaned_data['doc']
    docid=form.cleaned_data['docid']
    raw=unicode(str(tidy.parseString(doc, **{'output_xhtml' : 1,
                                  'add_xml_decl' : 0,
                                  'indent' : 0,
                                  'tidy_mark' : 0,
                                  'doctype' : "strict",
                                  'wrap' : 0})),'utf8')
    d=Doc(raw=raw.encode('utf8'),docid=docid.encode('utf8'), owner=request.user)
    if not 'stems' in d.__dict__ or not d.stems:
        # let's calculate and cache the results
        tfidf.add_input_document(d.termcnt.keys())
        d.save()
    return HttpResponseRedirect('/doc/%s' % (d.docid))

def job(request):
    d1=request.GET.get('d1','')
    d2=request.GET.get('d2','')
    try:
        D1=Doc(docid=d1, owner=request.user)
    except:
        return render_to_response('error.html', {'error': 'wrong document: "%s"!' % d1}, context_instance=RequestContext(request))
    try:
        D2=Doc(docid=d2, owner=request.user)
    except:
        return render_to_response('error.html', {'error': 'specify document: "%s"!' % d2}, context_instance=RequestContext(request))
    lcs.pippi(D1,D2)
    return HttpResponseRedirect('/doc/%s' % (d1))

def jobs(request):
    rdoc=request.GET.get('doc')
    try:
        refdoc=Doc(oid=ObjectId(rdoc))
    except:
        return render_to_response('error.html', {'error': 'wrong document: "%s"!' % rdoc}, context_instance=RequestContext(request))
    failed=[]
    for doc in request.GET.getlist('ids'):
        try:
            od=Doc(oid=ObjectId(doc))
        except:
            failed.append(doc)
            continue
        lcs.pippi(refdoc,od)
    return HttpResponseRedirect('/doc/%s' % (refdoc.docid))

def pippi(request,refdoc=None):
    if not refdoc:
        return render_to_response('error.html', {'error': 'specify document: %s!' % refdoc}, context_instance=RequestContext(request))
    refdoc=Doc(docid=refdoc)
    template_vars=pager(request,Docs.find({},['_id','docid']),'docid',False)
    docs=sorted([(doc['docid'],doc['_id']) for doc in template_vars['data']])
    docslen=Docs.count()
    template_vars['docs']=[{'id': doc.docid,
                            'oid': str(doc._id),
                            'indexed': doc.pippiDocsLen,
                            'title': doc.title,
                            'frags': doc.getFrags().count(),
                            'pippies': len(doc.pippies),
                            'job': not doc._id in refdoc.pippiDocs,
                            'type': doc.type,
                            'docs': len(doc.getRelatedDocIds()),
                            'tags': doc.autoTags(25) }
                           for doc in (Doc(docid=d) for d,oid in docs if not oid == refdoc._id)]
    template_vars['stats']=getOverview()
    template_vars['refdoc']=refdoc.docid
    template_vars['reftitle']=refdoc.title
    template_vars['oid']=str(refdoc._id)
    template_vars['starred']=request.session.get('starred',set())
    return render_to_response('pippi.html', template_vars, context_instance=RequestContext(request))

def stats(request):
    return render_to_response('stats.html', { 'stats': getOverview(), }, context_instance=RequestContext(request))

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
        docfilter = ObjectId(cgi.escape(request.GET.get('doc','')))
    except:
        pass
    if docfilter:
        filtr['doc']=docfilter
    try:
        pippifilter = ObjectId(cgi.escape(request.GET.get('pippi','')))
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
    return render_to_response('frags.html', template_vars, context_instance=RequestContext(request))

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
        docfilter = ObjectId(cgi.escape(request.GET.get('doc','')))
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
    return render_to_response('pippies.html', template_vars, context_instance=RequestContext(request))

def search(request):
    q = cgi.escape(request.GET.get('q',''))
    if not q:
        return render_to_response('error.html', {'error': 'Missing search query!'}, context_instance=RequestContext(request))

    filtr=[]
    lang=guessLanguage(q)
    swords=stopmap.stopmap.get(lang,stopmap.stopmap['en'])
    engine=getStemmer(lang)
    for word in nltk.tokenize.wordpunct_tokenize(unicode(q)):
        # stem each word
        stem=engine.stem(word.encode('utf8'))
        if stem and stem[0] not in swords and len(stem[0])>1:
            filtr.append(stem[0])
        else:
            filtr.append('')
    matches=[x['_id'] for x in DocStems.find({'value': { '$all' : filtr }},['_id'])]
    template_vars=pager(request,
                        Docs.find({"stemsid": { '$in': matches}}),
                        'docid',
                        False)
    template_vars['getparams']=request.GET.urlencode()
    template_vars['q']=q
    template_vars['stats']=getOverview()
    template_vars['starred']=request.session.get('starred',set())
    template_vars['docs']=[{'id': doc.docid,
                            'oid': str(doc._id),
                            'indexed': doc.pippiDocsLen,
                            'title': doc.title,
                            'frags': doc.getFrags().count(),
                            'pippies': len(doc.pippies),
                            'type': doc.type,
                            'docs': len(doc.getRelatedDocIds()),
                            'tags': doc.autoTags(25) }
                           for doc in (Doc(d=d) for d in template_vars['data'])]
    return render_to_response('search.html', template_vars, context_instance=RequestContext(request))

def metaView(request,doc=None):
    if not doc:
        return render_to_response('error.html', {'error': 'Missing document!'}, context_instance=RequestContext(request))
    try:
        d = Doc(docid=doc, owner=request.user)
    except:
        form = UploadForm({'docid': doc})
        return render_to_response('upload.html', { 'form': form, }, context_instance=RequestContext(request))

    relDocs = Docs.find({'_id': { '$in': list(d.getRelatedDocIds(cutoff=5))} }, ['docid','title'])
    return render_to_response('meta.html', {'doc': d,
                                            'oid': d._id,
                                            'related': relDocs,
                                            'metadata': d.metadata,
                                            }, context_instance=RequestContext(request))


def toggle_star(request,id=None):
    if not id:
        return render_to_response('error.html', {'error': 'Missing id!'}, context_instance=RequestContext(request))
    if not 'starred' in request.session or not request.session['starred']:
        request.session['starred']=set([])
    if id in request.session['starred']:
        s=request.session['starred']
        s.remove(id)
        request.session['starred']=s
        return HttpResponse('False')
    else:
        s=request.session['starred']
        s.add(id)
        request.session['starred']=s
        return HttpResponse('True')

def cutoffSL(doc, cutoff):
    m=Code("function(){ emit( this.len , { count : 1 } );}")
    r=Code("function (key, values) { var count = 0; values.forEach(function (v) {count += v.count;}); return {count: count}; }")
    if Pippies.count()>0:
        lens=dict([(x['_id'],int(x['value']['count'])) for x in Pippies.map_reduce(m,r,'cutoff sparkline', query={'docs': doc._id }).find()])
    else:
        lens={}
    if lens.keys():
        return [str(lens[x]) if x in lens else '0' for x in xrange(int(max(lens.keys())+1))][4:cutoff]
    else:
        return []
