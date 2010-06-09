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

from django.core.management import setup_environ
from lenx import settings
setup_environ(settings)
from lenx.brain import cache as Cache
CACHE=Cache.Cache(settings.CACHE_PATH)
from lenx.brain import tagcloud, stopwords

from lenx.brain import hunspell # get pyhunspell here: http://code.google.com/p/pyhunspell/
import nltk.tokenize # get this from http://www.nltk.org/
from BeautifulSoup import BeautifulSoup # apt-get?
from pymongo import Connection
from operator import itemgetter
import itertools, math, pymongo

EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="

conn = Connection()
db=conn.pippi
Docs=db.docs
Pippies=db.pippies
Frags=db.frags
MiscDb=db.miscdb
DocTexts=db.DocTexts
DocStems=db.DocStems
DocTokens=db.DocTokens
Frags.ensure_index([('pippi', pymongo.ASCENDING),
                    ('doc', pymongo.ASCENDING),
                    ('pos', pymongo.ASCENDING)], unique=True)
Frags.ensure_index([('l', pymongo.DESCENDING)])
Docs.ensure_index([('eurlexid', pymongo.ASCENDING)])
Docs.ensure_index([('pippiDocsLen', pymongo.DESCENDING)])
Pippies.ensure_index([('pippi', pymongo.ASCENDING)])

class Pippi():
    computed_attrs = [ 'relevance',]
    def __init__(self, pippi, oid=None, frag=None):
        if oid:
            # get by mongo oid
            frag=Pippies.find_one({"_id": oid})
        elif pippi:
            # get by pippi
            frag=Pippies.find_one({"pippi": pippi})
        if(frag):
            self.__dict__=frag
            self.pippi=tuple(self.pippi)
        else:
            self.__dict__={'pippi': tuple(pippi),
                           'len': len(pippi),
                           'docs': []} # should a be a set of {'pos':p,'txt':txt,'l':l,'doc':_id}
            self.save()

    def save(self):
        self.__dict__['_id']=Pippies.save(self.__dict__)

    def __getattr__(self, name):
        if name in self.computed_attrs and name not in self.__dict__ or not self.__dict__[name]:
            if name == 'relevance':
                self.__dict__[name]=self._getRelevance()
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys() or name in self.computed_attrs:
            self.__dict__[name]=value
        else: raise AttributeError, name

    def _getRelevance(self):
        return float(self.len)/float(len(self.docs) if len(self.docs) else 0)

    def getStr(self):
        return " ".join(eval(self.frag)).encode('utf8')

    def __unicode__(self):
        return unicode(self.pippi)

    def getDocs(self, d, cutoff=7):
        return set([Doc('',oid=oid) for oid in self.docs if oid != d._id])

class Frag():
    computed_attrs = [ 'score',]
    def __init__(self, oid=None, frag=None):
        if oid:
            # get by mongo oid
            frag=Frags.find_one({"_id": oid})
        if(frag):
            self.__dict__=frag
        else:
            self.__dict__={'pos':frag['p'],
                           'txt':frag['txt'],
                           'l':frag['l'],
                           'pippi':frag['pippi']._id,
                           'doc':frag['doc']._id}
            self.save()

    def save(self):
        self.__dict__['_id']=Frags.save(self.__dict__)

    def __getattr__(self, name):
        if name in self.computed_attrs and name not in self.__dict__ or not self.__dict__[name]:
            if name == 'score':
                self.__dict__[name]=self._getScore()
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            raise AttributeError, name

    def __setattr__(self, name, value):
        if name in self.__dict__.keys() or name in self.computed_attrs:
            self.__dict__[name]=value
        else: raise AttributeError, name

    def _getScore(self):
        d=Doc('',oid=self.doc)
        p=Pippi('',oid=self.pippi)
        return sum([d.tfidf.get(t,0) for t in p.pippi])

