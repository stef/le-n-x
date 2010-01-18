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

import document, cache
CACHE=cache.Cache('../cache');
from fsdb import FilesystemDB
FSDB=FilesystemDB('../db')
from operator import itemgetter

""" misc Doc functions """
class SDoc(document.Doc):
    def gettokenfreq(self):
        return map(
            lambda x: (x[0],len(x[1])),
            sorted(self.wpos.items(),
                   lambda x,y: cmp(len(x),len(y)),
                   itemgetter(1),
                   reverse=True))

    def getstemfreq(self):
        return map(
            lambda x: (x[0],len(x[1])),
            sorted(filter(lambda x: x[0],
                          self.spos.items()),
                   lambda x,y: cmp(len(x),len(y)),
                   itemgetter(1),
                   reverse=True))

""" misc MatchDb functions """
class SMatchDb(document.MatchDb):
    def frequentFrags(self):
        return sorted(self.db.items(),
                      reverse=True,
                      cmp=lambda x,y: cmp(len(x[1]), len(y[1])))

    def stats(self):
        res="number of total common phrases: %d\n" % (len(self.db))
        res+="number of multigrams: %d\n" % (len(filter(lambda x: len(x)>2,self.db.keys())))
        res+="max len of frag: %d\n" % (len(self.longestFrags()[0][0]))
        return res

    def printFreqFrags(self):
        frags=self.frequentFrags()
        res=[]
        for (k,docs) in frags:
            if len(k)>1:
                res.append(u'%d\t%s' % (len(docs),k))
        return '\n'.join(res).encode('utf8')

    def printFreqTokens(self):
        frags=self.frequentFrags()
        res=[]
        for (k,docs) in frags:
            if len(k)==1:
                res.append(u'%d\t%s' % (len(docs),k))
        return '\n'.join(res).encode('utf8')

if __name__ == "__main__":
    db=SMatchDb()
    print "loading..."
    db.load(cache=CACHE,storage=FSDB)
    print "done"
    print "---stats"
    print db.stats()
    print "---frequent frags"
    print db.printFreqFrags()
    print "---frequent tokens"
    print db.printFreqTokens()
