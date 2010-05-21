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

from django.conf import settings
DICTDIR=settings.DICT_PATH
from lenx.brain import cache as Cache
CACHE=Cache.Cache(settings.CACHE_PATH)

from lenx.brain import hunspell # get pyhunspell here: http://code.google.com/p/pyhunspell/
import nltk.tokenize # get this from http://www.nltk.org/
from BeautifulSoup import BeautifulSoup # apt-get?
from pymongo import Connection
from operator import itemgetter
import itertools, math

LANG='en_US'
DICT=DICTDIR+'/'+LANG
EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="

conn = Connection()
db=conn.pippi
Docs=db.docs
Pippies=db.pippies
MiscDb=db.miscdb

class Pippi():
    def __init__(self, pippi, oid=None):
        f=None
        if oid:
            # get by mongo oid
            frag=Pippies.find_one({"_id": oid})
        else:
            # get by pippi
            frag=Pippies.find_one({"pippi": pippi})
        if(frag):
            self.__dict__=frag
        else:
            self.__dict__={}
            self.__dict__['pippi'] = pippi
            self.__dict__['len'] = len(pippi)
            self.__dict__['docs'] = [] # should a be a list of {'pos':p,'txt':txt,'l':l,'doc':_id}
            self.save()

    def save(self):
        self.__dict__['_id']=Pippies.save(self.__dict__)

    def __getattr__(self, name):
        if name in self.__dict__.keys():
            return self.__dict__[name]
        else: raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            self.__dict__[name]=value
        else: raise AttributeError, name

    def getStr(self):
        return " ".join(eval(self.frag)).encode('utf8')

    def __unicode__(self):
        return unicode(self.frag)+":"+unicode(self.l)+"\n"+unicode(self.doc_set.all())

""" class representing a distinct document, does stemming, some minimal nlp, can be saved and loaded """
class Doc():
    computed_attrs = [ 'raw', 'text', 'tokens', 'stems', 'termcnt', 'title', 'subject']

    def __init__(self,eurlexid,oid=None,d=None):
        if oid:
            # get by mongo oid
            d=Docs.find_one({"_id": oid})
        elif eurlexid:
            # get by eurlexid
            d=Docs.find_one({"eurlexid": eurlexid})
        if d:
            # load the values
            self.__dict__=d
            if 'stems' in d:
                # convert stems back to tuples - mongo only does lists
                self.__dict__['stems'] = tuple([tuple(x) for x in d['stems']])
        elif eurlexid:
            # create a new document
            self.__dict__={}
            self.__dict__['eurlexid'] = eurlexid
            self.__dict__['pippies'] = [] # should a be a list of {'pos':p,'txt':txt,'l':l,'frag':frag._id}
            self.__dict__['pippiDocs'] = [] # should a be a list of docs this doc has been compared to
            self.__dict__['pippiDocsLen'] = 0
            self.save()
        else:
            raise KeyError('empty eurlexid')

    def __getattr__(self, name):
        # handle and cache calculated properties
        dirty=False
        if name in self.computed_attrs and name not in self.__dict__.keys():
            dirty=True
            if name == 'raw':
                self.raw=self._getraw()
            if name == 'text':
                self.text=self._gettext()
            if name == 'tokens':
                self.tokens=self._gettokens()
            if name in ['stems','termcnt']:
                (self.stems,self.termcnt)=self._getstems()
            if name == 'title':
                self.title=self._gettitle()
            if name == 'subject':
                self.subject=self._getsubj()
        if name in self.__dict__.keys():
            if dirty: self.save()
            return self.__dict__[name]
        else:
            raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys() or name in self.computed_attrs:
            self.__dict__[name]=value
        else: raise AttributeError, name

    def __unicode__(self):
        return self.eurlexid

    def save(self):
        def uniq(seq, idfun=None):
            seen = {}
            result = []
            if not idfun:
                def idfun(x):
                    return (str(x['txt']),x['pos'])
            for item in seq:
                marker = idfun(item)
                if marker in seen: continue
                seen[marker] = 1
                result+=[item]
            return result
        self.pippies=uniq(self.pippies)
        self.__dict__['_id']=Docs.save(self.__dict__)

    def _getraw(self, cache=CACHE):
        return cache.fetchUrl(EURLEXURL+self.eurlexid)

    def _gettext(self, cache=CACHE):
        soup = BeautifulSoup(self.raw)
        # TexteOnly is the id used on eur-lex pages containing distinct docs
        return [unicode(x) for x in soup.find(id='TexteOnly').findAll(text=True)]

    def _gettokens(self):
        return [token for frag in self.text if frag for token in nltk.tokenize.wordpunct_tokenize(unicode(frag))]

    def _getstems(self):
        # start stemming
        engine = hunspell.HunSpell(DICT+'.dic', DICT+'.aff')
        stems=[]
        termcnt={}
        #spos={}
        #i=0
        for word in self.tokens:
            # stem each word and count the results
            stem=engine.stem(word.encode('utf8'))
            if stem:
                stems.append((stem[0],))
                termcnt[stem[0]]=termcnt.get(stem[0],0)+1
            else:
                stems.append(('',))
        return (tuple(stems),termcnt)

    def _getHTMLMetaData(self, attr):
        soup = BeautifulSoup(self.raw)
        res=map(lambda x: (x and x.has_key('content') and x['content']) or "", soup.findAll('meta',attrs={'name':attr}))
        return '|'.join(res).encode('utf-8')

    def _gettitle(self):
        return self._getHTMLMetaData('DC.description')

    def _getsubj(self):
        return self._getHTMLMetaData('DC.subject')

    def getFrag(self,start,len):
        return " ".join(self.tokens[start:start+len]).encode('utf8')

    def getRelatedDocs(self, cutoff=7):
        return [Doc('',oid=oid)
                for oid in set([doc['doc']
                                for frag in Pippies.find({'docs.doc' : self._id,
                                                          'len' : { '$gte' : int(cutoff) }},
                                                         ['docs.doc'])
                                for doc in frag['docs']
                                if doc['doc'] != self._id])]

    def getDocFrags(self, cutoff=7):
        # returns the doc, with only the frags which are filtered by the cutoff and disctinct ordered by their location.
        return sorted([x for x in self.pippies if x['l']>cutoff],
                      key=itemgetter('pos'))

    def addDoc(self,d):
        if not d._id in self.pippiDocs:
            self.pippiDocs.append(d._id)
            self.pippiDocsLen=len(self.pippiDocs)