""" class representing a distinct document, does stemming, some minimal nlp, can be saved and loaded """
class Doc():
    computed_attrs = [ 'raw', 'text', 'tokens', 'stems', 'termcnt', 'title', 'subject', 'tfidf', 'frags']
    fieldMap = {'text': DocTexts, 'stems':  DocStems, 'tokens': DocTokens, }

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
        elif eurlexid:
            # create a new document
            self.__dict__={}
            self.__dict__['eurlexid'] = eurlexid
            self.__dict__['pippies'] = []
            self.__dict__['pippiDocs'] = []
            self.__dict__['pippiDocsLen'] = 0
            self.save()
        else:
            raise KeyError('empty eurlexid')

    # todo add interpretation according to http://www.ellispub.com/ojolplus/help/celex.htm#sectors2
    def __getattr__(self, name):
        # handle and cache calculated properties
        if name in self.computed_attrs and name not in self.__dict__ or not self.__dict__[name]:
            if name == 'raw':
                return self._getraw() # cached on fs
            if name == 'text':
                self.__dict__['text'] = self._gettext() # cached in extfields
            if name == 'tokens':
                self.__dict__['tokens'] = self._gettokens() # cached in extfields
            if name == 'stems':
                self.__dict__['stems'] = self._getstems() # cached in extfields
            if name == 'termcnt':
                self.__dict__['termcnt']=self._getstemcount()
            if name == 'title':
                self.__dict__['title']=self._gettitle()
            if name == 'subject':
                self.__dict__['subject']=self._getsubj()
            if name == 'tfidf':
                self.__dict__['tfidf']=self._gettfidf()
            if name == 'frags':
                return self._getfrags() # not cached at all
        if name in self.__dict__.keys():
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
        tmp=[(i,self.__dict__[i]) for i in self.fieldMap if i in self.__dict__]
        for i in tmp: del self.__dict__[i[0]]
        self.__dict__['_id']=Docs.save(self.__dict__)
        for (i,val) in tmp: self.__dict__[i]=val

    def _getraw(self, cache=CACHE):
        return cache.fetchUrl(EURLEXURL+self.eurlexid)

    def _gettext(self):
        res=self._getExtField('text')
        if res: return res
        soup = BeautifulSoup(self.raw)
        # TexteOnly is the id used on eur-lex pages containing docs
        res = [unicode(x) for x in soup.find(id='TexteOnly').findAll(text=True)]
        self._setExtField('text',res) # cache data
        return res

    def _gettokens(self):
        res=self._getExtField('tokens')
        if res: return res
        res = [token for frag in self.text if frag for token in nltk.tokenize.wordpunct_tokenize(unicode(frag))]
        self._setExtField('tokens',res) # cache data
        return res

    def _getstems(self):
        # start stemming
        stems= self._getExtField('stems') or []
        if stems:
            return tuple(stems)

        engine = hunspell.HunSpell(settings.DICT+'.dic', settings.DICT+'.aff')
        for word in self.tokens:
            # stem each word
            stem=engine.stem(word.encode('utf8'))
            if stem:
                stems.append(stem[0])
            else:
                stems.append('')
        self._setExtField('stems',stems) # cache data
        return tuple(stems)

    def _getstemcount(self):
        termcnt={}
        for stem in self.stems:
            if not stem=='':
                termcnt[stem]=termcnt.get(stem,0)+1
        return termcnt

    def _getHTMLMetaData(self, attr):
        soup = BeautifulSoup(self.raw)
        res=map(lambda x: (x and x.has_key('content') and x['content']) or "", soup.findAll('meta',attrs={'name':attr}))
        return '|'.join(res).encode('utf-8')

    def _gettitle(self):
        return self._getHTMLMetaData('DC.description') or self.eurlexid

    def _getsubj(self):
        return self._getHTMLMetaData('DC.subject')

    def _gettfidf(self):
        return tfidf.get_doc_keywords(self)

    def _getfrags(self):
        return [Frag(frag=f) for f in self.getFrags(cutoff=1)]

    def __hash__(self):
        return hash(self._id)

    def __eq__(self,other):
        return self._id == other._id

    def getRelatedDocIds(self, cutoff=7):
        return set([doc
                    for pippi in Pippies.find({'len': { '$gte': int(cutoff)},
                                               'docs': self._id},
                                              ['docs'])
                    for doc in pippi['docs']])

    def getFrags(self, cutoff=7):
        return Frags.find({'l': { '$gte': int(cutoff)},
                           'doc': self._id,
                           }).sort([('l', pymongo.DESCENDING)])

    def addDoc(self,d):
        if not d._id in self.pippiDocs:
            self.pippiDocs.append(d._id)
            self.pippiDocsLen=len(self.pippiDocs)

    def _getExtField(self, field):
        if field+"id" in self.__dict__:
            res=self.fieldMap[field].find_one({'_id': self.__dict__[field+'id']})
            if res: return res['value']

    def _setExtField(self, field, data):
        self.__dict__[field+'id']=self.fieldMap[field].save({'value': data})

    def autoTags(self,l):
        return tagcloud.logTags('',tags=dict([(t,w*100000) for (t, w) in self.tfidf.items() if t not in stopwords.stopwords]),l=l)

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
        if not term in self.term_num_docs:
            return self.idf_default
        return math.log(float(1 + self.num_docs) /
                        (1 + self.term_num_docs[term]))

    def get_doc_keywords(self, doc):
        """Retrieve terms and corresponding tf-idf for the specified document.
        The returned terms are ordered by decreasing tf-idf.
        """
        tfidf = {}
        doclen=len(doc.stems)
        for word in doc.termcnt:
            # The definition of TF specifies the denominator as the count of terms
            # within the document, but for short documents, I've found heuristically
            # that sometimes len(tokens_set) yields more intuitive results.
            mytf = float(doc.termcnt[word]) / doclen
            myidf = self.get_idf(word)
            tfidf[word] = mytf * myidf
        return tfidf

    def save(self):
        self.__dict__['_id']=MiscDb.save(self.__dict__)

tfidf=TfIdf()

if __name__ == "__main__":
    d=Doc('acta-release')
    print d.stems
    #d.save()
    print 'asdf'
    d1=Doc('acta-release')
    print d1.stems
