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
from lenx.view.db import Pippies, Frags, MiscDb
from lenx.view.doc import Doc
import math

EURLEXURL="http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri="

class Pippi():
    computed_attrs = [ 'relevance',]
    def __init__(self, pippi, oid=None, frag=None):
        if oid:
            # get by mongo oid
            frag=Pippies.find_one({"_id": oid})
        elif pippi:
            # get by pippi
            frag=Pippies.find_one({"pippi": ' '.join(pippi)})
        if(frag):
            self.__dict__=frag
            self.pippi=tuple(self.pippi.split(" "))
        else:
            self.__dict__={'pippi': tuple(pippi),
                           'len': len(pippi),
                           'docs': []} # should a be a set of {'pos':p,'txt':txt,'l':l,'doc':_id}
            self.save()

    def save(self):
        tmp=self.pippi
        self.pippi=" ".join(self.pippi)
        self.__dict__['_id']=Pippies.save(self.__dict__)
        self.pippi=tmp

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
        return unicode(" ".join(self.pippi))

    def getDocs(self, d, cutoff=7):
        return set([Doc(oid=oid) for oid in self.docs if oid != d._id])

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
        d=Doc(oid=self.doc)
        p=Pippi('',oid=self.pippi)
        return sum([d.tfidf.get(t,0) for t in p.pippi])

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
