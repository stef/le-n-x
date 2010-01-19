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
        res=[]
        res.append("number of total common phrases: %d" % (len(self.db)))
        res.append("number of multigrams: %d" % (len(filter(lambda x: len(x)>2,self.db.keys()))))
        lfrags=self.longestFrags()
        res.append("max len of frag: %d" % (len(lfrags[0][0])))
        return res

    def frequencyDistribution(self):
        res=[]
        lfrags=self.longestFrags()
        res.append(map(lambda x: len(x[0]), lfrags)))
        res.append(map(lambda x: len(x[1]), lfrags)))
        return res

        res.append("<table><tr>")
        res.append(u"\n".join(map(lambda x:
                                  (len(x[1])>2 and"<td>%s</td>" % len(x[0])) or "", lfrags)))
        res.append("</tr><tr>")
        res.append(u"\n".join(map(lambda x:
                                  (len(x[1])>2 and "<td>%s</td>" % len(x[1])) or "", lfrags)))
        res.append("</tr></table>")

    def getFreqFrags(self):
        frags=self.frequentFrags()
        res=[]
        for (k,docs) in frags:
            if len(k)>1:
                res.append(u'%d\t%s' % (len(docs),k))
        return res

    def getFreqTokens(self):
        frags=self.frequentFrags()
        res=[]
        for (k,docs) in frags:
            if len(k)==1:
                res.append(u'%d\t%s' % (len(docs),k))
        return res

if __name__ == "__main__":
    db=SMatchDb()
    print "loading..."
    db.load(cache=CACHE,storage=FSDB)
    print "done"
    print "---stats"
    print '\n'.join(db.stats()).encode('utf8')
    print "---frequent frags"
    print '\n'.join(db.getFreqFrags()).encode('utf8')
    print "---frequent tokens"
    print '\n'.join(db.printFreqTokens()).encode('utf8')