class TfIdf:
    def __init__(self, DEFAULT_IDF = 1.5):

        d=MiscDb.find_one({"name": 'tfidf'})
        if d:
            # load the values
            self.__dict__=d
        else:
            # create a new document
            self.__dict__={}
            self.__dict__['name'] = "tfidf"
            self.__dict__['num_docs'] = 0
            self.__dict__['term_num_docs'] = {} # term : num_docs_containing_term
            self.__dict__['stopwords'] = []
            self.__dict__['idf_default'] = DEFAULT_IDF
            self.save()

    def __getattr__(self, name):
        if name in self.__dict__.keys():
            return self.__dict__[name]
        else: raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys() or name == 'name':
            self.__dict__[name]=value
        else: raise AttributeError, name

    def save(self):
        self.__dict__['_id']=Pippies.save(self.__dict__)

    def add_input_document(self, stems):
        """Add terms in the specified document to the idf dictionary.
        requires a unique list of stems (usually doc.termcnt.keys())
        """
        self.num_docs += 1
        for stem in stems:
            self.term_num_docs[stem]=self.term_num_docs.get(stem,0)+1

    def get_idf(self, term):
        """Retrieve the IDF for the specified term.
        This is computed by taking the logarithm of (
        (number of documents in corpus) divided by (number of documents
        containing this term) ).
        """
        if term in self.stopwords:
            return 0
        if not term in self.term_num_docs:
            return self.idf_default
        return math.log(float(1 + self.get_num_docs()) /
                        (1 + self.term_num_docs[term]))

    def get_doc_keywords(self, doc):
        """Retrieve terms and corresponding tf-idf for the specified document.
        The returned terms are ordered by decreasing tf-idf.
        """
        tfidf = {}
        doclen = len(doc.stems)
        for word in doc.termcnt.keys():
            # The definition of TF specifies the denominator as the count of terms
            # within the document, but for short documents, I've found heuristically
            # that sometimes len(tokens_set) yields more intuitive results.
            mytf = float(doc.termcnt[word]) / doclen
            myidf = self.get_idf(word)
            tfidf[word] = mytf * myidf
        return sorted(tfidf.items(), key=itemgetter(1), reverse=True)

    def save(self):
        self.__dict__['_id']=MiscDb.save(self.__dict__)
